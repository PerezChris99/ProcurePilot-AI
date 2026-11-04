import asyncio
import httpx
from app.integrations.paypal.client import PayPalClient

def test_paypal_request_uses_server_credentials_and_idempotency():
    calls=[]
    def handler(request):
        calls.append(request)
        if request.url.path.endswith('/v1/oauth2/token'):
            assert request.headers['authorization'].startswith('Basic ')
            return httpx.Response(200,json={'access_token':'sandbox-token'})
        assert request.headers['authorization']=='Bearer sandbox-token'
        assert request.headers['paypal-request-id']=='stable-request-key'
        return httpx.Response(201,json={'id':'ORDER-123','status':'CREATED'})
    client=PayPalClient(transport=httpx.MockTransport(handler))
    client.client_id='client-id'; client.client_secret='client-secret'
    result=asyncio.run(client._request('POST','/v2/checkout/orders',payload={'intent':'CAPTURE'},request_id='stable-request-key'))
    assert result['id']=='ORDER-123'
    assert len(calls)==2

def test_webhook_verification_posts_paypal_transmission_headers():
    calls=[]
    def handler(request):
        if request.url.path.endswith('/v1/oauth2/token'): return httpx.Response(200,json={'access_token':'token'})
        calls.append(request)
        return httpx.Response(200,json={'verification_status':'SUCCESS'})
    client=PayPalClient(transport=httpx.MockTransport(handler))
    client.client_id='client'; client.client_secret='secret'; client.webhook_id='webhook-1'
    headers={'paypal-auth-algo':'SHA256withRSA','paypal-cert-url':'https://api-m.sandbox.paypal.com/cert','paypal-transmission-id':'transmission-1','paypal-transmission-sig':'signature','paypal-transmission-time':'2026-11-04T10:00:00Z'}
    verified=asyncio.run(client.verify_webhook(headers,{'id':'event-1','event_type':'PAYMENT.CAPTURE.COMPLETED'}))
    assert verified is True
    assert b'"webhook_id":"webhook-1"' in calls[0].read()
