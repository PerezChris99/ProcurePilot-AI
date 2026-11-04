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
