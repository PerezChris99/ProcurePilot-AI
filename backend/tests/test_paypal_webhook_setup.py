"""PayPal Sandbox listener setup: all network calls mocked, no real checkout."""
import asyncio
import json

import httpx
import pytest

from scripts.configure_paypal_webhook import (
    CANONICAL_ENDPOINT, REQUIRED_EVENTS, WebhookSetupError, ensure_webhook,
)
from app.integrations.paypal.client import PayPalClient

WEBHOOK_ID = "0NH55953DH663215D"


def make_paypal(handler):
    client = PayPalClient(transport=httpx.MockTransport(handler))
    client.client_id = "sandbox-business-client"
    client.client_secret = "do-not-log-test-only-secret"
    return client


def oauth_reply(request):
    if request.url.path == "/v1/oauth2/token":
        return httpx.Response(200, json={"access_token": "test-access-token"})
    return None


def hook():
    return {
        "id": WEBHOOK_ID,
        "url": CANONICAL_ENDPOINT,
        "event_types": [{"name": name} for name in sorted(REQUIRED_EVENTS)],
    }


def test_matching_webhook_is_reused_no_duplicate_created(monkeypatch):
    monkeypatch.setenv("PAYPAL_WEBHOOK_URL", CANONICAL_ENDPOINT)
    observed = []

    def transport(request):
        response = oauth_reply(request)
        if response is not None:
            return response
        observed.append((request.method, request.url.path))
        assert request.method == "GET"
        return httpx.Response(200, json={"webhooks": [hook()]})

    result = asyncio.run(ensure_webhook(create=True, client=make_paypal(transport)))
    assert result == {"id": WEBHOOK_ID, "action": "existing", "url": CANONICAL_ENDPOINT}
    assert observed == [("GET", "/v1/notifications/webhooks")]


def test_missing_webhook_does_not_register_without_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("PAYPAL_WEBHOOK_URL", CANONICAL_ENDPOINT)
    observed = []

    def transport(request):
        response = oauth_reply(request)
        if response is not None:
            return response
        observed.append(request.method)
        assert request.method == "GET"
        return httpx.Response(200, json={"webhooks": []})

    result = asyncio.run(ensure_webhook(create=False, client=make_paypal(transport)))
    assert result["id"] is None
    assert result["action"] == "missing"
    assert observed == ["GET"]


def test_register_creates_once_then_confirms_same_app_webhook(monkeypatch):
    monkeypatch.setenv("PAYPAL_WEBHOOK_URL", CANONICAL_ENDPOINT)
    calls = []
    state = []

    def transport(request):
        response = oauth_reply(request)
        if response is not None:
            return response
        calls.append(request.method)
        if request.method == "GET":
            return httpx.Response(200, json={"webhooks": state})
        assert request.method == "POST"
        data = json.loads(request.content)
        assert request.url.path == "/v1/notifications/webhooks"
        assert data["url"] == CANONICAL_ENDPOINT
        assert {event["name"] for event in data["event_types"]} == REQUIRED_EVENTS
        state.append(hook())
        return httpx.Response(201, json=hook())

    paypal = make_paypal(transport)
    first = asyncio.run(ensure_webhook(create=True, client=paypal))
    second = asyncio.run(ensure_webhook(create=True, client=paypal))
    assert first["action"] == "created"
    assert second["action"] == "existing"
    assert first["id"] == second["id"] == WEBHOOK_ID
    assert calls == ["GET", "POST", "GET", "GET"]


def test_incomplete_existing_subscription_requires_review_instead_of_duplicate(monkeypatch):
    monkeypatch.setenv("PAYPAL_WEBHOOK_URL", CANONICAL_ENDPOINT)
    existing = {**hook(), "event_types": [{"name": "PAYMENT.CAPTURE.COMPLETED"}]}

    def transport(request):
        response = oauth_reply(request)
        if response is not None:
            return response
        assert request.method == "GET"
        return httpx.Response(200, json={"webhooks": [existing]})

    with pytest.raises(WebhookSetupError, match="webhook_missing_required_events"):
        asyncio.run(ensure_webhook(create=True, client=make_paypal(transport)))


@pytest.mark.parametrize("invalid", [
    "https://procurepilotai-preview.vercel.app/api/v1/webhooks/paypal",
    "https://evil.example.com/api/v1/webhooks/paypal",
    "http://procurepilotai.vercel.app/api/v1/webhooks/paypal",
    "https://procurepilotai.vercel.app/api/v1/webhooks/paypal?secret=token",
    "https://procurepilotai.vercel.app/api/v1/webhooks/paypal/",
])
def test_other_urls_fail_before_using_merchant_credentials(monkeypatch, invalid):
    monkeypatch.setenv("PAYPAL_WEBHOOK_URL", invalid)

    def forbidden(request):
        raise AssertionError("No PayPal credentials should be sent")

    with pytest.raises(WebhookSetupError, match="unexpected_webhook_target"):
        asyncio.run(ensure_webhook(create=True, client=make_paypal(forbidden)))


def test_unexpected_list_response_fails_closed(monkeypatch):
    monkeypatch.setenv("PAYPAL_WEBHOOK_URL", CANONICAL_ENDPOINT)

    def transport(request):
        response = oauth_reply(request)
        if response is not None:
            return response
        return httpx.Response(200, json={"webhooks": "not a list"})

    with pytest.raises(WebhookSetupError, match="unexpected_webhooks_list"):
        asyncio.run(ensure_webhook(create=False, client=make_paypal(transport)))
