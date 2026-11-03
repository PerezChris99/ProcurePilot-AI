def test_health_endpoint_returns_ok(client):
    response=client.get('/api/v1/health')
    assert response.status_code==200
    assert response.json()=={'status':'ok','service':'procurepilot-api'}

def test_root_endpoint_returns_service_name(client):
    response=client.get('/')
    assert response.status_code==200
    assert response.json()['name']=='ProcurePilot AI'
