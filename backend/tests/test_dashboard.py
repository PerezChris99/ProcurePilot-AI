from app.integrations.channel3.client import Channel3Client
from app.integrations.channel3.schemas import Channel3Offer, Channel3Price, Channel3Product, Channel3SearchResponse


def register(client, email):
    response = client.post('/api/v1/auth/register', json={
        'email': email, 'full_name': 'Dashboard User',
        'password': 'correct-horse-battery-staple',
    })
    assert response.status_code == 201
    return {'Authorization': 'Bearer ' + response.json()['access_token']}


def test_dashboard_is_authenticated_and_isolated(client, monkeypatch):
    assert client.get('/api/v1/dashboard/summary').status_code == 401
    first = register(client, 'dashboard-first@example.com')
    second = register(client, 'dashboard-second@example.com')
    created = client.post('/api/v1/procurement-requests', headers=first, json={
        'request_text': 'Office laptop stands for employees', 'quantity': 1, 'currency': 'USD'
    })
    assert created.status_code == 201
    request_id = created.json()['id']

    async def search(self, query, *, limit=20, filters=None, user_id=None, page_token=None):
        return Channel3SearchResponse(products=[
            Channel3Product(id='stand-1', title='Laptop stand', offers=[
                Channel3Offer(url='https://retailer.example/stand', domain='retailer.example',
                              price=Channel3Price(amount='40.00', currency='USD'), availability='InStock')
            ])
        ])
    monkeypatch.setattr(Channel3Client, 'search_products', search)
    assert client.post(f'/api/v1/procurement-requests/{request_id}/discover', headers=first).status_code == 200
    order = client.post(f'/api/v1/procurement-requests/{request_id}/purchase-orders',
        headers=first, json={'product_id': 'stand-1', 'offer_url': 'https://retailer.example/stand'})
    assert order.status_code == 201
    assert client.post(f"/api/v1/purchase-orders/{order.json()['id']}/submit",headers=first).status_code == 200
    summary = client.get('/api/v1/dashboard/summary', headers=first).json()
    assert summary['completed_orders'] == 0
    assert summary['active_orders'] == 1
    assert summary['pending_approvals'] == 1
    assert summary['requests_with_results'] == 1
    assert summary['recent_activity']
    other = client.get('/api/v1/dashboard/summary', headers=second).json()
    assert other == {'completed_orders': 0, 'active_orders': 0, 'pending_approvals': 0,
                     'requests_with_results': 0, 'recent_activity': []}
