"""Ensure Vercel's ASGI entrypoint starts in production mode offline.

The example DB is intentionally unreachable; no database, provider calls,
migrations or payments are made.
"""
from pathlib import Path
import os
import subprocess
import sys

BACKEND = Path(__file__).resolve().parents[1]


def test_fastapi_vercel_entrypoint_imports_in_production_and_serves_health():
    env = os.environ.copy()
    env.update({
        "APP_ENV": "production",
        "FRONTEND_URL": "https://procurepilotai.vercel.app",
        "DATABASE_URL": "postgresql+psycopg://test:local-only@127.0.0.1:5432/procurepilot?sslmode=require",
        "JWT_SECRET_KEY": "S9w!E5b@Y7z#X3v$N6q%H2a&K4p*D8f?T",
        "RATE_LIMIT_REDIS_URL": "",
        "GOOGLE_API_KEY": "",
        "GROQ_API_KEY": "",
        "OPENROUTER_API_KEY": "",
        "CHANNEL3_API_KEY": "",
        "PAYPAL_CLIENT_ID": "",
        "PAYPAL_CLIENT_SECRET": "",
        "PAYPAL_WEBHOOK_ID": "",
    })
    program = """
from main import app
from fastapi.testclient import TestClient
with TestClient(app) as client:
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    assert response.json().get('status') == 'ok'
    auth = client.get('/api/v1/auth/me')
    assert auth.status_code == 401
"""
    proc = subprocess.run([sys.executable, "-c", program], cwd=BACKEND,
                          env=env, capture_output=True, text=True, timeout=45)
    # A Python traceback could contain environment context; don't echo it.
    assert proc.returncode == 0, (
        "Production-mode Vercel ASGI import/health failed. "
        "Investigate with local-only test credentials before deploying."
    )
