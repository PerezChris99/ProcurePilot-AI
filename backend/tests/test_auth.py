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


def test_registration_returns_sanitized_503_when_database_lookup_fails(client):
    from sqlalchemy.exc import OperationalError
    from app.main import app
    from app.core.database import get_db

    class DisconnectedSession:
        def scalar(self, statement):
            raise OperationalError("SELECT users", {}, Exception("password=private"))

    def broken_db():
        yield DisconnectedSession()

    app.dependency_overrides[get_db] = broken_db
    try:
        response = register(client, email='disconnected@example.com')
        assert response.status_code == 503
        assert response.headers['retry-after'] == '15'
        assert response.json()['detail'] == (
            'Authentication database is temporarily unavailable. Please try again later.'
        )
        assert 'private' not in response.text
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_login_returns_503_not_bad_credentials_when_database_fails(client):
    from sqlalchemy.exc import OperationalError
    from app.main import app
    from app.core.database import get_db

    class DisconnectedSession:
        def scalar(self, statement):
            raise OperationalError("SELECT users", {}, Exception("database unavailable"))

    def broken_db():
        yield DisconnectedSession()

    app.dependency_overrides[get_db] = broken_db
    try:
        response = client.post('/api/v1/auth/login', json={
            'email': 'buyer@example.com',
            'password': 'correct-horse-battery-staple',
        })
        assert response.status_code == 503
        assert 'database unavailable' not in response.text
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_registration_rolls_back_and_returns_503_on_failed_database_commit(client):
    from sqlalchemy.exc import OperationalError
    from app.main import app
    from app.core.database import get_db

    class WriteUnavailableSession:
        rolled_back = False

        def scalar(self, statement):
            return None

        def add(self, user):
            pass

        def flush(self):
            raise OperationalError("INSERT users", {}, Exception("secret database URI"))

        def commit(self):
            raise OperationalError("COMMIT users", {}, Exception("secret database URI"))

        def rollback(self):
            self.rolled_back = True

    broken = WriteUnavailableSession()

    def broken_db():
        yield broken

    app.dependency_overrides[get_db] = broken_db
    try:
        response = register(client, email='write-failed@example.com')
        assert response.status_code == 503
        assert broken.rolled_back is True
        assert 'secret database URI' not in response.text
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_registration_materializes_user_without_post_commit_refresh(client, monkeypatch):
    """Response contract does not depend on a second SELECT after INSERT/COMMIT."""
    from datetime import datetime
    from app.api import auth as auth_api
    from app.main import app
    from app.core.database import get_db
    from app.schemas.auth import UserResponse

    class EmulatedUserWrite:
        refresh_called = False
        rolled_back = False
        added = None

        def scalar(self, _query):
            return None

        def add(self, item):
            self.added = item

        def flush(self):
            self.added.id = '12345678-1234-4123-8123-123456789abc'
            self.added.created_at = datetime(2026, 11, 8, 12, 0, 0)
            self.added.is_active = True

        def commit(self):
            pass

        def refresh(self, _obj):
            self.refresh_called = True
            raise AssertionError('no post-commit SELECT allowed')

        def rollback(self):
            self.rolled_back = True

    write = EmulatedUserWrite()
    def override():
        yield write

    old = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override
    try:
        response = register(client, email='quick-registration@example.com')
        assert response.status_code == 201
        payload = response.json()
        assert payload['user']['id'] == '12345678-1234-4123-8123-123456789abc'
        assert payload['user']['email'] == 'quick-registration@example.com'
        assert write.refresh_called is False
        assert write.rolled_back is False
    finally:
        if old is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = old
