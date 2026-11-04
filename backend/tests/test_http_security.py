from app.main import app

def test_api_security_headers_and_no_store_on_authenticated_and_public(client):
    for path in ('/api/v1/health', '/api/v1/auth/me'):
        response=client.get(path)
        assert response.headers['x-content-type-options']=='nosniff'
        assert response.headers['x-frame-options']=='DENY'
        assert response.headers['referrer-policy']=='no-referrer'
        assert response.headers['cache-control']=='no-store'
        assert 'frame-ancestors' in response.headers['content-security-policy']
        assert 'geolocation=()' in response.headers['permissions-policy']

def test_cors_preflight_keeps_required_headers(client):
    response=client.options('/api/v1/auth/login',headers={
        'Origin':'http://localhost:5173','Access-Control-Request-Method':'POST',
        'Access-Control-Request-Headers':'content-type',
    })
    assert response.status_code==200
    assert response.headers['access-control-allow-origin']=='http://localhost:5173'
    assert response.headers['x-content-type-options']=='nosniff'

def test_oversized_content_length_rejected_before_body_parsing(client):
    response=client.post('/api/v1/auth/login',
        headers={'Content-Length':'999999999'},
        content=b'{}')
    assert response.status_code==413
    assert 'size limit' in response.json()['detail']
    assert response.headers['cache-control']=='no-store'

def test_small_body_still_reaches_validation(client):
    response=client.post('/api/v1/auth/login',json={'email':'invalid','password':'hi'})
    assert response.status_code==422
