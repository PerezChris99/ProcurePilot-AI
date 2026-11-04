from decimal import Decimal
from types import SimpleNamespace
import pytest
from app.integrations.channel3.client import Channel3Client
from app.integrations.channel3.schemas import Channel3Offer,Channel3Price,Channel3Product,Channel3SearchResponse
from app.integrations.paypal.client import PayPalClient

def register(client,email):
    response=client.post('/api/v1/auth/register',json={'email':email,'full_name':'Procurement Owner','password':'correct-horse-battery-staple'})
    assert response.status_code==201
    return {'Authorization':'Bearer '+response.json()['access_token']}

def make_order(client,monkeypatch,email='buyer@example.com',quantity=2,budget='500.00'):
    headers=register(client,email)
    created=client.post('/api/v1/procurement-requests',headers=headers,json={'request_text':'Two business monitors for the office','quantity':quantity,'budget':budget,'currency':'USD'})
    request_id=created.json()['id']
    async def search(self,query,*,limit=20,filters=None,user_id=None,page_token=None):
        return Channel3SearchResponse(products=[Channel3Product(id='monitor-real-1',title='Business monitor 27 inch',offers=[Channel3Offer(url='https://retailer.example/monitor',domain='retailer.example',price=Channel3Price(amount=Decimal('120.00'),currency='USD'),availability='InStock')])])
    monkeypatch.setattr(Channel3Client,'search_products',search)
    discovery=client.post(f'/api/v1/procurement-requests/{request_id}/discover',headers=headers)
    assert discovery.status_code==200
    response=client.post(f'/api/v1/procurement-requests/{request_id}/purchase-orders',headers=headers,json={'product_id':'monitor-real-1','offer_url':'https://retailer.example/monitor','unit_price':'0.01'})
    assert response.status_code==201
    return headers,response.json()

def fake_paypal(monkeypatch,po_id):
    async def create_order(self,**kwargs):
        return {'id':'PAYPAL-ORDER-123','status':'PAYER_ACTION_REQUIRED','links':[{'rel':'approve','href':'https://www.sandbox.paypal.com/checkoutnow?token=PAYPAL-ORDER-123'}]}
    async def get_order(self,order_id):
        return {'id':order_id,'status':'APPROVED','purchase_units':[{'custom_id':po_id,'amount':{'currency_code':'USD','value':'240.00'}}]}
    async def capture_order(self,order_id,idempotency_key):
        assert len(idempotency_key)==32
        return {'id':order_id,'status':'COMPLETED','purchase_units':[{'custom_id':po_id,'amount':{'currency_code':'USD','value':'240.00'},'payments':{'captures':[{'id':'CAPTURE-123','status':'COMPLETED','amount':{'currency_code':'USD','value':'240.00'}}]}}]}
    monkeypatch.setattr(PayPalClient,'ensure_configured',lambda self:None)
    monkeypatch.setattr(PayPalClient,'create_order',create_order)
    monkeypatch.setattr(PayPalClient,'get_order',get_order)
    monkeypatch.setattr(PayPalClient,'capture_order',capture_order)

def approved_order(client,monkeypatch,email):
    headers,order=make_order(client,monkeypatch,email=email)
    client.post(f"/api/v1/purchase-orders/{order['id']}/submit",headers=headers)
    client.post(f"/api/v1/purchase-orders/{order['id']}/approve",headers=headers,json={'comment':'Reviewed by the buyer'})
    return headers,order

def test_order_total_is_derived_from_saved_catalogue_offer_and_requires_human_approval(client,monkeypatch):
    headers,order=make_order(client,monkeypatch)
    assert order['total_amount']=='240.00'
    assert order['items'][0]['unit_price']=='120.00'
    assert order['items'][0]['quantity']==2
    assert client.post(f"/api/v1/purchase-orders/{order['id']}/payments/paypal/create",headers=headers).status_code==409
    submitted=client.post(f"/api/v1/purchase-orders/{order['id']}/submit",headers=headers)
    assert submitted.json()['status']=='pending_approval'
    approved=client.post(f"/api/v1/purchase-orders/{order['id']}/approve",headers=headers,json={'comment':'Reviewed against the request'})
    assert approved.json()['status']=='approved'
    assert approved.json()['approved_by']

def test_rejected_order_cannot_be_paid(client,monkeypatch):
    headers,order=make_order(client,monkeypatch,email='reject@example.com')
    client.post(f"/api/v1/purchase-orders/{order['id']}/submit",headers=headers)
    rejected=client.post(f"/api/v1/purchase-orders/{order['id']}/reject",headers=headers,json={'comment':'Budget approval declined'})
    assert rejected.json()['status']=='rejected'
    assert client.post(f"/api/v1/purchase-orders/{order['id']}/payments/paypal/create",headers=headers).status_code==409

def test_paypal_checkout_and_capture_complete_only_for_matching_approved_amount(client,monkeypatch):
    headers,order=approved_order(client,monkeypatch,'pay@example.com')
    fake_paypal(monkeypatch,order['id'])
    checkout=client.post(f"/api/v1/purchase-orders/{order['id']}/payments/paypal/create",headers=headers)
    assert checkout.status_code==200
    assert checkout.json()['approval_url'].startswith('https://www.sandbox.paypal.com/')
    assert 'idempotency_key' not in checkout.json()['payment']
    assert 'provider_response' not in checkout.json()['payment']
    captured=client.post(f"/api/v1/purchase-orders/{order['id']}/payments/paypal/capture",headers=headers)
    assert captured.status_code==200
    assert captured.json()['status']=='paid'
    assert captured.json()['payment']['status']=='completed'
    assert captured.json()['payment']['capture_id']=='CAPTURE-123'
    replay=client.post(f"/api/v1/purchase-orders/{order['id']}/payments/paypal/capture",headers=headers)
    assert replay.status_code==200
    assert replay.json()['status']=='paid'

def test_paypal_amount_mismatch_never_marks_purchase_order_paid(client,monkeypatch):
    headers,order=approved_order(client,monkeypatch,'mismatch@example.com')
    fake_paypal(monkeypatch,order['id'])
    async def mismatched_order(self,order_id):
        return {'id':order_id,'status':'APPROVED','purchase_units':[{'custom_id':order['id'],'amount':{'currency_code':'USD','value':'1.00'}}]}
    monkeypatch.setattr(PayPalClient,'get_order',mismatched_order)
    client.post(f"/api/v1/purchase-orders/{order['id']}/payments/paypal/create",headers=headers)
    response=client.post(f"/api/v1/purchase-orders/{order['id']}/payments/paypal/capture",headers=headers)
    assert response.status_code==409
    saved=client.get(f"/api/v1/purchase-orders/{order['id']}",headers=headers).json()
    assert saved['status']=='payment_pending'

def test_purchase_order_is_not_visible_to_another_user(client,monkeypatch):
    headers,order=make_order(client,monkeypatch,email='private@example.com')
    other=register(client,'other-buyer@example.com')
    assert client.get(f"/api/v1/purchase-orders/{order['id']}",headers=other).status_code==404
    assert client.get('/api/v1/purchase-orders',headers=other).json()==[]

def test_paypal_webhook_signature_is_required_and_duplicate_events_are_idempotent(client,monkeypatch):
    headers,order=approved_order(client,monkeypatch,'webhook@example.com')
    fake_paypal(monkeypatch,order['id'])
    client.post(f"/api/v1/purchase-orders/{order['id']}/payments/paypal/create",headers=headers)
    async def verified(self,request_headers,event): return True
    monkeypatch.setattr(PayPalClient,'verify_webhook',verified)
    event={'id':'WH-EVENT-001','event_type':'PAYMENT.CAPTURE.COMPLETED','resource':{'id':'CAPTURE-WH-1','status':'COMPLETED','amount':{'currency_code':'USD','value':'240.00'},'supplementary_data':{'related_ids':{'order_id':'PAYPAL-ORDER-123'}}}}
    first=client.post('/api/v1/webhooks/paypal',json=event)
    second=client.post('/api/v1/webhooks/paypal',json=event)
    assert first.status_code==200 and first.json()['duplicate'] is False
    assert second.status_code==200 and second.json()['duplicate'] is True
    saved=client.get(f"/api/v1/purchase-orders/{order['id']}",headers=headers).json()
    assert saved['status']=='paid'

def test_invalid_paypal_webhook_signature_is_rejected(client,monkeypatch):
    async def rejected(self,request_headers,event): return False
    monkeypatch.setattr(PayPalClient,'verify_webhook',rejected)
    response=client.post('/api/v1/webhooks/paypal',json={'id':'WH-BAD','event_type':'PAYMENT.CAPTURE.COMPLETED'})
    assert response.status_code==400

def test_paypal_base_url_rejects_untrusted_hosts(monkeypatch):
    import app.integrations.paypal.client as paypal_module
    from app.integrations.paypal.client import PayPalConfigurationError
    monkeypatch.setattr(paypal_module,'get_settings',lambda:SimpleNamespace(paypal_client_id='id',paypal_client_secret='secret',paypal_base_url='https://api-m.evilpaypal.com',paypal_webhook_id=''))
    with pytest.raises(PayPalConfigurationError): PayPalClient()

def test_out_of_stock_offer_cannot_become_a_purchase_order(client,monkeypatch):
    headers=register(client,'out-of-stock@example.com')
    created=client.post('/api/v1/procurement-requests',headers=headers,json={'request_text':'Find a replacement office monitor','quantity':1,'currency':'USD'})
    request_id=created.json()['id']
    async def search(self,query,*,limit=20,filters=None,user_id=None,page_token=None):
        return Channel3SearchResponse(products=[Channel3Product(id='monitor-oos',title='Out of stock monitor',offers=[Channel3Offer(url='https://retailer.example/oos',domain='retailer.example',price=Channel3Price(amount=Decimal('90.00'),currency='USD'),availability='OutOfStock')])])
    monkeypatch.setattr(Channel3Client,'search_products',search)
    client.post(f'/api/v1/procurement-requests/{request_id}/discover',headers=headers)
    response=client.post(f'/api/v1/procurement-requests/{request_id}/purchase-orders',headers=headers,json={'product_id':'monitor-oos','offer_url':'https://retailer.example/oos'})
    assert response.status_code==422
