from types import SimpleNamespace

from app.api import integrations


def _register(client, email="integrations@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Integration Tester",
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 201
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_integration_status_reports_configured_providers_without_secrets(
    client, monkeypatch
):
    monkeypatch.setattr(
        integrations,
        "get_settings",
        lambda: SimpleNamespace(
            google_api_key="private-gemini-key",
            ai_model="gemini-3.8-flash",
            channel3_api_key="private-channel3-key",
            channel3_base_url="https://api.trychannel3.com/v1",
            paypal_client_id="private-paypal-client-id",
            paypal_client_secret="private-paypal-secret",
            paypal_webhook_id="private-webhook-id",
            paypal_base_url="https://api-m.sandbox.paypal.com",
        ),
    )

    response = client.get(
        "/api/v1/integrations/status",
        headers=_register(client),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["database"]["connected"] is True
    assert payload["ai"] == {
        "provider": "Google Gemini",
        "configured": True,
        "model": "gemini-3.8-flash",
    }
    assert payload["channel3"]["configured"] is True
    assert payload["paypal"]["credentials_configured"] is True
    assert payload["paypal"]["webhook_configured"] is True
    assert payload["paypal"]["environment"] == "sandbox"

    for secret in (
        "private-gemini-key",
        "private-channel3-key",
        "private-paypal-client-id",
        "private-paypal-secret",
        "private-webhook-id",
    ):
        assert secret not in response.text


def test_integration_status_requires_authentication(client):
    response = client.get("/api/v1/integrations/status")
    assert response.status_code == 401
