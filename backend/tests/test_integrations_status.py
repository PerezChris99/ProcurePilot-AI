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
            app_env="development",
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
    assert payload["database"]["schema_ready"] is True
    assert payload["database"]["engine"] == "sqlite"
    assert payload["runtime"]["provider_checks"] == "configuration_only"
    assert payload["ai"] == {
        "provider": "Google Gemini",
        "configured": True,
        "api_key_set": True,
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


def test_integration_status_tracks_missing_credentials_and_partial_paypal_setup(client, monkeypatch):
    monkeypatch.setattr(
        integrations, "get_settings",
        lambda: SimpleNamespace(
            app_env="development", google_api_key="   ", ai_model=None,
            channel3_api_key="YOUR-API-KEY",
            channel3_base_url="https://api.trychannel3.com/v1",
            paypal_client_id="merchant-client",
            paypal_client_secret="", paypal_webhook_id="",
            paypal_base_url="https://api-m.sandbox.paypal.com",
        ),
    )
    result = client.get("/api/v1/integrations/status", headers=_register(client))
    assert result.status_code == 200
    state = result.json()
    assert state["ai"]["configured"] is False
    assert state["ai"]["model"] == "gemini-3.8-flash"
    assert state["channel3"]["configured"] is False
    assert state["channel3"]["base_url_configured"] is True
    assert state["channel3"]["api_key_set"] is False
    assert state["paypal"]["client_id_set"] is True
    assert state["paypal"]["client_secret_set"] is False
    assert state["paypal"]["credentials_configured"] is False
    assert state["paypal"]["webhook_configured"] is False
    assert state["paypal"]["environment"] == "sandbox"
    assert "merchant-client" not in result.text


def test_configuration_helpers_reject_invalid_urls_and_template_credentials():
    assert integrations._set("  ") is False
    assert integrations._set("your-api-key") is False
    assert integrations._set("replace-with-your-key") is False
    assert integrations._set("provided-real-key") is True
    assert integrations._https_endpoint("http://api.example.com") is False
    assert integrations._https_endpoint("https://user:pass@api.example.com") is False
    assert integrations._https_endpoint("https://api.trychannel3.com/v1") is True
    assert integrations._paypal_mode("https://api-m.paypal.com") == "live"
    assert integrations._paypal_mode("https://unknown.example.com") == "unknown"

