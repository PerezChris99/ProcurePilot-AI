from decimal import Decimal
from app.integrations.channel3.schemas import Channel3Product,Channel3Offer,Channel3Price,Channel3SearchResponse
from app.integrations.channel3.client import Channel3Client
from app.agents import runtime

def auth_headers(client,email):
    response=client.post('/api/v1/auth/register',json={'email':email,'full_name':'Procurement User','password':'correct-horse-battery-staple'})
    return {'Authorization':'Bearer '+response.json()['access_token']}

def test_request_is_persisted_and_scoped_to_authenticated_user(client):
    headers=auth_headers(client,'owner@example.com')
    created=client.post('/api/v1/procurement-requests',headers=headers,json={'request_text':'20 monitors with 27 inch displays','quantity':20,'budget':'5000.00','currency':'USD'})
    assert created.status_code==201
    request_id=created.json()['id']
    assert created.json()['status']=='draft'
    assert client.get('/api/v1/procurement-requests',headers=headers).json()[0]['id']==request_id
    other_headers=auth_headers(client,'other@example.com')
    assert client.get('/api/v1/procurement-requests/'+request_id,headers=other_headers).status_code==404

def test_discovery_uses_channel3_and_persists_ranked_snapshot(client,monkeypatch):
    headers=auth_headers(client,'discovery@example.com')
    created=client.post('/api/v1/procurement-requests',headers=headers,json={'request_text':'Business monitor 27 inch','quantity':2,'budget':'500.00','currency':'USD'})
    request_id=created.json()['id']
    async def fake_search(self,query,*,limit=20,filters=None,user_id=None,page_token=None):
        assert user_id is not None
        return Channel3SearchResponse(products=[Channel3Product(id='monitor-1',title='Business monitor',offers=[Channel3Offer(url='https://shop.example/monitor',domain='shop.example',price=Channel3Price(amount=Decimal('120'),currency='USD'),availability='InStock')])])
    monkeypatch.setattr(Channel3Client,'search_products',fake_search)
    response=client.post('/api/v1/procurement-requests/'+request_id+'/discover',headers=headers)
    assert response.status_code==200
    assert response.json()['source']=='Channel3'
    assert response.json()['results'][0]['ranking']['product_id']=='monitor-1'
    saved=client.get('/api/v1/procurement-requests/'+request_id,headers=headers).json()
    assert saved['status']=='products_discovered'
    assert saved['analysis_json']['results'][0]['product']['id']=='monitor-1'

def test_discovery_pagination_merges_products_and_uses_saved_token(client,monkeypatch):
    headers=auth_headers(client,'pages@example.com')
    created=client.post('/api/v1/procurement-requests',headers=headers,json={'request_text':'Find business monitors','quantity':1,'currency':'USD'})
    request_id=created.json()['id']
    calls=[]
    async def fake_search(self,query,*,limit=20,filters=None,user_id=None,page_token=None):
        calls.append(page_token)
        product_id='monitor-page-1' if page_token is None else 'monitor-page-2'
        token='next-page' if page_token is None else None
        return Channel3SearchResponse(products=[Channel3Product(id=product_id,title=product_id)],next_page_token=token)
    monkeypatch.setattr(Channel3Client,'search_products',fake_search)
    first=client.post('/api/v1/procurement-requests/'+request_id+'/discover',headers=headers)
    assert first.json()['next_page_available'] is True
    second=client.post('/api/v1/procurement-requests/'+request_id+'/discover?next_page=true',headers=headers)
    assert second.status_code==200
    assert calls==[None,'next-page']
    assert {item['product']['id'] for item in second.json()['results']}=={'monitor-page-1','monitor-page-2'}
    assert second.json()['next_page_available'] is False

def test_agent_analysis_is_user_scoped_and_persisted(client,monkeypatch):
    headers=auth_headers(client,'agent-owner@example.com')
    created=client.post('/api/v1/procurement-requests',headers=headers,json={'request_text':'Find 10 office chairs','quantity':10,'currency':'USD'})
    request_id=created.json()['id']
    async def fake_agent(user_id,prompt):
        assert user_id
        assert '10 office chairs' in prompt
        return 'Three catalogue options were reviewed; delivery is unverified.'
    monkeypatch.setattr(runtime,'run_procurement_agent',fake_agent)
    response=client.post('/api/v1/procurement-requests/'+request_id+'/analyze',headers=headers)
    assert response.status_code==200
    assert response.json()['explanation'].startswith('Three catalogue options')
    assert client.get('/api/v1/procurement-requests/'+request_id,headers=headers).json()['analysis_json']['ai_explanation']==response.json()['explanation']
