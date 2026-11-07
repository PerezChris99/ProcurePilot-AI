"""No-network release gates: never touch production credentials in unit tests."""
import pytest
from scripts import release_schema_gate as gate


DIRECT = (
    'postgresql+psycopg://procurepilot_owner:testing-only@'
    'ep-blue-band-bcjqtqrc.c-16.us-east-1.aws.neon.tech/'
    'procurepilot?sslmode=require'
)
POOLED = DIRECT.replace('ep-blue-band-bcjqtqrc.c-16', 'ep-blue-band-bcjqtqrc-pooler.c-16')
STAGING = (
    'postgresql://owner:testing-only@'
    'ep-spring-silence-bc8oxuii.c-16.us-east-1.aws.neon.tech/'
    'procurepilot?sslmode=require'
)


def test_prod_host_username_and_database_are_strictly_pinned():
    assert gate.checked_direct_url(DIRECT, 'production') == DIRECT
    assert gate.checked_direct_url(POOLED, 'production') == DIRECT
    for bad in (
        STAGING, DIRECT.replace('procurepilot_owner:', 'owner:'),
        DIRECT.replace('/procurepilot?', '/other?'),
        DIRECT.replace('sslmode=require', 'sslmode=disable'),
        DIRECT.replace('ep-blue-band-bcjqtqrc.', 'fake-blue-band.'),
        'sqlite:///local.db', '',
    ):
        with pytest.raises(gate.ReleaseGateError):
            gate.checked_direct_url(bad, 'production')


def test_staging_accepts_only_its_separate_project():
    assert gate.checked_direct_url(STAGING, 'preview').startswith(
        'postgresql+psycopg://owner:'
    )
    with pytest.raises(gate.ReleaseGateError):
        gate.checked_direct_url(DIRECT, 'preview')


def test_alembic_head_and_tables_are_required():
    assert gate.plan(gate.HEAD, set(gate.REQUIRED)) is False
    with pytest.raises(gate.ReleaseGateError, match='required_tables_missing'):
        gate.plan(gate.HEAD, {'users', 'alembic_version'})


def test_approved_forward_revisions_are_safe_and_unknown_schema_fails():
    assert gate.plan(None, set()) is True
    assert gate.plan('0009_delegated_approver', {'users','alembic_version'}) is True
    with pytest.raises(gate.ReleaseGateError, match='unversioned_existing_tables'):
        gate.plan(None, {'users'})
    with pytest.raises(gate.ReleaseGateError, match='unknown_alembic_revision'):
        gate.plan('other_project_revision', {'alembic_version'})


def test_build_requires_explicit_migration_switch(monkeypatch, capsys):
    monkeypatch.setenv('VERCEL', '1')
    monkeypatch.setenv('VERCEL_ENV', 'production')
    monkeypatch.setenv('DATABASE_URL', DIRECT)
    monkeypatch.delenv('PROCUREPILOT_RUN_REVIEWED_MIGRATIONS', raising=False)
    monkeypatch.setattr(gate, 'status', lambda url: (None, set()))
    monkeypatch.setattr(gate, 'migrate', lambda url: pytest.fail('migration executed without flag'))
    assert gate.main() == gate.FAILURE_CODES['migration_required_but_not_enabled']
    output = capsys.readouterr()
    assert 'migration_required_but_not_enabled' in output.err
    assert 'testing-only' not in output.err


def test_explicit_flag_runs_then_rechecks_schema(monkeypatch):
    monkeypatch.setenv('VERCEL', '1')
    monkeypatch.setenv('VERCEL_ENV', 'production')
    monkeypatch.setenv('DATABASE_URL', DIRECT)
    monkeypatch.setenv('PROCUREPILOT_RUN_REVIEWED_MIGRATIONS', '1')
    revisions = iter([(None, set()), (gate.HEAD, set(gate.REQUIRED))])
    calls = []
    monkeypatch.setattr(gate, 'status', lambda url: next(revisions))
    monkeypatch.setattr(gate, 'migrate', lambda url: calls.append(url))
    assert gate.main() == 0
    assert calls == [DIRECT]


def test_ready_database_does_not_rerun_migrations(monkeypatch):
    monkeypatch.setenv('VERCEL_ENV', 'production')
    monkeypatch.setenv('DATABASE_URL', DIRECT)
    monkeypatch.setenv('PROCUREPILOT_RUN_REVIEWED_MIGRATIONS', '1')
    monkeypatch.setattr(gate, 'status', lambda url: (gate.HEAD, set(gate.REQUIRED)))
    monkeypatch.setattr(gate, 'migrate', lambda url: pytest.fail('no-op migration expected'))
    assert gate.main() == 0


def test_connections_are_not_printed_on_failures(monkeypatch, capsys):
    monkeypatch.setenv('VERCEL_ENV', 'production')
    monkeypatch.setenv('DATABASE_URL', DIRECT)
    def fails(url):
        raise RuntimeError('password=testing-only DSN='+url)
    monkeypatch.setattr(gate, 'status', fails)
    assert gate.main() == gate.FAILURE_CODES['neon_connection_failed']
    err = capsys.readouterr().err
    assert 'testing-only' not in err
    assert 'postgresql' not in err
    assert 'neon_connection_failed' in err
