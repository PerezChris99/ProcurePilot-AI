from datetime import datetime,timedelta,timezone

import pytest
from jose import jwt

from app.core.config import get_settings, Settings
from app.security.tokens import TOKEN_AUDIENCE,TOKEN_ISSUER


def _auth(client,token):
    return client.get('/api/v1/auth/me',headers={'Authorization':'Bearer '+token})


def test_issued_token_contains_audience_issuer_not_before_and_unique_jti(client):
    response=client.post('/api/v1/auth/register',json={
        'email':'token-claims@example.com','full_name':'Test User',
        'password':'correct-horse-battery-staple',
    })
    assert response.status_code==201
    token=response.json()['access_token']
    claims=jwt.decode(token,get_settings().jwt_secret_key,
                      algorithms=['HS256'],audience=TOKEN_AUDIENCE,issuer=TOKEN_ISSUER)
    assert claims['sub']==response.json()['user']['id']
    assert claims['jti']
    assert claims['iat']<=claims['exp']
    assert claims['nbf']<=claims['exp']
    assert _auth(client,token).status_code==200


@pytest.mark.parametrize('overrides',[
    {'iss':'another-app'},
    {'aud':'another-service'},
    {'sub':'not-a-uuid'},
])
def test_foreign_or_malformed_signed_tokens_cannot_enter_workspace(client,overrides):
    now=datetime.now(timezone.utc)
    payload={'sub':'d6f4374b-61e4-42cc-9e91-f34db8a72e68',
             'iss':TOKEN_ISSUER,'aud':TOKEN_AUDIENCE,
             'iat':now,'nbf':now,'exp':now+timedelta(minutes=10)}
    payload.update(overrides)
    token=jwt.encode(payload,get_settings().jwt_secret_key,algorithm='HS256')
    assert _auth(client,token).status_code==401


def test_oversized_access_tokens_fail_without_excessive_parsing(client):
    assert _auth(client,'x'*5000).status_code==401


def test_access_token_lifetime_has_a_validated_maximum():
    with pytest.raises(ValueError):
        Settings(_env_file=None,access_token_expire_minutes=525600)
