"""Shared, atomically incremented authentication-rate-limit counters."""
from datetime import datetime
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AuthRateLimitCounter(Base):
    __tablename__ = 'auth_rate_limit_counters'
    bucket_key: Mapped[str] = mapped_column(String(160), primary_key=True)
    hits: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
