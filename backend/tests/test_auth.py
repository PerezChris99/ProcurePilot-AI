def register(client,email='buyer@example.com',password='correct-horse-battery-staple'):
    return client.post('/api/v1/auth/register',json={'email':email,'full_name':'Procurement Buyer','password':password})

def test_register_login_and_get_current_user(client):
    created=register(client)
    assert created.status_code==201
    token=created.json()['access_token']
    assert created.json()['user']['email']=='buyer@example.com'
    me=client.get('/api/v1/auth/me',headers={'Authorization':'Bearer '+token})
    assert me.status_code==200
    assert me.json()['full_name']=='Procurement Buyer'
    logged_in=client.post('/api/v1/auth/login',json={'email':'buyer@example.com','password':'correct-horse-battery-staple'})
    assert logged_in.status_code==200

def test_duplicate_email_is_rejected(client):
    assert register(client).status_code==201
    assert register(client).status_code==409

def test_invalid_password_does_not_authenticate(client):
    register(client)
    response=client.post('/api/v1/auth/login',json={'email':'buyer@example.com','password':'wrong-password'})
    assert response.status_code==401

def test_me_requires_bearer_token(client):
    assert client.get('/api/v1/auth/me').status_code==401
