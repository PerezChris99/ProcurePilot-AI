import asyncio
from types import SimpleNamespace

import pytest

from app.agents import runtime


class FakeEvent:
    usage_metadata = SimpleNamespace(
        prompt_token_count=240, candidates_token_count=75,
        total_token_count=315, cached_content_token_count=0,
    )
    content = SimpleNamespace(parts=[SimpleNamespace(text='Compare product A and B.',thought=False)])
    def is_final_response(self):
        return True


def test_evidence_analyst_uses_one_llm_call_and_records_usage(monkeypatch):
    seen = {}
    class FakeService:
        async def create_session(self, **kwargs):
            return SimpleNamespace(id='session-test')
    class FakeRunner:
        def __init__(self, **kwargs):
            seen['agent'] = kwargs['agent']
        async def run_async(self, **kwargs):
            seen['max_llm_calls'] = kwargs['run_config'].max_llm_calls
            yield FakeEvent()
    monkeypatch.setattr(runtime, 'InMemorySessionService', FakeService)
    monkeypatch.setattr(runtime, 'Runner', FakeRunner)
    monkeypatch.setattr(runtime, 'get_settings', lambda: SimpleNamespace(
        google_api_key='test-key', ai_timeout_seconds=30, ai_model='gemini-flash'
    ))
    result = asyncio.run(runtime.run_evidence_analysis('owner', 'Short trusted evidence packet'))
    assert seen['max_llm_calls'] == 1
    assert seen['agent'] is runtime.analysis_agent
    assert result['text'] == 'Compare product A and B.'
    assert result['usage']['input_tokens'] == 240
    assert result['usage']['total_tokens'] == 315


def test_evidence_analyst_rejects_missing_credentials_before_model_call(monkeypatch):
    monkeypatch.setattr(runtime, 'get_settings', lambda: SimpleNamespace(
        google_api_key=None, ai_timeout_seconds=30, ai_model='gemini-flash'
    ))
    with pytest.raises(runtime.AgentConfigurationError):
        asyncio.run(runtime.run_evidence_analysis('owner','Valid evidence'))


@pytest.mark.parametrize(('error_code','message','expected'), [
    ('UNAUTHENTICATED','ACCESS_TOKEN_TYPE_UNSUPPORTED','authentication'),
    ('PERMISSION_DENIED','Permission denied','permission_denied'),
    ('RESOURCE_EXHAUSTED','Quota exceeded','quota_or_rate_limit'),
    ('NOT_FOUND','Model not found','model_access'),
    ('RuntimeError','Cannot send request: client has been closed','transport'),
    ('DEADLINE_EXCEEDED','Timeout','timeout'),
    ('UNAVAILABLE','Temporary provider failure','provider_unavailable'),
])
def test_adk_error_events_preserve_safe_diagnostic_category(
    monkeypatch,error_code,message,expected
):
    class FakeService:
        async def create_session(self, **kwargs):
            return SimpleNamespace(id='session-test')
    class FakeRunner:
        def __init__(self, **kwargs):
            pass
        async def run_async(self, **kwargs):
            assert kwargs['run_config'].max_llm_calls==1
            yield SimpleNamespace(
                error_code=error_code,error_message=message,
                usage_metadata=None,
            )
    monkeypatch.setattr(runtime,'InMemorySessionService',FakeService)
    monkeypatch.setattr(runtime,'Runner',FakeRunner)
    monkeypatch.setattr(runtime,'get_settings',lambda:SimpleNamespace(
        google_api_key='test-key',ai_timeout_seconds=30,ai_model='gemini-3.8-flash'
    ))
    with pytest.raises(runtime.AgentExecutionError) as caught:
        asyncio.run(runtime.run_evidence_analysis('user','Evidence packet'))
    assert caught.value.category==expected
    assert message not in str(caught.value)


def test_wrapped_google_sdk_http_error_is_classified_without_returning_key(monkeypatch):
    class FakeAPIError(RuntimeError):
        code=401
    class FakeService:
        async def create_session(self,**kwargs):
            return SimpleNamespace(id='session-test')
    class FakeRunner:
        def __init__(self,**kwargs):
            pass
        async def run_async(self,**kwargs):
            raise FakeAPIError('UNAUTHENTICATED; key=do-not-leak')
            yield None
    monkeypatch.setattr(runtime,'InMemorySessionService',FakeService)
    monkeypatch.setattr(runtime,'Runner',FakeRunner)
    monkeypatch.setattr(runtime,'get_settings',lambda:SimpleNamespace(
        google_api_key='test-key',ai_timeout_seconds=30,ai_model='gemini-3.8-flash'
    ))
    with pytest.raises(runtime.AgentExecutionError) as caught:
        asyncio.run(runtime.run_evidence_analysis('user','Evidence packet'))
    assert caught.value.category=='authentication'
    assert caught.value.http_status==401
    assert 'do-not-leak' not in str(caught.value)


def test_nested_runtime_transport_error_is_classified_without_raw_message():
    try:
        raise RuntimeError('Cannot send a request, as the client has been closed.')
    except RuntimeError as cause:
        try:
            raise RuntimeError('ADK wrapper') from cause
        except RuntimeError as wrapped:
            category,status=runtime._exception_details(wrapped)
    assert category=='transport'
    assert status is None


def test_provider_token_usage_includes_thinking_and_caching_without_estimates():
    metric=SimpleNamespace(
        prompt_token_count=300,candidates_token_count=41,
        total_token_count=389,cached_content_token_count=12,
        thoughts_token_count=48,
    )
    event=SimpleNamespace(usage_metadata=metric)
    usage=runtime._usage_from_event(event)
    assert usage=={
        'input_tokens':300,'output_tokens':41,'total_tokens':389,
        'cached_input_tokens':12,'thinking_tokens':48,
    }


def test_adk_incremental_metrics_do_not_clobber_earlier_nonnull_usage(monkeypatch):
    class FakeService:
        async def create_session(self,**kwargs):
            return SimpleNamespace(id='session-1')
    class FakeRunner:
        def __init__(self,**kwargs): pass
        async def run_async(self,**kwargs):
            assert kwargs['run_config'].max_llm_calls==1
            first=SimpleNamespace(
                usage_metadata=SimpleNamespace(
                    prompt_token_count=200,candidates_token_count=30,
                    total_token_count=242,cached_content_token_count=0,
                    thoughts_token_count=12,
                ),
                error_code=None,content=None,
                is_final_response=lambda:False,
            )
            last=SimpleNamespace(
                usage_metadata=SimpleNamespace(
                    prompt_token_count=None,candidates_token_count=None,
                    total_token_count=None,cached_content_token_count=None,
                    thoughts_token_count=None,
                ),
                error_code=None,
                content=SimpleNamespace(parts=[SimpleNamespace(text='Verified offer. ',thought=False)]),
                is_final_response=lambda:True,
            )
            yield first
            yield last
    monkeypatch.setattr(runtime,'InMemorySessionService',FakeService)
    monkeypatch.setattr(runtime,'Runner',FakeRunner)
    monkeypatch.setattr(runtime,'get_settings',lambda:SimpleNamespace(
        google_api_key='test-key',ai_timeout_seconds=30,ai_model='gemini-3.8-flash'
    ))
    result=asyncio.run(runtime.run_evidence_analysis('owner','Saved short evidence'))
    assert result['text']=='Verified offer.'
    assert result['usage']['thinking_tokens']==12
    assert result['usage']['total_tokens']==242


def test_adk_runtime_distinguishes_provider_timeout_from_own_deadline(monkeypatch):
    class Session:
        async def create_session(self, **kwargs):
            return SimpleNamespace(id='timeout-test')
    class RunnerStub:
        def __init__(self, **kwargs):
            pass
        async def run_async(self, **kwargs):
            assert kwargs['run_config'].max_llm_calls == 1
            raise TimeoutError('provider request timed out; private transport details')
            yield None

    monkeypatch.setattr(runtime, 'InMemorySessionService', Session)
    monkeypatch.setattr(runtime, 'Runner', RunnerStub)
    monkeypatch.setattr(runtime, 'get_settings', lambda: SimpleNamespace(
        google_api_key='test-key', ai_timeout_seconds=60, ai_model='gemini-3.8-flash',
    ))
    with pytest.raises(runtime.AgentExecutionError) as raised:
        asyncio.run(runtime.run_evidence_analysis('owner', 'Saved short evidence'))
    assert raised.value.category == 'timeout'
    assert raised.value.origin == 'provider_exception'
    assert raised.value.timeout_seconds is None
    assert raised.value.elapsed_seconds >= 0
    assert 'private transport details' not in str(raised.value)


def test_adk_runtime_reports_local_timeout_and_never_retries(monkeypatch):
    class Session:
        async def create_session(self, **kwargs):
            return SimpleNamespace(id='timeout-test')
    calls=[]
    class SlowRunner:
        def __init__(self, **kwargs):
            pass
        async def run_async(self, **kwargs):
            calls.append(kwargs['run_config'].max_llm_calls)
            await asyncio.sleep(0.1)
            if False:
                yield None

    monkeypatch.setattr(runtime, 'InMemorySessionService', Session)
    monkeypatch.setattr(runtime, 'Runner', SlowRunner)
    monkeypatch.setattr(runtime, 'get_settings', lambda: SimpleNamespace(
        google_api_key='test-key', ai_timeout_seconds=60, ai_model='gemini-3.8-flash',
    ))
    original_timeout=asyncio.timeout
    monkeypatch.setattr(runtime.asyncio, 'timeout',
                        lambda seconds: original_timeout(0.01))
    with pytest.raises(runtime.AgentExecutionError) as raised:
        asyncio.run(runtime.run_evidence_analysis(
            'owner','Saved short evidence',timeout_seconds=75,
        ))
    assert raised.value.category=='timeout'
    assert raised.value.origin=='local_deadline'
    assert raised.value.timeout_seconds==75
    assert calls==[1]


@pytest.mark.parametrize('bad_limit',[0,9,91,300,True,60.5,'60'])
def test_adk_smoke_timeout_override_is_strictly_bounded(monkeypatch,bad_limit):
    monkeypatch.setattr(runtime,'get_settings',lambda:SimpleNamespace(
        google_api_key='test-key',ai_timeout_seconds=60,ai_model='gemini-3.8-flash'
    ))
    with pytest.raises(runtime.AgentConfigurationError):
        asyncio.run(runtime.run_evidence_analysis(
            'owner','Saved short evidence',timeout_seconds=bad_limit,
        ))
