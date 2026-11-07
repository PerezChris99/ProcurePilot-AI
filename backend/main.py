"""Vercel Services ASGI entrypoint.

Startup failures must fail closed, not silently expose the app or sensitive
configuration. Return a minimal 503 diagnostic category when initialization
fails; the real exception message and credential-bearing URL are never sent
over HTTP or written to logs.
"""
import json
import logging

try:
    from app.main import app as _loaded_app
except Exception as _initialization_error:
    def _classify_failure(error):
        if isinstance(error, ModuleNotFoundError):
            return 'missing_runtime_dependency'
        if isinstance(error, ImportError):
            return 'runtime_import_failure'
        if type(error).__name__ in ('ValidationError', 'SettingsError'):
            return 'invalid_configuration'
        return 'startup_initialization_failure'

    _category = _classify_failure(_initialization_error)
    logging.getLogger('procurepilot.startup').error(
        'Backend startup unavailable; category=%s', _category
    )

    async def _loaded_app(scope, receive, send):
        if scope['type'] == 'lifespan':
            while True:
                msg = await receive()
                if msg['type'] == 'lifespan.startup':
                    await send({'type': 'lifespan.startup.complete'})
                elif msg['type'] == 'lifespan.shutdown':
                    await send({'type': 'lifespan.shutdown.complete'})
                    return
        elif scope['type'] == 'http':
            body = json.dumps({
                'status': 'unavailable',
                'code': 'BACKEND_STARTUP_FAILED',
                'category': _category,
            }).encode('utf-8')
            await send({
                'type': 'http.response.start',
                'status': 503,
                'headers': [
                    (b'content-type', b'application/json'),
                    (b'cache-control', b'no-store'),
                    (b'retry-after', b'15'),
                    (b'x-content-type-options', b'nosniff'),
                ],
            })
            await send({'type': 'http.response.body', 'body': body})
        elif scope['type'] == 'websocket':
            await send({'type': 'websocket.close', 'code': 1011})

app = _loaded_app

__all__ = ['app']
