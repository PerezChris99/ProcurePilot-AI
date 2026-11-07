"""Vercel Services entrypoint. Local development continues to use app.main:app."""

from app.main import app

__all__ = ["app"]
