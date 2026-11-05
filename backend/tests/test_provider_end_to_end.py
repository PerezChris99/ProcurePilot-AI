"""End-to-end API workflow with deterministic third-party stubs.

This proves local integration and authorization wiring; it does not prove live
Gemini credentials, Channel3 catalogue availability, a real buyer's Sandbox
approval, or the external PayPal signature-verification service.
"""
from decimal import Decimal
from types import SimpleNamespace

from app.agents import runtime
from app.api import procurement_requests as procurement_api
from app.integrations.channel3.client import Channel3Client
from app.integrations.channel3.schemas import (
    Channel3Offer,Channel3Price,Channel3Product,Channel3SearchResponse,
)
from app.integrations.paypal.client import PayPalClient


def test_request_to_ai_to_human_approval_to_paypal_capture_has_one_audit_trail(client,monkeypatch):
    calls={'channel3':0,'gemini':0,'create':0,'get':0,'capture':0,'verify':0}
    response=client.post('/api/v1/auth/register',json={
        'email':'full-flow-owner@example.com',
        'full_name':'Full Flow Owner',
        'password':'correct-horse-battery-staple',
    })
    assert response.status_code==201
    headers={'Authorization':'Bearer '+response.json()['access_token']}
    created=client.post('/api/v1/procurement-requests',headers=headers,json={
        'request_text':'Two office monitors with real retailer offers',
        'quantity':2,'budget':'300.00','currency':'USD',
    })
    assert created.status_code==201
    request_id=created.json()['id']

    async def channel3_search(self,query,*,limit=20,filters=None,user_id=None,page_token=None):
        calls['channel3']+=1
        assert user_id
        assert 'office monitors' in query
        assert page_token is None
        return Channel3SearchResponse(products=[
            Channel3Product(id='c3-monitor-smoke',title='Office monitor 27-inch',
                offers=[Channel3Offer(
                    url='https://retailer.example/p/monitor-smoke',
                    domain='retailer.example',
                    price=Channel3Price(amount=Decimal('120.00'),currency='USD'),
                    availability='InStock',
                )]),
        ])

    async def analyze_with_stub(user_id,prompt):
        calls['gemini']+=1
        assert 'c3-monitor-smoke' in prompt
        assert '120.00' in prompt
        return {
            'text':'Product c3-monitor-smoke has a USD 120.00 eligible offer. Delivery is unverified.',
            'model':'gemini-mock-contract','usage':{'input_tokens':150,'output_tokens':23},
        }

    monkeypatch.setattr(Channel3Client,'search_products',channel3_search)
    monkeypatch.setattr(runtime,'run_evidence_analysis',analyze_with_stub)
    monkeypatch.setattr(procurement_api,'get_settings',lambda:SimpleNamespace(
        google_api_key='local-test-only',
        ai_evidence_candidates=4,
        ai_daily_user_runs=12,
        ai_daily_global_runs=100,
    ))

    analyzed=client.post(f'/api/v1/procurement-requests/{request_id}/analyze',headers=headers)
    assert analyzed.status_code==200
    assert analyzed.json()['source']=='gemini'
    assert analyzed.json()['cached'] is False
    repeated=client.post(f'/api/v1/procurement-requests/{request_id}/analyze',headers=headers)
    assert repeated.status_code==200
    assert repeated.json()['cached'] is True
    assert calls['channel3']==1
    assert calls['gemini']==1

    po=client.post(f'/api/v1/procurement-requests/{request_id}/purchase-orders',headers=headers,json={
        'product_id':'c3-monitor-smoke',
        'offer_url':'https://retailer.example/p/monitor-smoke',
        'unit_price':'0.01',
    })
    assert po.status_code==201
    order=po.json()
    assert order['total_amount']=='240.00'
    assert order['items'][0]['unit_price']=='120.00'
    order_id=order['id']
    preapproval=client.post(f'/api/v1/purchase-orders/{order_id}/payments/paypal/create',headers=headers)
    assert preapproval.status_code==409

    submitted=client.post(f'/api/v1/purchase-orders/{order_id}/submit',headers=headers)
    assert submitted.status_code==200 and submitted.json()['status']=='pending_approval'
    approval=client.post(f'/api/v1/purchase-orders/{order_id}/approve',headers=headers,json={
        'comment':'Approved after comparing eligible source offers',
    })
    assert approval.status_code==200 and approval.json()['status']=='approved'

    async def paypal_create(self,**kwargs):
        calls['create']+=1
        assert kwargs['po_id']==order_id
        assert kwargs['amount']=='240.00'
        assert kwargs['unit_price']=='120.00'
        assert kwargs['quantity']==2
        assert kwargs['currency']=='USD'
        return {
            'id':'SANDBOX-ORDER-456','status':'PAYER_ACTION_REQUIRED',
            'links':[{'rel':'approve','href':'https://www.sandbox.paypal.com/checkoutnow?token=SANDBOX-ORDER-456'}],
        }

    async def paypal_get(self,paypal_order_id):
        calls['get']+=1
        assert paypal_order_id=='SANDBOX-ORDER-456'
        return {
            'id':paypal_order_id,'status':'APPROVED',
            'purchase_units':[{'custom_id':order_id,'amount':{
                'currency_code':'USD','value':'240.00',
            }}],
        }

    async def paypal_capture(self,paypal_order_id,idempotency_key):
        calls['capture']+=1
        assert paypal_order_id=='SANDBOX-ORDER-456'
        assert len(idempotency_key)==32
        return {
            'id':paypal_order_id,'status':'COMPLETED',
            'purchase_units':[{'custom_id':order_id,
                'amount':{'currency_code':'USD','value':'240.00'},
                'payments':{'captures':[{
                    'id':'SANDBOX-CAPTURE-456','status':'COMPLETED',
                    'amount':{'currency_code':'USD','value':'240.00'},
                }]},
            }],
        }

    async def paypal_verify(self,request_headers,event):
        calls['verify']+=1
        return True

    monkeypatch.setattr(PayPalClient,'ensure_configured',lambda self:None)
    monkeypatch.setattr(PayPalClient,'create_order',paypal_create)
    monkeypatch.setattr(PayPalClient,'get_order',paypal_get)
    monkeypatch.setattr(PayPalClient,'capture_order',paypal_capture)
    monkeypatch.setattr(PayPalClient,'verify_webhook',paypal_verify)

    checkout=client.post(f'/api/v1/purchase-orders/{order_id}/payments/paypal/create',headers=headers)
    assert checkout.status_code==200
    assert checkout.json()['approval_url'].startswith('https://www.sandbox.paypal.com/')
    duplicate_checkout=client.post(f'/api/v1/purchase-orders/{order_id}/payments/paypal/create',headers=headers)
    assert duplicate_checkout.status_code==200
    assert duplicate_checkout.json()['idempotent_replay'] is True
    assert calls['create']==1

    paid=client.post(f'/api/v1/purchase-orders/{order_id}/payments/paypal/capture',headers=headers)
    assert paid.status_code==200
    assert paid.json()['status']=='paid'
    assert paid.json()['payment']['capture_id']=='SANDBOX-CAPTURE-456'
    duplicate_capture=client.post(f'/api/v1/purchase-orders/{order_id}/payments/paypal/capture',headers=headers)
    assert duplicate_capture.status_code==200
    assert duplicate_capture.json()['status']=='paid'
    assert calls['get']==1 and calls['capture']==1

    event={
        'id':'WEBHOOK-FULL-FLOW-456',
        'event_type':'PAYMENT.CAPTURE.COMPLETED',
        'resource':{
            'id':'SANDBOX-CAPTURE-456','status':'COMPLETED',
            'amount':{'currency_code':'USD','value':'240.00'},
            'supplementary_data':{'related_ids':{'order_id':'SANDBOX-ORDER-456'}},
        },
    }
    first=client.post('/api/v1/webhooks/paypal',json=event)
    second=client.post('/api/v1/webhooks/paypal',json=event)
    assert first.status_code==200
    assert second.status_code==200
    assert second.json()['duplicate'] is True
    assert calls['verify']==2

    saved=client.get(f'/api/v1/purchase-orders/{order_id}',headers=headers)
    assert saved.status_code==200
    saved=saved.json()
    assert saved['status']=='paid'
    assert saved['payment']['status']=='completed'
    assert saved['total_amount']=='240.00'
    actions={entry['action'] for entry in saved['audit_events']}
    assert 'purchase_order.created' in actions
    assert 'purchase_order.submitted' in actions
    assert 'purchase_order.approved' in actions
    assert 'payment.paypal_order_created' in actions
    assert 'payment.paypal_capture_completed' in actions
    assert calls['channel3']==1 and calls['gemini']==1
    assert calls['create']==1 and calls['capture']==1
