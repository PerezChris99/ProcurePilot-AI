"""Bounded ADK execution for predictable token use and safe operation."""
import asyncio
import time

from google.adk.agents.run_config import RunConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agents.procurement_agent.agent import analysis_agent, root_agent
from app.core.config import get_settings


class AgentConfigurationError(RuntimeError):
    pass


class AgentExecutionError(RuntimeError):
    def __init__(self, message, *, category='provider_error', http_status=None,
                 origin=None, elapsed_seconds=None, timeout_seconds=None):
        super().__init__(message)
        self.category = category
        self.http_status = http_status
        # Diagnostic metadata only; never pass raw provider exception messages.
        self.origin = origin
        self.elapsed_seconds = elapsed_seconds
        self.timeout_seconds = timeout_seconds


def _classify_provider_failure(code=None, message=None):
    """Return a safe category; never expose provider messages or credentials."""
    content = (str(code or '') + ' ' + str(message or '')).lower()
    if any(term in content for term in (
        'access_token_type_unsupported', 'unauthenticated', 'invalid_api_key',
        'api key not valid', 'api_key_invalid', '401',
    )):
        return 'authentication'
    if 'permission_denied' in content or '403' in content:
        return 'permission_denied'
    if any(term in content for term in ('resource_exhausted', 'rate_limit', 'quota', '429')):
        return 'quota_or_rate_limit'
    if any(term in content for term in ('not_found', '404', 'model not found')):
        return 'model_access'
    if any(term in content for term in ('closed', 'connection', 'transport', 'ssl', 'certificate')):
        return 'transport'
    if any(term in content for term in ('deadline_exceeded', 'timed out', 'timeout')):
        return 'timeout'
    if any(term in content for term in ('internal', 'unavailable', '500', '502', '503')):
        return 'provider_unavailable'
    return 'provider_error'


def _exception_details(exc):
    """Inspect a bounded exception chain without leaking raw exception text."""
    seen = set()
    pending = [exc]
    for _ in range(8):
        if not pending:
            break
        current = pending.pop(0)
        if id(current) in seen:
            continue
        seen.add(id(current))
        status = getattr(current, 'code', None)
        if not isinstance(status, int) or not 400 <= status <= 599:
            status = None
        category = _classify_provider_failure(
            getattr(current, 'status', None) or status or type(current).__name__,
            str(current),
        )
        if category != 'provider_error':
            return category, status
        for linked in (getattr(current, '__cause__', None),
                       getattr(current, '__context__', None),
                       getattr(current, 'error', None)):
            if isinstance(linked, BaseException) and id(linked) not in seen:
                pending.append(linked)
    return 'provider_error', None


def _usage_from_event(event):
    metadata = getattr(event, 'usage_metadata', None)
    if metadata is None:
        return None
    keys = (
        ('input_tokens', 'prompt_token_count'),
        ('output_tokens', 'candidates_token_count'),
        ('total_tokens', 'total_token_count'),
        ('cached_input_tokens', 'cached_content_token_count'),
        ('thinking_tokens', 'thoughts_token_count'),
    )
    return {name: getattr(metadata, attribute, None) for name, attribute in keys}


async def _run(user_id: str, prompt: str, *, agent, max_calls: int, timeout_seconds=None):
    settings = get_settings()
    if not settings.google_api_key:
        raise AgentConfigurationError('Gemini API credentials are not configured')
    if not prompt.strip() or len(prompt) > 10_000:
        raise AgentExecutionError('The evidence packet is invalid or exceeds the allowed size')
    limit = settings.ai_timeout_seconds if timeout_seconds is None else timeout_seconds
    # Accept a bounded diagnostic override, without ever disabling the wall clock limit.
    if type(limit) is not int or not 10 <= limit <= 90:
        raise AgentConfigurationError('AI timeout must be an integer between 10 and 90 seconds')
    session_service = InMemorySessionService()
    started = time.monotonic()
    # The expiry flag distinguishes our deadline from a provider TimeoutError.
    # Both paths still use the genuine Google ADK Runner and the same call cap.
    deadline = asyncio.timeout(limit)
    try:
        session = await session_service.create_session(
            app_name='procurepilot', user_id=user_id
        )
        runner = Runner(agent=agent, app_name='procurepilot', session_service=session_service)
        message = types.Content(role='user', parts=[types.Part(text=prompt)])
        final_text = None
        usage = None
        async with deadline:
            async for event in runner.run_async(
                user_id=user_id, session_id=session.id, new_message=message,
                run_config=RunConfig(max_llm_calls=max_calls),
            ):
                # ADK 2.x may emit an error event without throwing the original
                # provider exception. Do not silently turn it into "no final text".
                event_error = getattr(event, 'error_code', None)
                if event_error:
                    category = _classify_provider_failure(
                        event_error, getattr(event, 'error_message', None)
                    )
                    raise AgentExecutionError(
                        'Gemini ADK reported an unsuccessful model call',
                        category=category,
                        origin='adk_error_event',
                        elapsed_seconds=round(time.monotonic() - started, 2),
                        timeout_seconds=limit if category == 'timeout' else None,
                    )
                metrics = _usage_from_event(event)
                if metrics:
                    usage = {**(usage or {}), **{key: value for key, value in metrics.items() if value is not None}}
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
        # TimeoutError can originate in the provider client, *or* from our
        # asyncio.timeout context. The old code collapsed them together.
        raise AgentExecutionError(
            'The AI provider timed out; try again later',
            category='timeout',
            origin='local_deadline' if deadline.expired() else 'provider_exception',
            elapsed_seconds=round(time.monotonic() - started, 2),
            timeout_seconds=limit if deadline.expired() else None,
        ) from exc
    except Exception as exc:
        category, status = _exception_details(exc)
        raise AgentExecutionError(
            'The AI provider could not complete this assessment',
            category=category, http_status=status,
            origin='provider_exception',
            elapsed_seconds=round(time.monotonic() - started, 2),
        ) from exc


async def run_evidence_analysis(user_id: str, prompt: str, *, timeout_seconds=None) -> dict:
    """One ADK model call, zero tools; optional bounded timeout for smoke probes."""
    return await _run(
        user_id, prompt, agent=analysis_agent, max_calls=1,
        timeout_seconds=timeout_seconds,
    )


async def run_procurement_agent(user_id: str, prompt: str) -> str:
    """Legacy tool-using ADK entrypoint, also bounded (not used by /analyze)."""
    result = await _run(user_id, prompt, agent=root_agent, max_calls=3)
    return result['text']
