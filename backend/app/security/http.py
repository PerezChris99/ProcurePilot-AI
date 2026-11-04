"""ASGI response-security and request-size guard for the FastAPI JSON API.

Does not trust forwarded headers, and preserves CORS/preflight responses.
The deployment reverse proxy must also impose its own header/body/time limits.
"""
from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse


class _PayloadTooLarge(Exception):
    pass


class SecurityMiddleware:
    def __init__(self, app, *, max_body_bytes: int, production: bool):
        self.app = app
        self.max_body_bytes = max_body_bytes
        self.production = production

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        path = scope.get('path', '')
        response_started = False

        async def secure_send(message):
            nonlocal response_started
            if message['type'] == 'http.response.start':
                response_started = True
                headers = MutableHeaders(scope=message)
                headers['X-Content-Type-Options'] = 'nosniff'
                headers['X-Frame-Options'] = 'DENY'
                headers['Referrer-Policy'] = 'no-referrer'
                headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
                if path.startswith('/api/'):
                    headers['Cache-Control'] = 'no-store'
                    headers['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
                if self.production:
                    headers['Strict-Transport-Security'] = 'max-age=31536000'
            await send(message)

        async def reject(status, detail):
            response = JSONResponse({'detail': detail}, status_code=status)
            await response(scope, receive, secure_send)

        length_headers = [
            value for key, value in scope.get('headers', [])
            if key.lower() == b'content-length'
        ]
        if length_headers:
            try:
                if len(length_headers) != 1:
                    raise ValueError()
                length = int(length_headers[0].decode('ascii'))
                if length < 0:
                    raise ValueError()
            except (ValueError, UnicodeDecodeError):
                await reject(400, 'Invalid Content-Length')
                return
            if length > self.max_body_bytes:
                await reject(413, 'Request body exceeds size limit')
                return

        total = 0
        async def guarded_receive():
            nonlocal total
            message = await receive()
            if message['type'] == 'http.request':
                total += len(message.get('body', b''))
                if total > self.max_body_bytes:
                    raise _PayloadTooLarge()
            return message

        try:
            await self.app(scope, guarded_receive, secure_send)
        except _PayloadTooLarge:
            if response_started:
                raise
            await reject(413, 'Request body exceeds size limit')
