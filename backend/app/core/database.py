"""Conservatively pooled database connections with per-session Postgres time limits."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import get_settings, Settings

class Base(DeclarativeBase):
    pass


def _engine_options(database_url: str, settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    if database_url.startswith('sqlite'):
        # The SQLite path is reserved for local demo/test use, never public staging/prod.
        return {'connect_args': {'check_same_thread': False}}
    if database_url.startswith('postgresql+psycopg://'):
        # Each worker has its own bounded SQLAlchemy pool. A PgBouncer deployment
        # must size pool_size * instances below the server's connection budget.
        return {
            'pool_pre_ping': True,
            'pool_size': settings.db_pool_size,
            'max_overflow': settings.db_max_overflow,
            'pool_timeout': settings.db_pool_timeout_seconds,
            'pool_recycle': 1800,
            'connect_args': {
                'connect_timeout': settings.db_connect_timeout_seconds,
                'options': (
                    f'-c statement_timeout={settings.db_statement_timeout_ms} '
                    f'-c lock_timeout={settings.db_lock_timeout_ms} '
                    f'-c idle_in_transaction_session_timeout={settings.db_idle_transaction_timeout_ms}'
                ),
            },
        }
    return {'pool_pre_ping': True, 'pool_recycle': 1800}


_settings = get_settings()
engine = create_engine(_settings.database_url, **_engine_options(_settings.database_url, _settings))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
