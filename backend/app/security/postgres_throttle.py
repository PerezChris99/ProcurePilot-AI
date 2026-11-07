"""Neon/PostgreSQL-backed, fail-closed, cross-instance authentication throttling.

Each HMAC-anonymized bucket is incremented atomically in a transaction.
A denied attempt is counted and COMMITTED before returning HTTP 429.
Expired buckets are opportunistically removed; no plain email/IP is persisted.
"""
import secrets
from datetime import datetime, timedelta, timezone
from math import ceil

from fastapi import HTTPException
from sqlalchemy import case, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.models.auth_throttle import AuthRateLimitCounter


def enforce_postgres_throttle(buckets: list[tuple[str, int]]) -> None:
    now = datetime.now(timezone.utc)
    deadline = now + timedelta(seconds=60)
    observations = []
    try:
        with SessionLocal() as session:
            dialect = session.get_bind().dialect.name
            if dialect == 'postgresql':
                insert = pg_insert
            elif dialect == 'sqlite':
                # SQLite is for deterministic unit tests; never for public traffic.
                insert = sqlite_insert
            else:
                raise RuntimeError('Unsupported authentication limiter dialect')
            for key, limit in buckets:
                stmt = insert(AuthRateLimitCounter).values(
                    bucket_key=key, hits=1, expires_at=deadline
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=[AuthRateLimitCounter.bucket_key],
                    set_={
                        'hits': case(
                            (AuthRateLimitCounter.expires_at <= now, 1),
                            else_=AuthRateLimitCounter.hits + 1,
                        ),
                        'expires_at': case(
                            (AuthRateLimitCounter.expires_at <= now, deadline),
                            else_=AuthRateLimitCounter.expires_at,
                        ),
                    },
                ).returning(AuthRateLimitCounter.hits, AuthRateLimitCounter.expires_at)
                hits, expires_at = session.execute(stmt).one()
                observations.append((hits, expires_at, limit))
            # Bounded opportunistic cleanup, using the expiry index. A database
            # outage fails closed rather than bypassing authentication throttling.
            if secrets.randbelow(128) == 0:
                session.execute(
                    delete(AuthRateLimitCounter).where(
                        AuthRateLimitCounter.expires_at < now - timedelta(hours=1)
                    )
                )
            session.commit()
    except (SQLAlchemyError, OSError, TimeoutError, RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail='Authentication protection service is unavailable',
        ) from exc

    # Return 429 after commit, so an attacker cannot undo counted failures.
    for hits, expires_at, limit in observations:
        if int(hits) > limit:
            aware = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
            ttl = max(1, ceil((aware - now).total_seconds()))
            raise HTTPException(
                status_code=429, detail='Too many authentication attempts. Try again shortly.',
                headers={'Retry-After': str(ttl)},
            )
