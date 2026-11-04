import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.security import rate_limits


def test_auth_throttle_keys_are_hmac_hashed_not_plain_identifiers():
    key=rate_limits._anonymous_key('safe-secret','login:identity','person@example.com')
    assert key.startswith('procurepilot:auth:login:identity:')
    assert 'person@example.com' not in key
    assert key==rate_limits._anonymous_key('safe-secret','login:identity','person@example.com')
    assert key!=rate_limits._anonymous_key('other-secret','login:identity','person@example.com')


def test_public_auth_throttle_rejects_unconfigured_shared_redis(monkeypatch):
    monkeypatch.setattr(rate_limits,'get_settings',lambda:SimpleNamespace(
        app_env='production',rate_limit_redis_url=None,jwt_secret_key='secure-secret'))
    class FakeRequest:
        client=SimpleNamespace(host='192.0.2.1')
    with pytest.raises(HTTPException) as err:
        asyncio.run(rate_limits._guard(FakeRequest(),'login'))
    assert err.value.status_code==503


def test_auth_throttle_rejects_over_limit_with_retry_after(monkeypatch):
    monkeypatch.setattr(rate_limits,'get_settings',lambda:SimpleNamespace(
        app_env='production',rate_limit_redis_url='rediss://example.com:6380',
        jwt_secret_key='secure-secret'))
    class FakeRedis:
        async def eval(self,*args):
            return (121,35)
    monkeypatch.setattr(rate_limits,'_redis',lambda url: FakeRedis())
    class FakeRequest:
        client=SimpleNamespace(host='192.0.2.1')
        async def json(self):
            return {'email':'test@example.com'}
    with pytest.raises(HTTPException) as err:
        asyncio.run(rate_limits._guard(FakeRequest(),'login'))
    assert err.value.status_code==429
    assert err.value.headers['Retry-After']=='35'


def test_local_auth_works_offline_without_redis(monkeypatch):
    monkeypatch.setattr(rate_limits,'get_settings',lambda:SimpleNamespace(app_env='development'))
    asyncio.run(rate_limits._guard(None,'login'))
