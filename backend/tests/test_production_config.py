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
        Settings(_env_file=None,app_env='production',jwt_secret_key=weak)


def test_production_accepts_strong_non_template_jwt_secret():
    value='JxQ7fPcKzU4#n8BvA2!qW9sD6@hL3rTyN5'
    settings=Settings(_env_file=None,app_env='production',jwt_secret_key=value)
    assert settings.app_env=='production'
