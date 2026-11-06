import pytest
from pydantic import ValidationError
from app.core.config import Settings


@pytest.mark.parametrize('weak',[
    'development-only-change-this-secret',
    'replace-with-a-long-random-secret',
    'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
    'short',
])
def test_production_rejects_public_template_and_low_entropy_jwt_secrets(weak):
    with pytest.raises(ValidationError,match='unique JWT_SECRET_KEY'):
        Settings(_env_file=None,app_env='production',jwt_secret_key=weak,
                 database_url='postgresql+psycopg://user:password@db.example.com/procurepilot',
                 frontend_url='https://procurepilot.example.com')


def test_production_accepts_strong_non_template_jwt_secret():
    value='JxQ7fPcKzU4#n8BvA2!qW9sD6@hL3rTyN5'
    settings=Settings(_env_file=None,app_env='production',jwt_secret_key=value,
                      database_url='postgresql+psycopg://user:password@db.example.com/procurepilot',
                      frontend_url='https://procurepilot.example.com')
    assert settings.app_env=='production'


@pytest.mark.parametrize('database', ['sqlite:///./procurepilot.db'])
def test_production_rejects_unportable_database_defaults(database):
    with pytest.raises(ValidationError, match='Production DATABASE_URL'):
        Settings(_env_file=None,app_env='production',
                 jwt_secret_key='JxQ7fPcKzU4#n8BvA2!qW9sD6@hL3rTyN5',
                 database_url=database,frontend_url='https://procurepilot.example.com')

@pytest.mark.parametrize('origin', [
    'http://localhost:5173', 'http://procurepilot.example.com',
    'https://procurepilot.example.com/sign-in',
    'https://procurepilot.example.com?token=value',
])
def test_production_rejects_insecure_or_non_origin_frontend_urls(origin):
    with pytest.raises(ValidationError, match='Production FRONTEND_URL'):
        Settings(_env_file=None,app_env='production',
                 jwt_secret_key='JxQ7fPcKzU4#n8BvA2!qW9sD6@hL3rTyN5',
                 database_url='postgresql+psycopg://user:password@db.example.com/procurepilot',
                 frontend_url=origin)


def test_production_normalizes_frontend_origin_for_cors_and_paypal_redirect():
    settings = Settings(_env_file=None,app_env='production',
             jwt_secret_key='JxQ7fPcKzU4#n8BvA2!qW9sD6@hL3rTyN5',
             database_url='postgresql+psycopg://user:password@db.example.com/procurepilot',
             frontend_url='https://procurepilot.example.com/')
    assert settings.frontend_url == 'https://procurepilot.example.com'


@pytest.mark.parametrize('unknown',['prod','live','release',''])
def test_unknown_app_env_is_rejected_instead_of_silently_skipping_guards(unknown):
    with pytest.raises(ValidationError, match='APP_ENV must'):
        Settings(_env_file=None,app_env=unknown)


def test_case_insensitive_production_environment_is_canonicalized():
    settings = Settings(_env_file=None,app_env='Production',
             jwt_secret_key='JxQ7fPcKzU4#n8BvA2!qW9sD6@hL3rTyN5',
             database_url='postgresql+psycopg://user:password@db.example.com/procurepilot',
             frontend_url='https://procurepilot.example.com')
    assert settings.app_env == 'production'


def test_public_environment_rejects_example_postgresql_credentials():
    with pytest.raises(ValidationError, match='example PostgreSQL credentials'):
        Settings(_env_file=None,app_env='production',
             jwt_secret_key='JxQ7fPcKzU4#n8BvA2!qW9sD6@hL3rTyN5',
             database_url='postgresql+psycopg://postgres:postgres@localhost:5432/procurepilot',
             frontend_url='https://procurepilot.example.com')


def test_render_managed_postgresql_url_uses_explicit_psycopg_driver():
    settings=Settings(_env_file=None,app_env='production',
        jwt_secret_key='JxQ7fPcKzU4#n8BvA2!qW9sD6@hL3rTyN5',
        database_url='postgresql://user:password@private-db:5432/procurepilot',
        frontend_url='https://procurepilot-web.onrender.com')
    assert settings.database_url==(
        'postgresql+psycopg://user:password@private-db:5432/procurepilot')


def test_render_private_key_value_is_allowed_only_inside_render(monkeypatch):
    params=dict(_env_file=None,app_env='production',
        jwt_secret_key='JxQ7fPcKzU4#n8BvA2!qW9sD6@hL3rTyN5',
        database_url='postgresql+psycopg://user:password@private-db:5432/procurepilot',
        frontend_url='https://procurepilot-web.onrender.com')
    private='redis://red-abcdefghijklmnopqrst:6379'
    with pytest.raises(ValidationError,match='Render-internal'):
        Settings(**params,rate_limit_redis_url=private)
    monkeypatch.setenv('RENDER_SERVICE_ID','srv-local-render-test')
    settings=Settings(**params,rate_limit_redis_url=private)
    assert settings.rate_limit_redis_url==private
    for unsafe in (
        'redis://example.com:6379',
        'redis://red-abcdefghijklmnopqrst.evil.example:6379',
        'redis://red-abcdefghijklmnopqrst:6380',
        'redis://red-abcdefghijklmnopqrst:6379/1',
    ):
        with pytest.raises(ValidationError,match='Render-internal'):
            Settings(**params,rate_limit_redis_url=unsafe)
    tls=Settings(**params,rate_limit_redis_url='rediss://external.example:6380')
    assert tls.rate_limit_redis_url.startswith('rediss://')
