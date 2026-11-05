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
