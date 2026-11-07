"""Bounded SQLAlchemy connections for direct PostgreSQL and Neon PgBouncer.

Neon's pooled hostname uses transaction-mode PgBouncer. Passing PostgreSQL
session GUCs through libpq's startup `options=-c ...` can make every pooled
connection fail with "unsupported startup parameter in options". Configure
transaction-local limits only after a transaction starts when pooled.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import get_settings, Settings


class Base(DeclarativeBase):
    pass


def _is_neon_pooler(database_url: str) -> bool:
    """Identify Neon transaction pooler by hostname, never by credentials."""
    if not database_url.startswith('postgresql+psycopg://'):
        return False
    hostname = (make_url(database_url).host or '').lower()
    return (
        hostname.endswith('.neon.tech')
        and hostname.split('.', 1)[0].endswith('-pooler')
    )


def _engine_options(database_url: str, settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    if database_url.startswith('sqlite'):
        return {'connect_args': {'check_same_thread': False}}
    if database_url.startswith('postgresql+psycopg://'):
        connect_args = {'connect_timeout': settings.db_connect_timeout_seconds}
        if _is_neon_pooler(database_url):
            # PgBouncer rejects session GUCs passed as startup options.
            # Also avoid named prepared statements spanning transactions.
            connect_args['prepare_threshold'] = None
        else:
            # Direct PostgreSQL sessions can safely set timeouts at startup.
            connect_args['options'] = (
                f'-c statement_timeout={settings.db_statement_timeout_ms} '
                f'-c lock_timeout={settings.db_lock_timeout_ms} '
                f'-c idle_in_transaction_session_timeout={settings.db_idle_transaction_timeout_ms}'
            )
        return {
            'pool_pre_ping': True,
            'pool_size': settings.db_pool_size,
            'max_overflow': settings.db_max_overflow,
            'pool_timeout': settings.db_pool_timeout_seconds,
            'pool_recycle': 1800,
            'connect_args': connect_args,
        }
    return {'pool_pre_ping': True, 'pool_recycle': 1800}


def _apply_pooled_transaction_limits(connection, settings: Settings) -> None:
    """One bounded roundtrip on BEGIN; SET LOCAL semantics survive PgBouncer.

    Each SQLAlchemy transaction receives these limits without carrying values
    across unrelated backend sessions. Settings values are Pydantic-validated
    integers, and parameters are bound rather than interpolated into SQL.
    """
    connection.exec_driver_sql(
        "SELECT "
        "set_config('statement_timeout', %s, true), "
        "set_config('lock_timeout', %s, true), "
        "set_config('idle_in_transaction_session_timeout', %s, true)",
        (str(settings.db_statement_timeout_ms),
         str(settings.db_lock_timeout_ms),
         str(settings.db_idle_transaction_timeout_ms)),
    )


def _attach_pooled_transaction_limits(engine, settings: Settings) -> None:
    @event.listens_for(engine, 'begin')
    def _on_begin(connection):
        _apply_pooled_transaction_limits(connection, settings)


_settings = get_settings()
engine = create_engine(_settings.database_url,
                       **_engine_options(_settings.database_url, _settings))
if _is_neon_pooler(_settings.database_url):
    _attach_pooled_transaction_limits(engine, _settings)

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
