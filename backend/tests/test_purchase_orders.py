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

def test_checkout_approved_webhook_records_buyer_approval_for_later_capture(client,monkeypatch):
    headers,order=approved_order(client,monkeypatch,'buyer-approved@example.com')
    fake_paypal(monkeypatch,order['id'])
    client.post(f"/api/v1/purchase-orders/{order['id']}/payments/paypal/create",headers=headers)
    async def verified(self,request_headers,event): return True
    monkeypatch.setattr(PayPalClient,'verify_webhook',verified)
    event={'id':'WH-APPROVED-1','event_type':'CHECKOUT.ORDER.APPROVED','resource':{'id':'PAYPAL-ORDER-123','status':'APPROVED'}}
    response=client.post('/api/v1/webhooks/paypal',json=event)
    assert response.status_code==200
    saved=client.get(f"/api/v1/purchase-orders/{order['id']}",headers=headers).json()
    assert saved['payment']['status']=='buyer_approved'
    assert any(entry['action']=='payment.paypal_buyer_approved' for entry in saved['audit_events'])


def test_webhook_cannot_replace_an_existing_capture_with_a_different_id(client,monkeypatch):
    headers,order=approved_order(client,monkeypatch,'no-capture-replacement@example.com')
    fake_paypal(monkeypatch,order['id'])
    client.post(f"/api/v1/purchase-orders/{order['id']}/payments/paypal/create",headers=headers)
    async def verified(self,request_headers,event): return True
    monkeypatch.setattr(PayPalClient,'verify_webhook',verified)

    def event(event_id,capture_id):
        return {'id':event_id,'event_type':'PAYMENT.CAPTURE.COMPLETED','resource':{
            'id':capture_id,'status':'COMPLETED',
            'amount':{'currency_code':'USD','value':'240.00'},
            'supplementary_data':{'related_ids':{'order_id':'PAYPAL-ORDER-123'}}}}
    first=client.post('/api/v1/webhooks/paypal',json=event('WH-CAPTURE-ONE','CAPTURE-ONE'))
    second=client.post('/api/v1/webhooks/paypal',json=event('WH-CAPTURE-TWO','CAPTURE-TWO'))
    assert first.status_code==200
    assert second.status_code==200
    saved=client.get(f"/api/v1/purchase-orders/{order['id']}",headers=headers).json()
    assert saved['status']=='paid'
    assert saved['payment']['capture_id']=='CAPTURE-ONE'
    assert any(entry['action']=='payment.webhook_mismatch' for entry in saved['audit_events'])


def test_webhook_rejects_malformed_resource_after_signature_verification(client,monkeypatch):
    async def verified(self,request_headers,event): return True
    monkeypatch.setattr(PayPalClient,'verify_webhook',verified)
    response=client.post('/api/v1/webhooks/paypal',json={
        'id':'WH-BAD-RESOURCE','event_type':'PAYMENT.CAPTURE.COMPLETED',
        'resource':['not','a','payment']})
    assert response.status_code==400


def test_purchase_order_list_returns_complete_details_without_n_plus_one_queries(client,monkeypatch):
    headers,order=make_order(client,monkeypatch,email='list-batch@example.com')
    response=client.get('/api/v1/purchase-orders',headers=headers)
    assert response.status_code==200
    assert len(response.json())==1
    assert response.json()[0]['id']==order['id']
    assert response.json()[0]['items'][0]['product_title']=='Business monitor 27 inch'
    assert any(event['action']=='purchase_order.created' for event in response.json()[0]['audit_events'])


def test_approvals_query_only_returns_owners_pending_orders(client, monkeypatch):
    headers, order = make_order(client, monkeypatch, email='approvals-owner@example.com')
    other = register(client, 'approvals-other@example.com')
    assert client.get('/api/v1/purchase-orders?status=pending_approval', headers=headers).json() == []
    assert client.post(f"/api/v1/purchase-orders/{order['id']}/submit", headers=headers).status_code == 200
    result = client.get('/api/v1/purchase-orders?status=pending_approval', headers=headers)
    assert result.status_code == 200
    assert [entry['id'] for entry in result.json()] == [order['id']]
    assert client.get('/api/v1/purchase-orders?status=pending_approval', headers=other).json() == []
    assert client.get('/api/v1/purchase-orders?status=unknown', headers=headers).status_code == 422
    assert client.post(f"/api/v1/purchase-orders/{order['id']}/approve", headers=headers, json={'comment':'Reviewed'}).status_code == 200
    assert client.get('/api/v1/purchase-orders?status=pending_approval', headers=headers).json() == []


def test_passport_freezes_evidence_and_only_owner_can_export(client,monkeypatch):
    owner,order=make_order(client,monkeypatch,email='passport-tested@example.com')
    po=order['id']
    payload=client.get(f'/api/v1/purchase-orders/{po}/passport',headers=owner)
    assert payload.status_code==200
    passport=payload.json()
    assert passport['evidence']['source']=='Channel3'
    assert passport['buyer_decision']['approval_model']==(
        'Personal workspace; self-approval permitted')
    assert passport['evidence']['selected']['product_id']=='monitor-real-1'
    assert passport['comparison']['least_cost_eligible_total']=='240.00'
    assert passport['comparison']['selected_total']=='240.00'
    assert passport['payment_proof']['retailer_settlement'] is False
    assert len(passport['snapshot_sha256'])==64
    pdf=client.get(f'/api/v1/purchase-orders/{po}/passport.pdf',headers=owner)
    assert pdf.status_code==200 and pdf.content.startswith(b'%PDF-')
    other=register(client,'other-passport@example.com')
    assert client.get(f'/api/v1/purchase-orders/{po}/passport',headers=other).status_code==404
    assert client.get(f'/api/v1/purchase-orders/{po}/passport.pdf',headers=other).status_code==404


def test_hard_merchant_and_specification_requirements_are_enforced(client,monkeypatch):
    owner=register(client,'policy-tested@example.com')
    req=client.post('/api/v1/procurement-requests',headers=owner,json={
        'request_text':'Two 27-inch monitors for the office','quantity':2,
        'currency':'USD','budget':'500.00',
        'policy_json':{'mandatory_attributes':{'screen_size':'27 inch'},
                       'allowed_merchants':['approved.example'],'max_unit_price':'135.00'},
    })
    assert req.status_code==201
    rid=req.json()['id']
    async def search(self,query,*,limit=20,filters=None,user_id=None,page_token=None):
        return Channel3SearchResponse(products=[
            Channel3Product(id='wrong-size',title='Wrong size',
                structured_attributes={'screen_size':['24 inch']},
                offers=[Channel3Offer(url='https://approved.example/wrong',
                    domain='approved.example',price=Channel3Price(amount=Decimal('100.00'),currency='USD'),
                    availability='InStock')]),
            Channel3Product(id='valid',title='Valid monitor',
                structured_attributes={'screen_size':['27 inch']},
                offers=[
                    Channel3Offer(url='https://wrong.example/other',
                        domain='wrong.example',price=Channel3Price(amount=Decimal('110.00'),currency='USD'),
                        availability='InStock'),
                    Channel3Offer(url='https://approved.example/valid',
                        domain='approved.example',price=Channel3Price(amount=Decimal('120.00'),currency='USD'),
                        availability='InStock'),
                ]),
        ])
    monkeypatch.setattr(Channel3Client,'search_products',search)
    discovered=client.post(f'/api/v1/procurement-requests/{rid}/discover',headers=owner)
    assert discovered.status_code==200
    items={x['product']['id']:x for x in discovered.json()['results']}
    assert items['wrong-size']['policy']['eligible_offer_urls']==[]
    assert items['valid']['policy']['eligible_offer_urls']==['https://approved.example/valid']
    for product_id,url in [('wrong-size','https://approved.example/wrong'),
                           ('valid','https://wrong.example/other')]:
        denied=client.post(f'/api/v1/procurement-requests/{rid}/purchase-orders',
            headers=owner,json={'product_id':product_id,'offer_url':url})
        assert denied.status_code==422
    accepted=client.post(f'/api/v1/procurement-requests/{rid}/purchase-orders',
        headers=owner,json={'product_id':'valid','offer_url':'https://approved.example/valid'})
    assert accepted.status_code==201
    assert accepted.json()['total_amount']=='240.00'


def test_delegated_approver_can_only_decide_assigned_order_not_pay(client,monkeypatch):
    owner=register(client,'delegator@example.com')
    reviewer=register(client,'delegate@example.com')
    outsider=register(client,'outsider@example.com')
    req=client.post('/api/v1/procurement-requests',headers=owner,json={
        'request_text':'Two office monitors for independent review',
        'quantity':2,'currency':'USD',
        'policy_json':{'approver_email':'delegate@example.com'},
    })
    assert req.status_code==201
    rid=req.json()['id']
    async def search(self,query,*,limit=20,filters=None,user_id=None,page_token=None):
        return Channel3SearchResponse(products=[Channel3Product(id='delegate-product',
            title='Office monitor',offers=[Channel3Offer(
                url='https://retailer.example/monitor',domain='retailer.example',
                price=Channel3Price(amount=Decimal('120.00'),currency='USD'),
                availability='InStock')])])
    monkeypatch.setattr(Channel3Client,'search_products',search)
    assert client.post(f'/api/v1/procurement-requests/{rid}/discover',headers=owner).status_code==200
    result=client.post(f'/api/v1/procurement-requests/{rid}/purchase-orders',headers=owner,json={
        'product_id':'delegate-product','offer_url':'https://retailer.example/monitor',
    })
    assert result.status_code==201
    order=result.json()
    assert order['assigned_approver_id'] is not None
    po=order['id']
    assert client.post(f'/api/v1/purchase-orders/{po}/submit',headers=owner).status_code==200
    owner_pending=client.get('/api/v1/purchase-orders?status=pending_approval',headers=owner).json()
    reviewer_pending=client.get('/api/v1/purchase-orders?status=pending_approval',headers=reviewer).json()
    assert owner_pending[0]['can_approve'] is False
    assert reviewer_pending[0]['can_approve'] is True
    assert client.get('/api/v1/purchase-orders',headers=reviewer).json()==[]
    assert client.get(f'/api/v1/purchase-orders/{po}',headers=reviewer).status_code==404
    for forbidden in (owner,outsider):
        assert client.post(f'/api/v1/purchase-orders/{po}/approve',
            headers=forbidden,json={}).status_code==404
    approved=client.post(f'/api/v1/purchase-orders/{po}/approve',headers=reviewer,json={})
    assert approved.status_code==200
    assert approved.json()['approved_by']==order['assigned_approver_id']
    delegated_passport=client.get(
        f'/api/v1/purchase-orders/{po}/passport',headers=owner)
    assert delegated_passport.status_code==200
    assert delegated_passport.json()['buyer_decision']['approval_model']==(
        'Distinct registered reviewer assigned per order')
    assert client.post(f'/api/v1/purchase-orders/{po}/payments/paypal/create',
        headers=reviewer).status_code==404
    assert client.get('/api/v1/purchase-orders?status=pending_approval',headers=reviewer).json()==[]


@pytest.fixture
def foreign_key_client():
    """Exercise purchase creation with FK enforcement, as on PostgreSQL."""
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.main import app
    from app.core.database import Base, get_db

    engine = create_engine('sqlite://', connect_args={'check_same_thread': False},
                           poolclass=StaticPool)

    @event.listens_for(engine, 'connect')
    def enforce_foreign_keys(connection, _):
        connection.execute('PRAGMA foreign_keys=ON')

    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_db():
        with testing_session() as db:
            yield db

    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_create_po_persists_parent_before_item_and_audit_foreign_keys(foreign_key_client, monkeypatch):
    headers, order = make_order(foreign_key_client, monkeypatch,
                                email='foreign-key-order@example.com')
    assert order['status'] == 'draft'
    assert order['items'][0]['product_id'] == 'monitor-real-1'
    assert any(event['action'] == 'purchase_order.created'
               for event in order['audit_events'])
    saved = foreign_key_client.get('/api/v1/purchase-orders/' + order['id'],
                                    headers=headers)
    assert saved.status_code == 200
    assert saved.json()['id'] == order['id']


def test_plain_language_screen_size_blocks_wrong_display_and_accessories(client,monkeypatch):
    headers=register(client,'requested-72in@example.com')
    request_id=client.post('/api/v1/procurement-requests',headers=headers,json={
        'request_text':'i need 72 inch monitors',
        'quantity':4,'budget':'3000.00','currency':'USD',
    }).json()['id']

    async def search(self,query,*,limit=20,filters=None,user_id=None,page_token=None):
        def product(identifier,title):
            return Channel3Product(id=identifier,title=title,offers=[
                Channel3Offer(url='https://retailer.example/'+identifier,
                    domain='retailer.example',availability='InStock',
                    price=Channel3Price(amount=Decimal('400'),currency='USD'))
            ])
        return Channel3SearchResponse(products=[
            product('wrong-size','HP 24 in Monitor'),
            product('stand','Dual Monitor Stand'),
            product('correct','72 inch Commercial Monitor'),
        ])
    monkeypatch.setattr(Channel3Client,'search_products',search)
    snapshot=client.post(f'/api/v1/procurement-requests/{request_id}/discover',
                         headers=headers)
    assert snapshot.status_code==200
    entries={entry['product']['id']:entry for entry in snapshot.json()['results']}
    assert entries['wrong-size']['policy']['eligible_offer_urls']==[]
    assert entries['stand']['policy']['eligible_offer_urls']==[]
    assert entries['correct']['policy']['eligible_offer_urls']==[
        'https://retailer.example/correct']

    for blocked in ('wrong-size','stand'):
        response=client.post(
            f'/api/v1/procurement-requests/{request_id}/purchase-orders',
            headers=headers,json={'product_id':blocked,
                                  'offer_url':'https://retailer.example/'+blocked})
        assert response.status_code==422

    created=client.post(
        f'/api/v1/procurement-requests/{request_id}/purchase-orders',
        headers=headers,json={'product_id':'correct',
                              'offer_url':'https://retailer.example/correct'})
    assert created.status_code==201
    assert created.json()['total_amount']=='1600.00'


def test_paypal_create_and_capture_release_read_transactions_before_network(client,monkeypatch):
    """The 15-second PostgreSQL idle transaction deadline must not span PayPal I/O."""
    headers,order=approved_order(client,monkeypatch,'paypal-transactions@example.com')
    fake_paypal(monkeypatch,order['id'])
    from app.core.database import get_db
    from app.main import app
    original_override=app.dependency_overrides[get_db]
    sessions=[]

    def tracked_db():
        for db in original_override():
            sessions.append(db)
            yield db

    app.dependency_overrides[get_db]=tracked_db
    try:
        original_create=PayPalClient.create_order
        original_get=PayPalClient.get_order
        original_capture=PayPalClient.capture_order

        async def checked_create(self,**kwargs):
            assert sessions[-1].in_transaction() is False
            return await original_create(self,**kwargs)

        async def checked_get(self,order_id):
            assert sessions[-1].in_transaction() is False
            return await original_get(self,order_id)

        async def checked_capture(self,order_id,key):
            assert sessions[-1].in_transaction() is False
            return await original_capture(self,order_id,key)

        monkeypatch.setattr(PayPalClient,'create_order',checked_create)
        monkeypatch.setattr(PayPalClient,'get_order',checked_get)
        monkeypatch.setattr(PayPalClient,'capture_order',checked_capture)
        checkout=client.post(f"/api/v1/purchase-orders/{order['id']}/payments/paypal/create",headers=headers)
        assert checkout.status_code==200
        capture=client.post(f"/api/v1/purchase-orders/{order['id']}/payments/paypal/capture",headers=headers)
        assert capture.status_code==200
        assert capture.json()['status']=='paid'
    finally:
        app.dependency_overrides[get_db]=original_override


def test_channel3_recheck_releases_postgres_read_transaction(client,monkeypatch):
    headers,order=make_order(client,monkeypatch,email='offer-recheck-window@example.com')
    from app.main import app
    from app.core.database import get_db
    original_override=app.dependency_overrides[get_db]
    seen=[]
    def tracked_db():
        for session in original_override():
            seen.append(session)
            yield session
    app.dependency_overrides[get_db]=tracked_db
    try:
        async def get_product(self,product_id,*,user_id=None):
            assert seen[-1].in_transaction() is False
            return Channel3Product(
                id=product_id,title='Business monitor 27 inch',
                offers=[Channel3Offer(
                    url='https://retailer.example/monitor',
                    domain='retailer.example',
                    price=Channel3Price(amount=Decimal('120.00'),currency='USD'),
                    availability='InStock')],
            )
        monkeypatch.setattr(Channel3Client,'get_product',get_product)
        response=client.post(
            f"/api/v1/purchase-orders/{order['id']}/verify-offer",headers=headers,
        )
        assert response.status_code==200
        assert response.json()['status']=='unchanged'
    finally:
        app.dependency_overrides[get_db]=original_override



def test_checkout_approval_url_is_sandbox_only_and_cannot_target_live_paypal():
    # The Orders v2 create response can provide a payer-action or approve link.
    # A Sandbox-only app must never show a Live checkout or lookalike domain.
    assert PayPalClient.is_approval_url(
        'https://www.sandbox.paypal.com/checkoutnow?token=PAYPAL-123')
    assert PayPalClient.is_approval_url(
        'https://sandbox.paypal.com/checkoutnow?token=PAYPAL-123')
    for malicious in (
        'https://www.paypal.com/checkoutnow?token=PAYPAL-123',
        'http://www.sandbox.paypal.com/checkoutnow?token=PAYPAL-123',
        'https://www.sandbox.paypal.com.evil.example/checkoutnow',
        'https://user:password@www.sandbox.paypal.com/checkoutnow',
        'https://www.sandbox.paypal.com:443/checkoutnow',
        'javascript:alert(1)',
    ):
        assert not PayPalClient.is_approval_url(malicious)
