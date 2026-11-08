"""Production/preview Vercel Services database gate.

Called during the *backend service build*, not on request import. Verifies that
the Vercel environment points at the expected Neon project and that required
Alembic tables exist. Forward migrations require an explicit one-shot flag.
Never prints DSNs, query text, SQL exception messages, or credentials.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool

BACKEND = Path(__file__).resolve().parents[1]
REQUIRED = frozenset((
    'alembic_version', 'users', 'procurement_requests', 'purchase_orders',
    'purchase_order_items', 'approvals', 'payments', 'webhook_events',
    'audit_events', 'ai_daily_budgets', 'auth_rate_limit_counters',
))
KNOWN_REVISIONS = frozenset((
    '0001_users', '0002_requests', '0003_orders', '0004_ai_budget',
    '0005_read_indexes', '0006_purchase_policy', '0007_decision_evidence',
    '0008_offer_verification', '0009_delegated_approver',
    '0010_auth_throttles',
))
HEAD = '0010_auth_throttles'
# Distinct, public-safe exit codes make Vercel deployment state useful even
# when build log access is restricted. Never encode an actual URL or exception.
FAILURE_CODES = {
    'unexpected_vercel_environment': 20,
    'database_url_absent': 21,
    'database_target_mismatch': 22,
    'database_url_malformed': 23,
    'neon_connection_failed': 24,
    'alembic_upgrade_failed': 25,
    'post_migration_db_connect_failed': 26,
    'alembic_revision_outdated': 27,
    'required_tables_missing': 28,
    'unknown_alembic_revision': 29,
    'unversioned_existing_tables': 30,
    'migration_required_but_not_enabled': 31,
    'database_name_mismatch': 32,
    'invalid_settings_jwt': 40,
    'invalid_settings_frontend': 41,
    'invalid_settings_database': 42,
    'invalid_settings_other': 43,
    'alembic_settings_invalid': 44,
    'alembic_runtime_dependency_missing': 45,
    'alembic_database_permission_denied': 46,
    'alembic_database_connect_failed': 47,
    'alembic_schema_conflict': 48,
    'alembic_revision_conflict': 49,
    'alembic_schema_sql_failed': 50,
    'api_import_failed': 60,
    'api_health_failed': 61,
    'api_readiness_failed': 62,
    'api_auth_guard_failed': 63,
    'api_cors_failed': 64,
    'staging_registration_failed': 65,
    'staging_login_failed': 66,
    'staging_authenticated_read_failed': 67,
    'staging_request_creation_failed': 68,
    'staging_cleanup_failed': 69,
    'staging_throttle_not_batched': 77,
    'auth_regression_failed': 72,
    'auth_regression_missing_pytest': 73,
    'auth_regression_tests_auth': 74,
    'auth_regression_tests_rate_limits': 75,
    'auth_regression_tests_postgres_throttle': 76,
    'staging_ai_prerequisite_failed': 78,
    'staging_ai_discovery_failed': 79,
    'staging_ai_analysis_failed': 80,
}
EXPECTED = {
    'production': (
        'ep-blue-band-bcjqtqrc.c-16.us-east-1.aws.neon.tech',
        'procurepilot_owner',
    ),
    'preview': (
        'ep-spring-silence-bc8oxuii.c-16.us-east-1.aws.neon.tech',
        'owner',
    ),
}


class ReleaseGateError(RuntimeError):
    def __init__(self, category: str):
        super().__init__(category)
        self.category = category


def checked_direct_url(raw: str, environment: str) -> str:
    """Return a direct/TLS URI, never an unsafe or unknown database target."""
    if environment not in EXPECTED:
        raise ReleaseGateError('unexpected_vercel_environment')
    if not raw:
        raise ReleaseGateError('database_url_absent')
    try:
        normalized = raw
        if normalized.startswith(('postgres://', 'postgresql://')):
            normalized = 'postgresql+psycopg://' + normalized.split('://', 1)[1]
        parsed = make_url(normalized)
        host, user = EXPECTED[environment]
        supplied_host = (parsed.host or '').lower()
        allowed = (host, host.replace('.c-16.', '-pooler.c-16.'))
        if (
            parsed.drivername != 'postgresql+psycopg'
            or supplied_host not in allowed
            or parsed.username != user
            or not parsed.password
            or parsed.database != 'procurepilot'
            or parsed.port not in (None, 5432)
            or parsed.query.get('sslmode') not in ('require', 'verify-full')
        ):
            raise ReleaseGateError('database_target_mismatch')
        return parsed.set(host=host).render_as_string(hide_password=False)
    except ReleaseGateError:
        raise
    except (ValueError, TypeError, AttributeError) as exc:
        raise ReleaseGateError('database_url_malformed') from exc


def status(direct_url: str) -> tuple[str | None, set[str]]:
    """Read-only metadata; no generated app model imports or customer rows."""
    engine = create_engine(
        direct_url, poolclass=NullPool,
        connect_args={'connect_timeout': 6, 'prepare_threshold': None},
    )
    try:
        with engine.connect() as conn:
            if conn.execute(text('SELECT current_database()')).scalar() != 'procurepilot':
                raise ReleaseGateError('database_name_mismatch')
            tables = set(inspect(conn).get_table_names(schema='public'))
            revision = None
            if 'alembic_version' in tables:
                revision = conn.execute(
                    text('SELECT version_num FROM public.alembic_version LIMIT 1')
                ).scalar_one_or_none()
            return revision, tables
    finally:
        engine.dispose()


def verify(revision: str | None, tables: set[str]) -> None:
    if revision != HEAD:
        raise ReleaseGateError('alembic_revision_outdated')
    if not REQUIRED.issubset(tables):
        raise ReleaseGateError('required_tables_missing')


def plan(revision: str | None, tables: set[str]) -> bool:
    """Reject unexpected pre-existing schemas instead of stamping/overwriting."""
    if revision == HEAD:
        verify(revision, tables)
        return False
    if revision is not None and revision not in KNOWN_REVISIONS:
        raise ReleaseGateError('unknown_alembic_revision')
    if revision is None and (tables & (REQUIRED - {'alembic_version'})):
        raise ReleaseGateError('unversioned_existing_tables')
    return True


def validate_fastapi_settings() -> None:
    """Exercise the identical Pydantic config path that FastAPI startup needs."""
    from pydantic import ValidationError
    from app.core.config import Settings
    try:
        Settings()
    except ValidationError as exc:
        # Settings' model_validator reports loc=(), not a field path. Do not
        # accidentally raise IndexError while classifying the original error.
        # Messages are inspected privately but NEVER printed.
        issues = exc.errors(include_input=False)
        fields = {
            str(problem['loc'][0]).lower()
            for problem in issues if problem.get('loc')
        }
        fixed_messages = ' '.join(str(p.get('msg', '')).lower() for p in issues)
        if ('jwt_secret_key' in fields or
                'jwt_secret_key' in fixed_messages or
                'unique jwt' in fixed_messages):
            code = 'invalid_settings_jwt'
        elif 'frontend_url' in fields or 'frontend_url' in fixed_messages:
            code = 'invalid_settings_frontend'
        elif 'database_url' in fields or 'database_url' in fixed_messages:
            code = 'invalid_settings_database'
        else:
            code = 'invalid_settings_other'
        raise ReleaseGateError(code) from exc
    except (ValueError, TypeError) as exc:
        raise ReleaseGateError('invalid_settings_other') from exc


def classify_alembic_failure(stderr: str, stdout: str) -> str:
    """Inspect errors privately and return only a safe allowlisted category."""
    combined = (stderr + '\n' + stdout).lower()
    if 'validation error for settings' in combined or 'pydantic' in combined and 'validationerror' in combined:
        return 'alembic_settings_invalid'
    if 'modulenotfounderror' in combined or 'no module named' in combined:
        return 'alembic_runtime_dependency_missing'
    if 'insufficientprivilege' in combined or 'permission denied for' in combined:
        return 'alembic_database_permission_denied'
    if any(term in combined for term in (
        'could not connect', 'connection refused', 'connection timed out',
        'operationalerror', 'password authentication failed', 'ssl error',
    )):
        return 'alembic_database_connect_failed'
    if 'duplicatetable' in combined or 'duplicateobject' in combined or 'already exists' in combined:
        return 'alembic_schema_conflict'
    if "can't locate revision" in combined or 'revisionerror' in combined:
        return 'alembic_revision_conflict'
    if 'programmingerror' in combined or 'syntaxerror' in combined or 'invalidforeignkey' in combined:
        return 'alembic_schema_sql_failed'
    return 'alembic_upgrade_failed'


def migrate(direct_url: str) -> None:
    env = os.environ.copy()
    env['DATABASE_URL'] = direct_url
    proc = subprocess.run(
        [sys.executable, '-m', 'alembic', '-c', 'alembic.ini', 'upgrade', HEAD],
        cwd=BACKEND, env=env, capture_output=True, text=True, timeout=180,
        check=False,
    )
    if proc.returncode:
        # stderr and stdout can contain driver-specific DSN parts.
        raise ReleaseGateError(classify_alembic_failure(proc.stderr, proc.stdout))


def smoke_fastapi(environment: str) -> None:
    """Exercise the actual ASGI application with Vercel's resolved environment.

    Production probes are read-only. Staging may exercise disposable writes
    when explicitly enabled and cleans up its user and request records.
    """
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        from app.core.config import get_settings
    except Exception as exc:
        raise ReleaseGateError('api_import_failed') from exc

    with TestClient(app) as client:
        if client.get('/api/v1/health').status_code != 200:
            raise ReleaseGateError('api_health_failed')
        if client.get('/api/v1/ready').status_code != 200:
            raise ReleaseGateError('api_readiness_failed')
        if client.get('/api/v1/auth/me').status_code != 401:
            raise ReleaseGateError('api_auth_guard_failed')
        origin = get_settings().frontend_url
        cors = client.options('/api/v1/auth/login', headers={
            'Origin': origin, 'Access-Control-Request-Method': 'POST',
        })
        if cors.status_code not in (200, 204) or cors.headers.get('access-control-allow-origin') != origin:
            raise ReleaseGateError('api_cors_failed')

        if environment != 'preview' or os.environ.get('PROCUREPILOT_STAGING_AUTH_SMOKE') != '1':
            return

        from secrets import token_hex, token_urlsafe
        from sqlalchemy import delete, event
        from app.core.database import SessionLocal, engine
        from app.models import ProcurementRequest, User

        email = 'pp-staging-check-' + token_hex(12) + '@example.com'
        password = token_urlsafe(24)
        user_id = None
        # Monitor the actual psycopg/Neon SQL generated by the authentication
        # endpoints. No SQL or user details are written to build logs.
        throttle_inserts = []
        def count_auth_upserts(_conn, _cursor, statement, _parameters, _context, _many):
            if 'INSERT INTO auth_rate_limit_counters' in statement:
                throttle_inserts.append(1)
        event.listen(engine, 'before_cursor_execute', count_auth_upserts)
        try:
            created = client.post('/api/v1/auth/register', json={
                'email': email, 'password': password,
                'full_name': 'Staging Verification',
            })
            if created.status_code != 201:
                raise ReleaseGateError('staging_registration_failed')
            user_id = created.json()['user']['id']
            token = created.json()['access_token']
            logged_in = client.post('/api/v1/auth/login', json={
                'email': email, 'password': password,
            })
            if logged_in.status_code != 200:
                raise ReleaseGateError('staging_login_failed')
            # One atomic source+identity UPSERT for register, one for login.
            # A regression to two separate SQL writes per request fails Preview.
            if len(throttle_inserts) != 2:
                raise ReleaseGateError('staging_throttle_not_batched')
            headers = {'Authorization': 'Bearer ' + token}
            me = client.get('/api/v1/auth/me', headers=headers)
            if me.status_code != 200 or me.json().get('id') != user_id:
                raise ReleaseGateError('staging_authenticated_read_failed')
            request = client.post('/api/v1/procurement-requests',
                headers=headers, json={
                    'request_text': 'Staging API connectivity smoke test only',
                    'quantity': 1, 'budget': '100.00', 'currency': 'USD',
                })
            if request.status_code != 201:
                raise ReleaseGateError('staging_request_creation_failed')
            if os.environ.get('PROCUREPILOT_STAGING_AI_ROUTE_SMOKE') == '1':
                # Mock ONLY the two external providers; keep the real
                # authenticated FastAPI endpoints, policy, SQL and Neon rows.
                # No Gemini charges, Channel3 quota or PayPal transactions.
                from types import SimpleNamespace
                from unittest.mock import patch
                from app.agents import runtime
                from app.api import procurement_requests as procurement_api
                from app.integrations.channel3.client import Channel3Client
                from app.integrations.channel3.schemas import (
                    Channel3Offer, Channel3Price, Channel3Product, Channel3SearchResponse,
                )
                request_id = request.json()['id']
                path = '/api/v1/procurement-requests/' + request_id
                before = client.post(path + '/analyze', headers=headers)
                if before.status_code != 409:
                    raise ReleaseGateError('staging_ai_prerequisite_failed')
                calls = {'catalogue': 0, 'model': 0}
                async def stub_catalogue(self, query, **kwargs):
                    calls['catalogue'] += 1
                    return Channel3SearchResponse(products=[Channel3Product(
                        id='staging-evidence-item',
                        title='Staging API connectivity smoke test only',
                        offers=[Channel3Offer(
                            url='https://seller.example/staging-item',
                            domain='seller.example', availability='InStock',
                            price=Channel3Price(amount='20.00', currency='USD'),
                        )],
                    )])
                async def stub_analysis(user_id, prompt, **kwargs):
                    calls['model'] += 1
                    return {
                        'text': 'Saved staging offer qualifies under the test policy.',
                        'model': 'test-provider', 'provider': 'gemini',
                        'usage': {'input_tokens': 7, 'output_tokens': 8},
                    }
                mock_settings = SimpleNamespace(
                    google_api_key='staging-mock-do-not-send',
                    ai_fallback_enabled=False,
                    ai_evidence_candidates=4,
                    ai_max_prompt_chars=3600,
                    ai_daily_user_runs=12,
                    ai_daily_global_runs=100,
                )
                with (
                    patch.object(Channel3Client, 'search_products', stub_catalogue),
                    patch.object(runtime, 'run_evidence_analysis', stub_analysis),
                    patch.object(procurement_api, 'reserve_ai_call',
                                 lambda *_args, **_kw: None),
                    patch.object(procurement_api, 'get_settings',
                                 lambda: mock_settings),
                ):
                    discovery = client.post(path + '/discover', headers=headers)
                    if discovery.status_code != 200:
                        raise ReleaseGateError('staging_ai_discovery_failed')
                    analysis = client.post(path + '/analyze', headers=headers)
                    cached = client.post(path + '/analyze', headers=headers)
                if (
                    analysis.status_code != 200
                    or analysis.json().get('source') != 'gemini'
                    or cached.status_code != 200
                    or cached.json().get('cached') is not True
                    or calls != {'catalogue': 1, 'model': 1}
                ):
                    raise ReleaseGateError('staging_ai_analysis_failed')

        finally:
            event.remove(engine, 'before_cursor_execute', count_auth_upserts)
            if user_id:
                try:
                    with SessionLocal() as db:
                        db.execute(delete(ProcurementRequest).where(
                            ProcurementRequest.user_id == user_id))
                        db.execute(delete(User).where(User.id == user_id))
                        db.commit()
                except Exception as exc:
                    raise ReleaseGateError('staging_cleanup_failed') from exc


def main() -> int:
    environment = os.environ.get('VERCEL_ENV', '')
    if not os.environ.get('VERCEL') and not environment:
        print('[release-db] skipped outside Vercel')
        return 0
    try:
        direct_url = checked_direct_url(os.environ.get('DATABASE_URL', ''), environment)
        validate_fastapi_settings()
        try:
            revision, tables = status(direct_url)
        except ReleaseGateError:
            raise
        except Exception as exc:
            raise ReleaseGateError('neon_connection_failed') from exc
        needs_upgrade = plan(revision, tables)
        if needs_upgrade:
            if os.environ.get('PROCUREPILOT_RUN_REVIEWED_MIGRATIONS') != '1':
                raise ReleaseGateError('migration_required_but_not_enabled')
            print('[release-db] applying reviewed non-destructive forward migration chain')
            migrate(direct_url)
            try:
                revision, tables = status(direct_url)
            except Exception as exc:
                raise ReleaseGateError('post_migration_db_connect_failed') from exc
        verify(revision, tables)
        smoke_fastapi(environment)
        print('[release-db] PASS FastAPI health/readiness/auth guards, Neon and Alembic 0010')
        return 0
    except ReleaseGateError as exc:
        print('[release-db] FAIL category=' + exc.category, file=sys.stderr)
        return FAILURE_CODES.get(exc.category, 70)
    except Exception as exc:
        # Keep raw exceptions private; DB exceptions often embed the DSN.
        print('[release-db] FAIL category=unexpected_' + type(exc).__name__,
              file=sys.stderr)
        return 71


if __name__ == '__main__':
    raise SystemExit(main())
