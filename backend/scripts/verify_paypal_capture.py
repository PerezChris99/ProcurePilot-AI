"""No-network, no-pytest PayPal capture contract acceptance for Vercel Preview.

The test suite makes ZERO real PayPal/Channel3 HTTP requests, never touches
Neon (in-memory SQLite), and never creates a real charge. This complements
pytest tests/test_purchase_orders.py, which developers run locally.
"""
from __future__ import annotations

import io
import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from app.api.purchase_orders import (
    _paypal_order_matches, _paypal_completed_capture,
    _paypal_capture_response_noncontradictory,
)
from app.integrations.paypal.client import PayPalClient

ORDER=SimpleNamespace(id="11111111-2222-3333-4444-555555555555",
                      po_number="PP-20261108-ABCDEF01",
                      total_amount=Decimal("240.00"),currency="USD")
PAYMENT=SimpleNamespace(paypal_order_id="PAYPAL-TEST-ORDER-123",
                        capture_id=None)


def approved_get():
    return {
        "id":PAYMENT.paypal_order_id,"status":"APPROVED",
        "purchase_units":[{
            "reference_id":ORDER.po_number,"custom_id":ORDER.id,
            "amount":{"value":"240.00","currency_code":"USD"},
        }],
    }


def captured_response():
    # Modeled after the official PayPal Orders v2 capture example: the
    # original custom_id and purchase-unit amount are absent.
    return {
        "id":PAYMENT.paypal_order_id,"status":"COMPLETED",
        "purchase_units":[{
            "reference_id":ORDER.po_number,
            "payments":{"captures":[{
                "id":"CAPTURE-RESULT-987654321","status":"COMPLETED",
                "amount":{"currency_code":"USD","value":"240.00"},
            }]},
        }],
    }


class CaptureContract(unittest.TestCase):
    def test_approved_order_identity_and_amount_before_capture(self):
        self.assertTrue(_paypal_order_matches(approved_get(),ORDER,PAYMENT))
        missing=approved_get()
        del missing["purchase_units"][0]["custom_id"]
        self.assertFalse(_paypal_order_matches(missing,ORDER,PAYMENT))

    def test_capture_response_accepts_omitted_original_metadata(self):
        capture=_paypal_completed_capture(captured_response(),ORDER,PAYMENT)
        self.assertEqual(capture["id"],"CAPTURE-RESULT-987654321")
        self.assertFalse(_paypal_order_matches(captured_response(),ORDER,PAYMENT))

    def test_completed_get_can_reconcile_without_recapture(self):
        self.assertEqual(_paypal_completed_capture(captured_response(),ORDER,PAYMENT)["status"],"COMPLETED")

    def test_wrong_amount_fails(self):
        result=captured_response()
        result["purchase_units"][0]["payments"]["captures"][0]["amount"]["value"]="239.99"
        self.assertIsNone(_paypal_completed_capture(result,ORDER,PAYMENT))
        self.assertFalse(_paypal_capture_response_noncontradictory(result,ORDER,PAYMENT))

    def test_wrong_currency_fails(self):
        result=captured_response()
        result["purchase_units"][0]["payments"]["captures"][0]["amount"]["currency_code"]="EUR"
        self.assertIsNone(_paypal_completed_capture(result,ORDER,PAYMENT))

    def test_wrong_order_id_fails(self):
        result=captured_response();result["id"]="WRONG-ORDER-123"
        self.assertIsNone(_paypal_completed_capture(result,ORDER,PAYMENT))

    def test_wrong_explicit_custom_id_fails(self):
        result=captured_response()
        result["purchase_units"][0]["custom_id"]="unrelated-po"
        self.assertIsNone(_paypal_completed_capture(result,ORDER,PAYMENT))

    def test_wrong_reference_id_fails(self):
        result=captured_response()
        result["purchase_units"][0]["reference_id"]="WRONG-PO"
        self.assertIsNone(_paypal_completed_capture(result,ORDER,PAYMENT))

    def test_duplicate_capture_fails(self):
        result=captured_response()
        capture=result["purchase_units"][0]["payments"]["captures"][0]
        result["purchase_units"][0]["payments"]["captures"].append(capture.copy())
        self.assertIsNone(_paypal_completed_capture(result,ORDER,PAYMENT))

    def test_nan_capture_fails(self):
        result=captured_response()
        result["purchase_units"][0]["payments"]["captures"][0]["amount"]["value"]="NaN"
        self.assertIsNone(_paypal_completed_capture(result,ORDER,PAYMENT))

    def test_existing_other_capture_id_fails(self):
        result=captured_response()
        payment=SimpleNamespace(paypal_order_id=PAYMENT.paypal_order_id,
                                capture_id="ANOTHER-CAPTURE")
        self.assertIsNone(_paypal_completed_capture(result,ORDER,payment))

    def test_sparse_completed_response_allows_read_only_follow_up(self):
        result=captured_response()
        result["purchase_units"][0]["payments"]={}
        self.assertIsNone(_paypal_completed_capture(result,ORDER,PAYMENT))
        self.assertTrue(_paypal_capture_response_noncontradictory(result,ORDER,PAYMENT))


class CaptureEndpointContract(unittest.TestCase):
    """End-to-end FastAPI endpoints against in-memory SQLite and fake PayPal.

    Never uses a real PayPal credential or any actual hosted data.
    """

    def setUp(self):
        import uuid
        from contextlib import ExitStack
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from app.main import app
        from app.core.database import Base,get_db
        from app.integrations.channel3.client import Channel3Client
        from app.integrations.channel3.schemas import (
            Channel3Offer,Channel3Price,Channel3Product,Channel3SearchResponse
        )

        self.stack=ExitStack()
        self.engine=create_engine(
            'sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        sessions=sessionmaker(bind=self.engine,autoflush=False,autocommit=False)
        def get_test_db():
            db=sessions()
            try: yield db
            finally: db.close()
        app.dependency_overrides[get_db]=get_test_db
        self.addCleanup(self.engine.dispose)
        self.addCleanup(lambda: app.dependency_overrides.clear())

        self.client=self.stack.enter_context(TestClient(app))
        self.addCleanup(self.stack.close)
        self.state={'captures':0,'gets':0,'already_completed':False,
                    'sparse_post':False,'wrong_amount':False,'pending_post':False}
        async def discover(_,query,*,limit=20,filters=None,user_id=None,page_token=None):
            return Channel3SearchResponse(products=[Channel3Product(
                id='test-monitor-1',title='27 inch business monitor',
                offers=[Channel3Offer(
                    url='https://retailer.example/monitor',
                    domain='retailer.example',
                    price=Channel3Price(amount=Decimal('120.00'),currency='USD'),
                    availability='InStock',
                )],
            )])
        self.stack.enter_context(patch.object(Channel3Client,'search_products',discover))
        self.stack.enter_context(patch.object(PayPalClient,'ensure_configured',lambda _:None))
        async def create_paypal(_,**_kwargs):
            return {'id':'FAKE-PAYPAL-ORDER-001','status':'PAYER_ACTION_REQUIRED',
                    'links':[{'rel':'approve','href':'https://www.sandbox.paypal.com/checkoutnow?token=FAKE-PAYPAL-ORDER-001'}]}
        self.stack.enter_context(patch.object(PayPalClient,'create_order',create_paypal))

        async def get_paypal(_,order_id):
            self.state['gets']+=1
            if self.state['already_completed'] or self.state['captures']:
                data={
                    'id':order_id,'status':'COMPLETED',
                    'purchase_units':[{'reference_id':self.order['po_number'],
                                       'payments':{'captures':[{
                                           'id':'FAKE-CAPTURE-001','status':'COMPLETED',
                                           'amount':{'currency_code':'USD','value':'240.00'},
                                       }]}}],
                }
                # Full GET detail is optional for already completed captures.
                return data
            return {
                'id':order_id,'status':'APPROVED',
                'purchase_units':[{
                    'reference_id':self.order['po_number'],'custom_id':self.order['id'],
                    'amount':{'currency_code':'USD','value':'240.00'},
                }],
            }
        async def capture_paypal(_,order_id,key):
            self.state['captures']+=1
            data={
                'id':order_id,'status':'COMPLETED',
                'purchase_units':[{
                    'reference_id':self.order['po_number'],
                    'payments':{'captures':[{
                        'id':'FAKE-CAPTURE-001','status':'COMPLETED',
                        'amount':{
                            'currency_code':'USD',
                            'value':'239.00' if self.state['wrong_amount'] else '240.00',
                        },
                    }]},
                }],
            }
            if self.state['sparse_post']:
                data['purchase_units'][0]['payments']={}
            if self.state['pending_post']:
                data['status']='PENDING'
                data['purchase_units'][0]['payments']['captures'][0]['status']='PENDING'
            return data
        self.stack.enter_context(patch.object(PayPalClient,'get_order',get_paypal))
        self.stack.enter_context(patch.object(PayPalClient,'capture_order',capture_paypal))

        unique=uuid.uuid4().hex[:12]
        registered=self.client.post('/api/v1/auth/register',json={
            'email':'paypal-qa-'+unique+'@example.com',
            'full_name':'Payment QA Fixture',
            'password':'correct-horse-battery-staple',
        })
        self.assertEqual(registered.status_code,201)
        self.headers={'Authorization':'Bearer '+registered.json()['access_token']}
        req=self.client.post('/api/v1/procurement-requests',headers=self.headers,
                             json={'request_text':'Two monitors for new office',
                                   'quantity':2,'budget':'500.00','currency':'USD'})
        self.assertEqual(req.status_code,201)
        request_id=req.json()['id']
        discovered=self.client.post(
            '/api/v1/procurement-requests/'+request_id+'/discover',
            headers=self.headers)
        self.assertEqual(discovered.status_code,200)
        created=self.client.post(
            '/api/v1/procurement-requests/'+request_id+'/purchase-orders',
            headers=self.headers,
            json={'product_id':'test-monitor-1',
                  'offer_url':'https://retailer.example/monitor'})
        self.assertEqual(created.status_code,201)
        self.order=created.json()
        path='/api/v1/purchase-orders/'+self.order['id']
        self.path=path
        self.assertEqual(self.client.post(path+'/submit',headers=self.headers).status_code,200)
        self.assertEqual(self.client.post(path+'/approve',headers=self.headers,
                                          json={'comment':'Test approval'}).status_code,200)
        self.assertEqual(self.client.post(path+'/payments/paypal/create',
                                          headers=self.headers).status_code,200)

    def test_real_api_capture_with_paypal_slim_response(self):
        result=self.client.post(self.path+'/payments/paypal/capture',headers=self.headers)
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json()['status'],'paid')
        self.assertEqual(result.json()['payment']['capture_id'],'FAKE-CAPTURE-001')
        self.assertEqual(self.state['captures'],1)
        repeated=self.client.post(self.path+'/payments/paypal/capture',headers=self.headers)
        self.assertEqual(repeated.status_code,200)
        self.assertEqual(self.state['captures'],1)

    def test_real_api_recover_completed_provider_without_capture(self):
        self.state['already_completed']=True
        result=self.client.post(self.path+'/payments/paypal/capture',headers=self.headers)
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json()['status'],'paid')
        self.assertEqual(self.state['captures'],0)

    def test_real_api_sparse_post_reconciles_via_get(self):
        self.state['sparse_post']=True
        result=self.client.post(self.path+'/payments/paypal/capture',headers=self.headers)
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json()['status'],'paid')
        self.assertEqual(self.state['captures'],1)
        self.assertEqual(self.state['gets'],2)

    def test_real_api_pending_capture_preserves_merchant_binding(self):
        self.state['pending_post']=True
        result=self.client.post(self.path+'/payments/paypal/capture',headers=self.headers)
        self.assertEqual(result.status_code,409)
        data=self.client.get(self.path,headers=self.headers).json()
        self.assertEqual(data['status'],'payment_pending')
        self.assertEqual(data['payment']['status'],'pending')
        self.assertTrue(data['payment']['checkout_merchant_current'])
        self.assertIsNone(data['payment']['capture_id'])

    def test_real_api_mismatched_capture_amount_keeps_unpaid(self):
        self.state['wrong_amount']=True
        result=self.client.post(self.path+'/payments/paypal/capture',headers=self.headers)
        self.assertEqual(result.status_code,502)
        saved=self.client.get(self.path,headers=self.headers).json()
        self.assertEqual(saved['status'],'payment_pending')
        self.assertIsNone(saved['payment']['capture_id'])


def run() -> int:
    suite=unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromTestCase(CaptureContract),
        unittest.defaultTestLoader.loadTestsFromTestCase(CaptureEndpointContract),
    ])
    result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    if not result.wasSuccessful():
        # Tests contain only hardcoded synthetic values. Even so, print only
        # testcase method names and do not print exception traces/credentials.
        for case,_ in result.failures+result.errors:
            print("[paypal-capture] FAIL "+case._testMethodName)
        return 1
    print("[paypal-capture] PASS "+str(result.testsRun)+" no-network contract tests")
    return 0


if __name__=="__main__":
    raise SystemExit(run())
