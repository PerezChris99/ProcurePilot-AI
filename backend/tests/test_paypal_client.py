import asyncio

import httpx
import pytest

from app.integrations.paypal.client import PayPalClient


def test_paypal_request_uses_server_credentials_and_idempotency():
    calls = []

    def handler(request):
        calls.append(request)
        if request.url.path.endswith("/v1/oauth2/token"):
            assert request.headers["authorization"].startswith("Basic ")
            return httpx.Response(200, json={"access_token": "sandbox-token"})
        assert request.headers["authorization"] == "Bearer sandbox-token"
        assert request.headers["paypal-request-id"] == "stable-request-key"
        return httpx.Response(201, json={"id": "ORDER-123", "status": "CREATED"})

    client = PayPalClient(transport=httpx.MockTransport(handler))
    client.client_id = "client-id"
    client.client_secret = "client-secret"
    result = asyncio.run(
        client._request(
            "POST",
            "/v2/checkout/orders",
            payload={"intent": "CAPTURE"},
            request_id="stable-request-key",
        )
    )
    assert result["id"] == "ORDER-123"
    assert len(calls) == 2


def test_get_order_uses_validated_id_and_returns_remote_order():
    calls = []

    def handler(request):
        calls.append((request.method, request.url.path))
        if request.url.path.endswith("/v1/oauth2/token"):
            return httpx.Response(200, json={"access_token": "sandbox-token"})
        return httpx.Response(200, json={"id": "ORDER-123", "status": "APPROVED"})

    client = PayPalClient(transport=httpx.MockTransport(handler))
    client.client_id = "client-id"
    client.client_secret = "client-secret"

    result = asyncio.run(client.get_order("ORDER-123"))

    assert result == {"id": "ORDER-123", "status": "APPROVED"}
    assert calls[-1] == ("GET", "/v2/checkout/orders/ORDER-123")


def test_capture_order_uses_validated_id_and_idempotency_key():
    calls = []

    def handler(request):
        calls.append(request)
        if request.url.path.endswith("/v1/oauth2/token"):
            return httpx.Response(200, json={"access_token": "sandbox-token"})
        return httpx.Response(
            201,
            json={
                "id": "ORDER-123",
                "status": "COMPLETED",
                "purchase_units": [{"payments": {"captures": [{"id": "CAPTURE-123"}]}}],
            },
        )

    client = PayPalClient(transport=httpx.MockTransport(handler))
    client.client_id = "client-id"
    client.client_secret = "client-secret"

    result = asyncio.run(client.capture_order("ORDER-123", "capture-idempotency-key"))

    assert result["status"] == "COMPLETED"
    assert calls[-1].method == "POST"
    assert calls[-1].url.path == "/v2/checkout/orders/ORDER-123/capture"
    assert calls[-1].headers["paypal-request-id"] == "capture-idempotency-key"


@pytest.mark.parametrize("method,args", [
    ("get_order", ("bad/order",)),
    ("capture_order", ("bad/order", "idempotency-key")),
])
def test_order_retrieval_and_capture_reject_invalid_ids_before_network(method, args):
    def handler(request):
        raise AssertionError("No HTTP request should be made for an invalid PayPal order ID")

    client = PayPalClient(transport=httpx.MockTransport(handler))
    client.client_id = "client-id"
    client.client_secret = "client-secret"

    with pytest.raises(ValueError, match="Invalid PayPal order ID"):
        asyncio.run(getattr(client, method)(*args))


def test_webhook_verification_posts_paypal_transmission_headers():
    calls = []

    def handler(request):
        if request.url.path.endswith("/v1/oauth2/token"):
            return httpx.Response(200, json={"access_token": "token"})
        calls.append(request)
        return httpx.Response(200, json={"verification_status": "SUCCESS"})

    client = PayPalClient(transport=httpx.MockTransport(handler))
    client.client_id = "client"
    client.client_secret = "secret"
    client.webhook_id = "webhook-1"
    headers = {
        "paypal-auth-algo": "SHA256withRSA",
        "paypal-cert-url": "https://api-m.sandbox.paypal.com/cert",
        "paypal-transmission-id": "transmission-1",
        "paypal-transmission-sig": "signature",
        "paypal-transmission-time": "2026-11-04T10:00:00Z",
    }
    verified = asyncio.run(
        client.verify_webhook(
            headers, {"id": "event-1", "event_type": "PAYMENT.CAPTURE.COMPLETED"}
        )
    )
    assert verified is True
    assert b'"webhook_id":"webhook-1"' in calls[0].read()


def test_approval_url_only_allows_paypal_checkout_hosts():
    assert PayPalClient.is_approval_url(
        "https://www.sandbox.paypal.com/checkoutnow?token=abc"
    )
    assert PayPalClient.is_approval_url("https://www.paypal.com/checkoutnow?token=abc")
    assert not PayPalClient.is_approval_url("https://evil.example/checkout")
    assert not PayPalClient.is_approval_url("http://www.sandbox.paypal.com/checkoutnow")
    assert not PayPalClient.is_approval_url(
        "https://www.sandbox.paypal.com:8443/checkoutnow"
    )


def test_sandbox_oauth_rejects_expired_credentials_without_disclosing_tokens():
    from app.integrations.paypal.client import PayPalUnavailable
    requests=[]
    def handler(request):
        requests.append(request)
        assert request.url.host=='api-m.sandbox.paypal.com'
        assert request.url.path=='/v1/oauth2/token'
        return httpx.Response(401,json={'error':'invalid_client'})
    client=PayPalClient(transport=httpx.MockTransport(handler))
    client.client_id='invalid-id'
    client.client_secret='invalid-secret'
    with pytest.raises(PayPalUnavailable,match='PayPal authentication failed') as result:
        asyncio.run(client._access_token())
    assert len(requests)==1
    assert 'invalid-secret' not in str(result.value)


def test_create_order_sends_exact_approved_amount_and_sandbox_return_urls():
    import json
    payloads=[]
    def handler(request):
        if request.url.path.endswith('/v1/oauth2/token'):
            return httpx.Response(200,json={'access_token':'test-sandbox-token'})
        payloads.append(json.loads(request.read()))
        assert request.url.host=='api-m.sandbox.paypal.com'
        assert request.url.path=='/v2/checkout/orders'
        assert request.headers['PayPal-Request-Id']=='po-unique-key'
        return httpx.Response(201,json={'id':'ORDER-123','status':'CREATED'})
    client=PayPalClient(transport=httpx.MockTransport(handler))
    client.client_id='sandbox-merchant'
    client.client_secret='sandbox-secret'
    result=asyncio.run(client.create_order(
        po_id='purchase-order-123',
        po_number='PP-123',
        amount='240.00',
        currency='USD',
        description='27 inch office monitor',
        quantity=2,
        unit_price='120.00',
        idempotency_key='po-unique-key',
        return_url='http://localhost:5173/orders?paypal=return',
        cancel_url='http://localhost:5173/orders?paypal=cancel',
    ))
    assert result['id']=='ORDER-123'
    p=payloads[0]
    assert p['intent']=='CAPTURE'
    assert p['purchase_units'][0]['amount']['value']=='240.00'
    assert p['purchase_units'][0]['amount']['currency_code']=='USD'
    assert p['purchase_units'][0]['custom_id']=='purchase-order-123'
    assert p['purchase_units'][0]['items'][0]['quantity']=='2'
    assert p['purchase_units'][0]['items'][0]['unit_amount']['value']=='120.00'
    assert p['payment_source']['paypal']['experience_context']['shipping_preference']=='NO_SHIPPING'
    assert p['payment_source']['paypal']['experience_context']['return_url'].startswith('http://localhost:5173/')


def test_hackathon_checkout_refuses_live_paypal_credentials_before_network():
    from app.integrations.paypal.client import PayPalConfigurationError
    def forbidden(request):
        raise AssertionError("Live PayPal must never be called by the hackathon build")
    client=PayPalClient(transport=httpx.MockTransport(forbidden))
    client.base_url="https://api-m.paypal.com"
    client.client_id="live-client-id"
    client.client_secret="live-client-secret"
    with pytest.raises(PayPalConfigurationError,match="Sandbox transactions only"):
        asyncio.run(client._access_token())


def test_paypal_oauth_retries_single_503_without_replaying_payment_mutations():
    calls=[]
    def handler(request):
        calls.append(request)
        if request.url.path.endswith('/v1/oauth2/token'):
            if sum(r.url.path.endswith('/v1/oauth2/token') for r in calls)==1:
                return httpx.Response(503,json={'error':'unavailable'})
            return httpx.Response(200,json={'access_token':'sandbox-token'})
        assert request.headers['paypal-request-id']=='capture-stable-key'
        return httpx.Response(503,json={'error':'capture uncertain'})
    client=PayPalClient(transport=httpx.MockTransport(handler))
    client.client_id='test-client'
    client.client_secret='test-secret'
    from app.integrations.paypal.client import PayPalUnavailable
    with pytest.raises(PayPalUnavailable):
        asyncio.run(client.capture_order('ORDER-123','capture-stable-key'))
    assert sum(r.url.path.endswith('/v1/oauth2/token') for r in calls)==2
    assert sum(r.url.path.endswith('/capture') for r in calls)==1


@pytest.mark.parametrize('code',[401,403,429])
def test_paypal_oauth_does_not_retry_invalid_or_limited_access(code):
    requests=[]
    def handler(request):
        requests.append(request)
        return httpx.Response(code,json={'error':'not-retryable'})
    client=PayPalClient(transport=httpx.MockTransport(handler))
    client.client_id='sandbox-client'
    client.client_secret='sandbox-secret'
    from app.integrations.paypal.client import PayPalUnavailable
    with pytest.raises(PayPalUnavailable):
        asyncio.run(client._access_token())
    assert len(requests)==1
