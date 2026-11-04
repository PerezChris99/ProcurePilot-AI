"""Bounded ADK execution for predictable token use and safe operation."""
import asyncio

from google.adk.agents.run_config import RunConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agents.procurement_agent.agent import analysis_agent, root_agent
from app.core.config import get_settings


class AgentConfigurationError(RuntimeError):
    pass


class AgentExecutionError(RuntimeError):
    pass


def _usage_from_event(event):
    metadata = getattr(event, 'usage_metadata', None)
    if metadata is None:
        return None
    keys = (
        ('input_tokens', 'prompt_token_count'),
        ('output_tokens', 'candidates_token_count'),
        ('total_tokens', 'total_token_count'),
        ('cached_input_tokens', 'cached_content_token_count'),
    )
    return {name: getattr(metadata, attribute, None) for name, attribute in keys}


async def _run(user_id: str, prompt: str, *, agent, max_calls: int):
    settings = get_settings()
    if not settings.google_api_key:
        raise AgentConfigurationError('Gemini API credentials are not configured')
    if not prompt.strip() or len(prompt) > 10_000:
        raise AgentExecutionError('The evidence packet is invalid or exceeds the allowed size')
    session_service = InMemorySessionService()
    try:
        session = await session_service.create_session(
            app_name='procurepilot', user_id=user_id
        )
        runner = Runner(agent=agent, app_name='procurepilot', session_service=session_service)
        message = types.Content(role='user', parts=[types.Part(text=prompt)])
        final_text = None
        usage = None
        async with asyncio.timeout(settings.ai_timeout_seconds):
            async for event in runner.run_async(
                user_id=user_id, session_id=session.id, new_message=message,
                run_config=RunConfig(max_llm_calls=max_calls),
            ):
                metrics = _usage_from_event(event)
                if metrics:
                    usage = metrics
                if event.is_final_response() and event.content and event.content.parts:
                    final_text = ''.join(
                        part.text or '' for part in event.content.parts
                        if getattr(part, 'text', None) and not getattr(part, 'thought', False)
                    )
        if not final_text or not final_text.strip():
            raise AgentExecutionError('The AI provider returned no usable final assessment')
        return {
            'text': final_text.strip()[:3500],
            'model': settings.ai_model or 'gemini-flash-latest',
            'usage': usage,
        }
    except (AgentConfigurationError, AgentExecutionError):
        raise
    except TimeoutError as exc:
        raise AgentExecutionError('The AI provider timed out; try again later') from exc
    except Exception as exc:
        raise AgentExecutionError('The AI provider could not complete this assessment') from exc


async def run_evidence_analysis(user_id: str, prompt: str) -> dict:
    """The normal user workflow makes at most ONE LLM call, with zero tool calls."""
    return await _run(user_id, prompt, agent=analysis_agent, max_calls=1)


async def run_procurement_agent(user_id: str, prompt: str) -> str:
    """Legacy tool-using ADK entrypoint, also bounded (not used by /analyze)."""
    result = await _run(user_id, prompt, agent=root_agent, max_calls=3)
    return result['text']
