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


@pytest.mark.parametrize(('private_error', 'expected'), [
    ('pydantic_core.ValidationError: 1 validation error for Settings', 'alembic_settings_invalid'),
    ("ModuleNotFoundError: No module named 'alembic'", 'alembic_runtime_dependency_missing'),
    ('psycopg.errors.InsufficientPrivilege: permission denied for table users', 'alembic_database_permission_denied'),
    ('sqlalchemy.exc.OperationalError: connection timed out', 'alembic_database_connect_failed'),
    ('psycopg.errors.DuplicateTable: relation already exists', 'alembic_schema_conflict'),
    ("Can't locate revision identified by abc", 'alembic_revision_conflict'),
    ('sqlalchemy.exc.ProgrammingError: invalidforeignkey', 'alembic_schema_sql_failed'),
    ('unrecognized error password=secret', 'alembic_upgrade_failed'),
])
def test_alembic_error_classifier_returns_only_safe_category(private_error, expected):
    result = gate.classify_alembic_failure(private_error, '')
    assert result == expected
    assert 'secret' not in result


def test_config_preflight_catches_runtime_settings_errors_without_passwords(monkeypatch):
    from app.core import config
    class BrokenSettings:
        def __init__(self):
            raise ValueError('password=private-secret')
    monkeypatch.setattr(config, 'Settings', BrokenSettings)
    with pytest.raises(gate.ReleaseGateError, match='invalid_settings_other') as caught:
        gate.validate_fastapi_settings()
    assert 'private-secret' not in str(caught.value)


def test_model_level_pydantic_validation_with_empty_location_is_classified(monkeypatch):
    from pydantic import BaseModel, model_validator
    from app.core import config

    class BrokenSettings(BaseModel):
        @model_validator(mode='after')
        def reject(self):
            raise ValueError('Production requires a unique JWT_SECRET_KEY of at least 32 characters')

    monkeypatch.setattr(config, 'Settings', BrokenSettings)
    with pytest.raises(gate.ReleaseGateError, match='invalid_settings_jwt'):
        gate.validate_fastapi_settings()


def test_paypal_diagnostic_is_read_only_and_refuses_wrong_webhook_id(monkeypatch):
    from types import SimpleNamespace
    from app.integrations.paypal import client as paypal_module
    from app.core import config
    from scripts import configure_paypal_webhook as webhook_setup
    monkeypatch.setenv('PROCUREPILOT_PAYPAL_INSPECT','1')
    monkeypatch.setenv('PROCUREPILOT_PAYPAL_INSPECT_ORDER_ID','SANDBOX-EXISTING-123')
    monkeypatch.setattr(config,'get_settings',lambda:SimpleNamespace(
        paypal_webhook_id='CORRECTPAYPALID98765'))
    calls=[]
    class MockPayPal:
        def ensure_configured(self): calls.append('credentials_checked')
        def is_valid_order_id(self, value): return True
        async def get_order(self, value):
            calls.append('get_order')
            return {
                'status':'PAYER_ACTION_REQUIRED',
                'purchase_units':[{'payee':{'merchant_id':'MERCHANT-TEST'}}],
            }
    monkeypatch.setattr(paypal_module,'PayPalClient',MockPayPal)
    async def mock_webhook(*,create,client):
        assert create is False
        calls.append('list_webhook')
        return {'id':'DIFFERENTID000000','action':'existing'}
    monkeypatch.setattr(webhook_setup,'ensure_webhook',mock_webhook)
    with pytest.raises(gate.ReleaseGateError,match='paypal_webhook_id_mismatch'):
        gate.inspect_preview_paypal_merchant('preview')
    assert calls == ['credentials_checked','list_webhook']
    assert 'get_order' not in calls


def test_paypal_diagnostic_classifies_unapproved_historical_order(monkeypatch):
    from types import SimpleNamespace
    from app.integrations.paypal import client as paypal_module
    from app.core import config
    from scripts import configure_paypal_webhook as webhook_setup
    monkeypatch.setenv('PROCUREPILOT_PAYPAL_INSPECT','1')
    monkeypatch.setenv('PROCUREPILOT_PAYPAL_INSPECT_ORDER_ID','SANDBOX-EXISTING-123')
    monkeypatch.setattr(config,'get_settings',lambda:SimpleNamespace(
        paypal_webhook_id='CORRECTPAYPALID98765'))
    calls=[]
    class MockPayPal:
        def ensure_configured(self): calls.append('checked')
        def is_valid_order_id(self,value): return True
        async def get_order(self,value):
            calls.append('get_order')
            return {'status':'CREATED','purchase_units':[{'payee':{'merchant_id':'MERCHANT-TEST'}}]}
    monkeypatch.setattr(paypal_module,'PayPalClient',MockPayPal)
    async def match(*,create,client):
        assert create is False
        return {'id':'CORRECTPAYPALID98765','action':'existing'}
    monkeypatch.setattr(webhook_setup,'ensure_webhook',match)
    with pytest.raises(gate.ReleaseGateError,match='paypal_existing_order_unapproved'):
        gate.inspect_preview_paypal_merchant('preview')
    assert calls==['checked','get_order']


def test_paypal_diagnostic_is_never_executed_in_production(monkeypatch):
    monkeypatch.setenv('PROCUREPILOT_PAYPAL_INSPECT','1')
    monkeypatch.setenv('PROCUREPILOT_PAYPAL_INSPECT_ORDER_ID','SANDBOX-EXISTING-123')
    gate.inspect_preview_paypal_merchant('production')  # no network or side effects


@pytest.mark.parametrize("status,category", [
    (401, "paypal_webhook_management_unauthorized"),
    (403, "paypal_webhook_management_forbidden"),
    (404, "paypal_webhook_management_not_found"),
    (429, "paypal_webhook_management_rate_limited"),
    (503, "paypal_webhook_management_provider_error"),
    (400, "paypal_webhook_management_rejected"),
])
def test_read_only_paypal_webhook_diagnostic_classifies_http_code_without_provider_body(status,category):
    import httpx
    request=httpx.Request("GET","https://api-m.sandbox.paypal.com/v1/notifications/webhooks")
    response=httpx.Response(status,request=request,json={"debug_id":"private-provider-id","message":"private-provider-payload"})
    error=httpx.HTTPStatusError("Private provider content",request=request,response=response)
    assert gate.paypal_webhook_diagnostic_category(error)==category
    try:
        raise RuntimeError("Wrapped PayPal request") from error
    except RuntimeError as wrapper:
        assert gate.paypal_webhook_diagnostic_category(wrapper)==category


def test_read_only_paypal_webhook_diagnostic_categorizes_transport_and_unknown():
    import httpx
    assert gate.paypal_webhook_diagnostic_category(httpx.ConnectError("secret host data"))=="paypal_webhook_management_transport"
    assert gate.paypal_webhook_diagnostic_category(ValueError("unexpected data"))=="paypal_webhook_management_unavailable"
