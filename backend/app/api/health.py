"""Unprivileged liveness and schema-aware readiness checks.

Liveness is independent of remote providers. Readiness detects missing/obsolete
database migrations before traffic is routed to purchasing endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import AiDailyBudget, User

router = APIRouter(tags=['health'])


@router.get('/health', summary='Application process liveness')
def health_check():
    return {'status': 'ok', 'service': 'procurepilot-api'}


@router.get('/ready', summary='Database and schema readiness')
def readiness_check(db: Session = Depends(get_db)):
    try:
        # Actual SQL against both the core user table and latest migration.
        # SELECT ... LIMIT 1 is cheap and succeeds when tables are empty.
        db.scalar(select(User.id).limit(1))
        db.scalar(select(AiDailyBudget.scope).limit(1))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503, detail='Database or required schema is unavailable'
        ) from exc
    return {'status': 'ready', 'service': 'procurepilot-api'}
