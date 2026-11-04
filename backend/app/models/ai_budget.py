from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AiDailyBudget(Base):
    """Atomic daily call reservations across workers, keyed by UTC calendar day."""

    __tablename__ = 'ai_daily_budgets'

    scope: Mapped[str] = mapped_column(String(80), primary_key=True)
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
