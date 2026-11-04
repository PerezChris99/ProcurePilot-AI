"""Atomic per-day AI call reservations; database enforces limits across API workers."""
from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.ai_budget import AiDailyBudget


class AiQuotaExceeded(Exception):
    def __init__(self, scope: str):
        self.scope = scope
        super().__init__('Daily AI call allowance exhausted')


def reserve_ai_call(db: Session, user_id: str, *, today=None, settings=None) -> None:
    """Charge one attempt before the external LLM call, including uncertain failures.

    Each conditional UPDATE is atomic. Both global and user reservations are in
    one transaction; hitting either limit rolls back the entire reservation.
    """
    settings = settings or get_settings()
    day = today or datetime.now(timezone.utc).date()
    dialect = db.get_bind().dialect.name
    insert = pg_insert if dialect == 'postgresql' else sqlite_insert if dialect == 'sqlite' else None
    if insert is None:
        raise RuntimeError('AI quota requires PostgreSQL or SQLite')
    scopes = (
        ('global', settings.ai_daily_global_runs),
        ('user:' + user_id, settings.ai_daily_user_runs),
    )
    try:
        for scope, limit in scopes:
            db.execute(
                insert(AiDailyBudget).values(scope=scope, day=day, calls=0)
                .on_conflict_do_nothing(index_elements=['scope', 'day'])
            )
            updated = db.execute(
                update(AiDailyBudget).where(
                    AiDailyBudget.scope == scope,
                    AiDailyBudget.day == day,
                    AiDailyBudget.calls < limit,
                ).values(calls=AiDailyBudget.calls + 1)
            )
            if updated.rowcount != 1:
                raise AiQuotaExceeded('global' if scope == 'global' else 'user')
        db.commit()
    except Exception:
        db.rollback()
        raise
