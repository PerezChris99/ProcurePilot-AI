"""Neon/PostgreSQL-backed, fail-closed, cross-instance authentication throttling.

Atomic fixed-window source and identity limits are committed even on denial.
Use one batched INSERT ... ON CONFLICT ... RETURNING for both buckets, rather
than a separate network round trip per bucket on hosted Neon. No email or IP
is stored: all bucket keys are HMAC-anonymized upstream.
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
    if not buckets:
        return

    now = datetime.now(timezone.utc)
    deadline = now + timedelta(seconds=60)
    try:
        with SessionLocal() as session:
            dialect = session.get_bind().dialect.name
            if dialect == 'postgresql':
                insert = pg_insert
            elif dialect == 'sqlite':
                # SQLite is for deterministic tests; never for public traffic.
                insert = sqlite_insert
            else:
                raise RuntimeError('Unsupported authentication limiter dialect')

            # Preserve the existing atomic SQL update and rolling fixed-window
            # behavior. Both HMAC buckets are processed in ONE statement and
            # committed together, not in two separate DB network round trips.
            stmt = insert(AuthRateLimitCounter).values([
                {'bucket_key': key, 'hits': 1, 'expires_at': deadline}
                for key, _limit in buckets
            ])
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
            ).returning(
                AuthRateLimitCounter.bucket_key,
                AuthRateLimitCounter.hits,
                AuthRateLimitCounter.expires_at,
            )
            updates = {
                key: (hits, expires_at)
                for key, hits, expires_at in session.execute(stmt).all()
            }
            # Never authorize a request on an incomplete database result.
            if len(updates) != len(buckets):
                raise RuntimeError('Authentication limiter returned incomplete results')

            # Opportunistic cleanup remains bounded and transactional.
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

    # Make decisions AFTER COMMIT: denied attempts must still be counted.
    # Never remove/loosen the existing 8/min identity and 120/min source caps.
    for key, limit in buckets:
        hits, expires_at = updates[key]
        if int(hits) > limit:
            aware = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
            ttl = max(1, ceil((aware - now).total_seconds()))
            raise HTTPException(
                status_code=429,
                detail='Too many authentication attempts. Try again shortly.',
                headers={'Retry-After': str(ttl)},
            )
