import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import AuthRateLimitCounter
from app.security import postgres_throttle, rate_limits


@pytest.fixture
def shared_limiter_db(monkeypatch):
    engine = create_engine(
        'sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        postgres_throttle, 'SessionLocal',
        sessionmaker(bind=engine, autoflush=False, autocommit=False),
    )
    monkeypatch.setattr(postgres_throttle.secrets, 'randbelow', lambda n: 1)
    yield engine
    engine.dispose()


def test_neon_fallback_enforces_identity_limit_and_hides_email(monkeypatch, shared_limiter_db):
    monkeypatch.setattr(rate_limits, 'get_settings', lambda: SimpleNamespace(
        app_env='production', rate_limit_redis_url=None,
        database_url='postgresql+psycopg://user:secret@neon.example/procurepilot',
        jwt_secret_key='long-and-random-unit-test-secret-123456789',
    ))
    class Request:
        client = SimpleNamespace(host='192.0.2.90')
        async def json(self):
            return {'email': 'PERSON@EXAMPLE.COM'}

    for attempt in range(8):
        asyncio.run(rate_limits._guard(Request(), 'login'))
    with pytest.raises(HTTPException) as denied:
        asyncio.run(rate_limits._guard(Request(), 'login'))
    assert denied.value.status_code == 429
    assert int(denied.value.headers['Retry-After']) >= 1

    with postgres_throttle.SessionLocal() as session:
        records = session.scalars(select(AuthRateLimitCounter)).all()
        assert len(records) == 2  # shared IP and canonicalized identity
        assert all('person@example.com' not in item.bucket_key for item in records)
        assert sorted(item.hits for item in records) == [9, 9]


def test_expired_window_resets_atomically(shared_limiter_db):
    buckets = [('hashed-identity', 2)]
    postgres_throttle.enforce_postgres_throttle(buckets)
    postgres_throttle.enforce_postgres_throttle(buckets)
    with postgres_throttle.SessionLocal() as session:
        row = session.get(AuthRateLimitCounter, 'hashed-identity')
        row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=5)
        session.commit()
    postgres_throttle.enforce_postgres_throttle(buckets)
    with postgres_throttle.SessionLocal() as session:
        assert session.get(AuthRateLimitCounter, 'hashed-identity').hits == 1


def test_denied_requests_remain_counted(shared_limiter_db):
    buckets = [('hashed-identity', 1)]
    postgres_throttle.enforce_postgres_throttle(buckets)
    for expected in (2, 3):
        with pytest.raises(HTTPException) as exc:
            postgres_throttle.enforce_postgres_throttle(buckets)
        assert exc.value.status_code == 429
        with postgres_throttle.SessionLocal() as session:
            assert session.get(AuthRateLimitCounter, 'hashed-identity').hits == expected


def test_missing_migration_fails_closed(monkeypatch):
    engine = create_engine('sqlite://', poolclass=StaticPool,
                           connect_args={'check_same_thread': False})
    monkeypatch.setattr(
        postgres_throttle, 'SessionLocal', sessionmaker(bind=engine)
    )
    monkeypatch.setattr(postgres_throttle.secrets, 'randbelow', lambda n: 1)
    with pytest.raises(HTTPException) as exc:
        postgres_throttle.enforce_postgres_throttle([('hashed-source', 120)])
    assert exc.value.status_code == 503
    engine.dispose()
