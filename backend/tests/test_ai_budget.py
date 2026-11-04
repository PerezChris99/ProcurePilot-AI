from datetime import date
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.agents.budget import AiQuotaExceeded, reserve_ai_call
from app.core.database import Base
from app.models.ai_budget import AiDailyBudget


@pytest.fixture
def session():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db
    engine.dispose()


def test_atomic_daily_per_user_and_global_budget_cannot_be_exceeded(session):
    config = SimpleNamespace(ai_daily_user_runs=2, ai_daily_global_runs=3)
    day = date(2026, 11, 4)
    reserve_ai_call(session, 'person-1', today=day, settings=config)
    reserve_ai_call(session, 'person-1', today=day, settings=config)
    with pytest.raises(AiQuotaExceeded) as raised:
        reserve_ai_call(session, 'person-1', today=day, settings=config)
    assert raised.value.scope == 'user'
    assert session.get(AiDailyBudget, ('global', day)).calls == 2
    reserve_ai_call(session, 'person-2', today=day, settings=config)
    with pytest.raises(AiQuotaExceeded) as raised:
        reserve_ai_call(session, 'person-2', today=day, settings=config)
    assert raised.value.scope == 'global'
    assert session.get(AiDailyBudget, ('global', day)).calls == 3
    assert session.get(AiDailyBudget, ('user:person-2', day)).calls == 1


def test_daily_budget_resets_on_a_new_utc_day(session):
    config = SimpleNamespace(ai_daily_user_runs=1, ai_daily_global_runs=1)
    reserve_ai_call(session, 'person-1', today=date(2026, 11, 4), settings=config)
    reserve_ai_call(session, 'person-1', today=date(2026, 11, 5), settings=config)
    assert len(session.scalars(select(AiDailyBudget).where(AiDailyBudget.scope == 'global')).all()) == 2
