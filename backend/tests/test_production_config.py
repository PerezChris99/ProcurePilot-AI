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


@pytest.mark.parametrize('database', ['sqlite:///./procurepilot.db','postgresql://user:password@db.example.com/procurepilot'])
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
