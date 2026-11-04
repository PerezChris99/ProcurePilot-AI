"""Proof that list endpoints avoid unbounded catalogue/audit payloads."""
from app.integrations.channel3.client import Channel3Client
from app.integrations.channel3.schemas import Channel3Product, Channel3SearchResponse


def _auth(client,email='pagination@example.com'):
    res=client.post('/api/v1/auth/register',json={
        'email':email,'full_name':'Read Path Test',
        'password':'correct-horse-battery-staple',
    })
    assert res.status_code==201
    return {'Authorization':'Bearer '+res.json()['access_token']}


def test_procurement_list_returns_lean_records_but_detail_retains_evidence(client,monkeypatch):
    headers=_auth(client)
    created=client.post('/api/v1/procurement-requests',headers=headers,json={
        'request_text':'Find laboratory monitors for office testing',
        'currency':'USD',
    })
    request_id=created.json()['id']
    async def search(self,query,*,limit=20,filters=None,user_id=None,page_token=None):
        return Channel3SearchResponse(products=[Channel3Product(id='monitor-one',title='Monitor')])
    monkeypatch.setattr(Channel3Client,'search_products',search)
    assert client.post(f'/api/v1/procurement-requests/{request_id}/discover',headers=headers).status_code==200
    lightweight=client.get('/api/v1/procurement-requests',headers=headers).json()[0]
    assert lightweight['id']==request_id
    assert lightweight['analysis_json'] is None
    full=client.get(f'/api/v1/procurement-requests/{request_id}',headers=headers).json()
    assert full['analysis_json']['results'][0]['product']['id']=='monitor-one'
    legacy=client.get('/api/v1/procurement-requests?include_analysis=true',headers=headers).json()
    assert legacy[0]['analysis_json']['results']


def test_older_procurement_records_are_reachable_by_stable_keyset(client):
    headers=_auth(client,'pagination-cursor@example.com')
    ids=[]
    for i in range(3):
        record=client.post('/api/v1/procurement-requests',headers=headers,json={
            'request_text':f'Find equipment for department number {i}',
        })
        assert record.status_code==201
        ids.append(record.json()['id'])
    first=client.get('/api/v1/procurement-requests?limit=1',headers=headers).json()
    assert len(first)==1
    cursor=first[0]
    older=client.get('/api/v1/procurement-requests',headers=headers,params={
        'limit':1,'before_created_at':cursor['created_at'],'before_id':cursor['id'],
    })
    assert older.status_code==200
    assert len(older.json())==1
    assert older.json()[0]['id']!=cursor['id']
    assert client.get('/api/v1/procurement-requests?before_id=abc',headers=headers).status_code==422
