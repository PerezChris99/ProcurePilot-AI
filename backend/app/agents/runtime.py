import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from app.agents.procurement_agent.agent import root_agent
from app.core.config import get_settings

class AgentConfigurationError(RuntimeError):
    pass

class AgentExecutionError(RuntimeError):
    pass

async def run_procurement_agent(user_id: str, prompt: str) -> str:
    settings=get_settings()
    if not settings.google_api_key:
        raise AgentConfigurationError('Gemini API credentials are not configured')
    session_service=InMemorySessionService()
    try:
        session=await session_service.create_session(app_name='procurepilot',user_id=user_id)
        runner=Runner(agent=root_agent,app_name='procurepilot',session_service=session_service)
        message=types.Content(role='user',parts=[types.Part(text=prompt)])
        final_text=None
        async with asyncio.timeout(45):
            async for event in runner.run_async(user_id=user_id,session_id=session.id,new_message=message):
                if event.is_final_response() and event.content and event.content.parts:
                    final_text=''.join(part.text or '' for part in event.content.parts if getattr(part,'text',None))
        if not final_text:
            raise AgentExecutionError('The procurement agent returned no final response')
        return final_text.strip()
    except (AgentConfigurationError,AgentExecutionError):
        raise
    except TimeoutError as exc:
        raise AgentExecutionError('The procurement agent timed out') from exc
    except Exception as exc:
        raise AgentExecutionError('The procurement agent could not complete this analysis') from exc
