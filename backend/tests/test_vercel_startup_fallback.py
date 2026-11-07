"""Fail-closed Vercel entrypoint: no passwords or traceback in HTTP responses."""
import asyncio
import builtins
import json
from pathlib import Path
import runpy
from types import SimpleNamespace

import pytest

ENTRY = Path(__file__).resolve().parents[1] / 'main.py'


@pytest.mark.parametrize(('failure', 'expected'), [
    (ModuleNotFoundError('private-secret-shall-not-leak'), 'missing_runtime_dependency'),
    (ImportError('private-secret-shall-not-leak'), 'runtime_import_failure'),
    (type('ValidationError', (Exception,), {})('private-secret-shall-not-leak'),
     'invalid_configuration'),
    (RuntimeError('private-secret-shall-not-leak'), 'startup_initialization_failure'),
])
def test_failed_import_returns_safe_503(monkeypatch, failure, expected):
    original_import = builtins.__import__

    def failing_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'app.main':
            raise failure
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, '__import__', failing_import)
    namespace = runpy.run_path(str(ENTRY), run_name='vercel_startup_test')
    monkeypatch.setattr(builtins, '__import__', original_import)
    app = namespace['app']
    sent = []

    async def receive():
        return {'type': 'http.request', 'body': b'', 'more_body': False}

    async def send(event):
        sent.append(event)

    asyncio.run(app({'type': 'http', 'method': 'GET',
                     'path': '/api/v1/health', 'headers': []}, receive, send))
    assert sent[0]['status'] == 503
    headers = dict(sent[0]['headers'])
    assert headers[b'cache-control'] == b'no-store'
    data = json.loads(sent[1]['body'])
    assert data == {'status': 'unavailable',
                    'code': 'BACKEND_STARTUP_FAILED', 'category': expected}
    assert b'private-secret-shall-not-leak' not in sent[1]['body']


def test_fail_closed_lifespan_shutdown(monkeypatch):
    original_import = builtins.__import__
    def failing_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'app.main':
            raise RuntimeError('internal')
        return original_import(name, globals, locals, fromlist, level)
    monkeypatch.setattr(builtins, '__import__', failing_import)
    namespace = runpy.run_path(str(ENTRY), run_name='vercel_startup_lifespan_test')
    monkeypatch.setattr(builtins, '__import__', original_import)
    app = namespace['app']
    messages = [{'type': 'lifespan.startup'}, {'type': 'lifespan.shutdown'}]
    sent = []
    async def receive():
        return messages.pop(0)
    async def send(event):
        sent.append(event)
    asyncio.run(app({'type': 'lifespan'}, receive, send))
    assert [x['type'] for x in sent] == ['lifespan.startup.complete',
                                        'lifespan.shutdown.complete']


def test_vercel_static_scanner_finds_top_level_app_assignment():
    import ast
    module = ast.parse(ENTRY.read_text(encoding='utf-8'))
    exported = any(
        isinstance(node, (ast.Assign, ast.AnnAssign)) and
        any(isinstance(target, ast.Name) and target.id == 'app'
            for target in (node.targets if isinstance(node, ast.Assign)
                           else [node.target]))
        for node in module.body
    )
    assert exported, 'Vercel PYTHON_HANDLER_NOT_FOUND: app must be top-level'
