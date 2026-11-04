"""Local Vite host aliases and CORS preflight behavior.

Only the browser origin aliases are relaxed in development; authentication
remains enforced and production uses a single configured HTTPS origin.
"""
from app.main import allowed_frontend_origins


def test_localhost_and_ipv4_loopback_share_dev_cors_allowlist():
    assert allowed_frontend_origins('http://localhost:5173', 'development') == [
        'http://localhost:5173', 'http://127.0.0.1:5173',
    ]
    assert allowed_frontend_origins('http://127.0.0.1:5173', 'development') == [
        'http://127.0.0.1:5173', 'http://localhost:5173',
    ]


def test_dev_cors_does_not_permit_unrelated_hosts():
    assert allowed_frontend_origins('https://workspace.example.com', 'development') == [
        'https://workspace.example.com',
    ]


def test_public_environment_has_exact_origin_only():
    for environment in ('production', 'staging'):
        assert allowed_frontend_origins('https://frontend.example.com', environment) == [
            'https://frontend.example.com',
        ]


def _preflight(client, origin, endpoint='/api/v1/auth/login', method='POST'):
    return client.options(endpoint, headers={
        'Origin': origin,
        'Access-Control-Request-Method': method,
        'Access-Control-Request-Headers': 'content-type',
    })


def test_preflight_allows_configured_frontend_origin(client):
    from app.core.config import get_settings
    configured = get_settings()
    allowed = allowed_frontend_origins(configured.frontend_url, configured.app_env)
    for origin in allowed:
        response = _preflight(client, origin)
        assert response.status_code == 200, (origin, response.text)
        assert response.headers['access-control-allow-origin'] == origin


def test_preflight_rejects_foreign_websites(client):
    response = _preflight(client, 'https://untrusted.example.com')
    assert response.status_code == 400
    assert 'access-control-allow-origin' not in response.headers


def test_cors_preflight_does_not_skip_authentication(client):
    from app.core.config import get_settings
    origin = allowed_frontend_origins(
        get_settings().frontend_url, get_settings().app_env,
    )[0]
    assert _preflight(client, origin, '/api/v1/auth/me', method='GET').status_code == 200
    response = client.get('/api/v1/auth/me', headers={'Origin': origin})
    assert response.status_code == 401
