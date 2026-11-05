"""Read-only live provider smoke runner is deterministic under mocked clients."""
import asyncio

from scripts import provider_smoke


def test_provider_smoke_reports_all_three_checks_without_leaking_secrets(monkeypatch):
    async def good():
        return {'working':True}
    monkeypatch.setattr(provider_smoke,'CHECKS',{'channel3':good,'paypal':good,'gemini':good})
    result=asyncio.run(provider_smoke.run_checks('all'))
    assert result['status']=='pass'
    assert set(result['checks'])=={'channel3','paypal','gemini'}
    assert all(item['status']=='pass' for item in result['checks'].values())


def test_provider_smoke_returns_failure_when_any_provider_raises(monkeypatch):
    async def fail():
        raise ValueError('sensitive-key-do-not-output')
    async def pass_check():
        return {'working':True}
    monkeypatch.setattr(provider_smoke,'CHECKS',{'channel3':pass_check,'paypal':fail,'gemini':pass_check})
    result=asyncio.run(provider_smoke.run_checks('all'))
    assert result['status']=='fail'
    assert result['checks']['paypal']=={'status':'fail','error_type':'ValueError'}
    assert 'sensitive-key-do-not-output' not in repr(result)
    only_channel=asyncio.run(provider_smoke.run_checks('channel3'))
    assert only_channel['status']=='pass'
    assert list(only_channel['checks'])==['channel3']


def test_paypal_smoke_refuses_live_endpoint_before_authentication(monkeypatch):
    class FakeLivePayPal:
        base_url='https://api-m.paypal.com'
        def ensure_configured(self):
            raise AssertionError('Must reject live PayPal before credential checking')
        async def _access_token(self):
            raise AssertionError('Must never request a live PayPal token')
    monkeypatch.setattr(provider_smoke,'PayPalClient',FakeLivePayPal)
    result=asyncio.run(provider_smoke.run_checks('paypal'))
    assert result['status']=='fail'
    assert result['checks']['paypal']['error_type']=='RuntimeError'
