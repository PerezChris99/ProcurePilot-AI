from pydantic import ValidationError
import pytest
from app.core.config import Settings
from app.core.database import _engine_options

def test_postgresql_pool_and_timeout_defaults_are_bounded():
    settings=Settings(_env_file=None,app_env='test')
    options=_engine_options('postgresql+psycopg://app:secret@db.example.com/procurepilot',settings)
    assert options['pool_pre_ping'] is True
    assert options['pool_size']==5
    assert options['max_overflow']==5
    assert options['pool_timeout']==10
    assert options['connect_args']['connect_timeout']==5
    text=options['connect_args']['options']
    assert 'statement_timeout=15000' in text
    assert 'lock_timeout=3000' in text
    assert 'idle_in_transaction_session_timeout=15000' in text

def test_pool_limits_are_configurable_with_hard_boundaries():
    settings=Settings(_env_file=None,app_env='test',db_pool_size=3,db_max_overflow=2,db_statement_timeout_ms=9000,db_lock_timeout_ms=1500)
    opt=_engine_options('postgresql+psycopg://app:secret@db.example.com/test',settings)
    assert opt['pool_size']==3
    assert opt['max_overflow']==2
    assert 'statement_timeout=9000' in opt['connect_args']['options']
    with pytest.raises(ValidationError):
        Settings(_env_file=None,app_env='test',db_pool_size=500)
    with pytest.raises(ValidationError,match='DB_LOCK_TIMEOUT_MS'):
        Settings(_env_file=None,app_env='test',db_lock_timeout_ms=15000)

def test_sqlite_demo_does_not_receive_postgresql_pool_or_session_options():
    settings=Settings(_env_file=None,app_env='test')
    assert _engine_options('sqlite:///./procurepilot.db',settings)=={'connect_args':{'check_same_thread':False}}
