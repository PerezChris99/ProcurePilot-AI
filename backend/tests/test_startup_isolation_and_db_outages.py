"""Prevent AI SDK outages from taking down auth and expose safe Neon outages."""
import os
from pathlib import Path
import subprocess
import sys

from sqlalchemy.exc import OperationalError

BACKEND = Path(__file__).resolve().parents[1]


def test_asgi_bootstrap_and_auth_routes_do_not_import_google_adk():
    """Cold-import app.main in an isolated interpreter with ADK unavailable.

    A runtime dependency regression must not turn GET /health or the auth route
    registration into an ASGI import error on Vercel.
    """
    script = """
import builtins
old_import = builtins.__import__
def isolated(name, globals=None, locals=None, fromlist=(), level=0):
    if name.startswith('google.adk') or name == 'app.agents.runtime':
        raise RuntimeError('AI SDK imported during health/auth startup')
    return old_import(name, globals, locals, fromlist, level)
builtins.__import__ = isolated
from app.main import app
from fastapi.testclient import TestClient
with TestClient(app) as client:
    response = client.get('/api/v1/health')
    assert response.status_code == 200, response.status_code
    paths = set(app.openapi()['paths'])
    assert '/api/v1/auth/login' in paths
    assert '/api/v1/auth/register' in paths
    assert '/api/v1/ready' in paths
"""
    env = os.environ.copy()
    env.update({
        'APP_ENV': 'test',
        'DATABASE_URL': 'sqlite://',
        'JWT_SECRET_KEY': 'isolated-test-only-do-not-use-in-production',
        'GOOGLE_API_KEY': '',
        'GROQ_API_KEY': '',
        'OPENROUTER_API_KEY': '',
    })
    proc = subprocess.run(
        [sys.executable, '-c', script], cwd=BACKEND,
        env=env, text=True, capture_output=True, timeout=45,
    )
    assert proc.returncode == 0, (
        'FastAPI startup still depends on AI SDK initialization; '
        'verify import graph locally using non-secret test configuration.'
    )


def test_protected_endpoints_return_safe_503_on_neon_failure(client):
    from app.main import app
    from app.core.database import get_db

    created = client.post('/api/v1/auth/register', json={
        'email': 'outage-contract@example.com',
        'full_name': 'Outage Contract',
        'password': 'correct-horse-battery-staple',
    })
    assert created.status_code == 201
    token = created.json()['access_token']

    class BrokenSession:
        def get(self, model, key):
            raise OperationalError('SELECT users', {}, Exception(
                'postgresql+psycopg://private:secret@example.test/procurepilot'
            ))

    def unavailable():
        yield BrokenSession()

    original = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = unavailable
    try:
        response = client.get('/api/v1/auth/me', headers={
            'Authorization': 'Bearer ' + token,
        })
        assert response.status_code == 503
        assert response.headers['retry-after'] == '15'
        assert response.json()['detail'] == (
            'Database is temporarily unavailable. Please retry shortly.'
        )
        assert 'private' not in response.text
        assert 'postgresql' not in response.text
    finally:
        if original is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = original
