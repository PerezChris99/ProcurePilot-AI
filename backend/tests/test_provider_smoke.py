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


def test_gemini_adk_error_exposes_allowlisted_category_not_secret(monkeypatch):
    from app.agents.runtime import AgentExecutionError
    async def failing_gemini():
        raise AgentExecutionError(
            'private provider text token=never-print-this',
            category='authentication',http_status=401,
        )
    monkeypatch.setattr(provider_smoke,'CHECKS',{'gemini':failing_gemini})
    result=asyncio.run(provider_smoke.run_checks('gemini'))
    assert result['status']=='fail'
    entry=result['checks']['gemini']
    assert entry['error_type']=='AgentExecutionError'
    assert entry['category']=='authentication'
    assert entry['http_status']==401
    assert 'Verify the Gemini AI Studio API key' in entry['hint']
    assert 'never-print-this' not in repr(result)


def test_unknown_gemini_error_category_uses_generic_safe_hint(monkeypatch):
    from app.agents.runtime import AgentExecutionError
    async def failing_gemini():
        raise AgentExecutionError('not for logs',category='unexpected-category')
    monkeypatch.setattr(provider_smoke,'CHECKS',{'gemini':failing_gemini})
    result=asyncio.run(provider_smoke.run_checks('gemini'))
    assert result['checks']['gemini']['category']=='provider_error'
    assert 'not for logs' not in repr(result)


def test_smoke_timeout_reports_origin_and_elapsed_without_raw_exception(monkeypatch):
    from app.agents.runtime import AgentExecutionError

    async def timed_out():
        raise AgentExecutionError(
            'secret internal exception', category='timeout',
            origin='local_deadline', elapsed_seconds=60.01, timeout_seconds=60,
        )

    monkeypatch.setattr(provider_smoke, 'CHECKS', {'gemini':timed_out})
    result=asyncio.run(provider_smoke.run_checks('gemini'))
    entry=result['checks']['gemini']
    assert entry['status']=='fail'
    assert entry['category']=='timeout'
    assert entry['origin']=='local_deadline'
    assert entry['elapsed_seconds']==60.01
    assert entry['timeout_seconds']==60
    assert 'secret internal exception' not in repr(result)


def test_smoke_single_gemini_call_accepts_bounded_override_and_counts_usage(monkeypatch):
    calls=[]

    async def mocked_adk(user_id,prompt,*,timeout_seconds=None):
        calls.append(timeout_seconds)
        assert 'payment_authorized' in prompt
        return {
            'text':'No verified purchases exist.',
            'model':'gemini-3.8-flash',
            'usage': {
                'input_tokens':180,'output_tokens':22,
                'total_tokens':202,'thinking_tokens':14,
                'unknown_metadata':'never-display',
            },
        }
    monkeypatch.setattr(provider_smoke,'run_evidence_analysis',mocked_adk)
    result=asyncio.run(provider_smoke.run_checks(
        'gemini',gemini_timeout_seconds=75,
    ))
    assert result['status']=='pass'
    assert calls==[75]
    entry=result['checks']['gemini']
    assert entry['usage']['thinking_tokens']==14
    assert 'unknown_metadata' not in repr(result)
    assert entry['elapsed_seconds']>=0
