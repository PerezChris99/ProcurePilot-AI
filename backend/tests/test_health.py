def test_health_endpoint_returns_ok(client):
    response=client.get('/api/v1/health')
    assert response.status_code==200
    assert response.json()=={'status':'ok','service':'procurepilot-api'}

def test_root_endpoint_returns_service_name(client):
    response=client.get('/')
    assert response.status_code==200
    assert response.json()['name']=='ProcurePilot AI'


def test_ready_endpoint_checks_database_schema(client):
    response = client.get('/api/v1/ready')
    assert response.status_code == 200
    assert response.json() == {'status':'ready', 'service':'procurepilot-api'}


def test_ready_endpoint_fails_closed_when_db_or_migration_is_unavailable(client):
    from sqlalchemy.exc import SQLAlchemyError
    from app.main import app
    from app.core.database import get_db

    class BrokenDatabase:
        def scalar(self, statement):
            raise SQLAlchemyError('connection dropped')

    def fail_get_db():
        yield BrokenDatabase()

    old_override = app.dependency_overrides[get_db]
    app.dependency_overrides[get_db] = fail_get_db
    try:
        result = client.get('/api/v1/ready')
        assert result.status_code == 503
        assert result.json()['detail'] == 'Database or required schema is unavailable'
        # Process liveness remains healthy for restarts and diagnostics.
        assert client.get('/api/v1/health').status_code == 200
    finally:
        app.dependency_overrides[get_db] = old_override
