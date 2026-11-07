from pydantic import ValidationError
import pytest
from app.core.config import Settings
from app.core.database import _engine_options, _is_neon_pooler, _apply_pooled_transaction_limits, _attach_pooled_transaction_limits

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


def test_neon_pooler_does_not_send_unsupported_pg_startup_options():
    settings=Settings(_env_file=None,app_env='test')
    pooled='postgresql+psycopg://procurepilot_owner:hidden@ep-blue-band-bcjqtqrc-pooler.c-16.us-east-1.aws.neon.tech/procurepilot?sslmode=require'
    assert _is_neon_pooler(pooled)
    options=_engine_options(pooled,settings)
    assert options['connect_args']['connect_timeout']==5
    assert 'options' not in options['connect_args']
    assert options['connect_args']['prepare_threshold'] is None
    assert options['pool_pre_ping'] is True


def test_direct_neon_connections_preserve_startup_limits():
    settings=Settings(_env_file=None,app_env='test')
    direct='postgresql+psycopg://procurepilot_owner:hidden@ep-blue-band-bcjqtqrc.c-16.us-east-1.aws.neon.tech/procurepilot?sslmode=require'
    assert not _is_neon_pooler(direct)
    assert 'statement_timeout=15000' in _engine_options(direct,settings)['connect_args']['options']


def test_neon_pooler_detection_never_matches_database_name_or_username():
    assert not _is_neon_pooler('sqlite:///./pooler.neon.tech.db')
    assert not _is_neon_pooler('postgresql+psycopg://pooler:secret@db.example.com/procurepilot')
    assert not _is_neon_pooler('postgresql+psycopg://pooler:secret@ep-blue-band-bcjqtqrc.c-16.us-east-1.aws.neon.tech/pooler')


def test_transaction_local_neon_limits_are_parameterized_and_no_sql_injection():
    settings=Settings(_env_file=None,app_env='test',
        db_statement_timeout_ms=9000,db_lock_timeout_ms=2500,
        db_idle_transaction_timeout_ms=10000)
    class CapturingConnection:
        query=None
        arguments=None
        def exec_driver_sql(self, query, arguments):
            self.query=query
            self.arguments=arguments
    conn=CapturingConnection()
    _apply_pooled_transaction_limits(conn,settings)
    assert conn.query.count('set_config(')==3
    assert conn.query.count('%s')==3
    assert '9000' not in conn.query
    assert conn.arguments==('9000','2500','10000')
    assert 'true' in conn.query


def test_pooler_begin_hook_is_registered_and_runs_once_per_transaction(monkeypatch):
    from sqlalchemy import create_engine, text
    import app.core.database as database_module
    settings=Settings(_env_file=None,app_env='test')
    seen=[]
    monkeypatch.setattr(database_module,'_apply_pooled_transaction_limits',
        lambda connection, config: seen.append((connection,config)))
    engine=create_engine('sqlite://')
    _attach_pooled_transaction_limits(engine,settings)
    try:
        with engine.connect() as connection:
            with connection.begin():
                assert connection.execute(text('SELECT 1')).scalar()==1
        assert len(seen)==1
        assert seen[0][1] is settings
    finally:
        engine.dispose()
