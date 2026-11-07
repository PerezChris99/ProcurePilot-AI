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
        fields = {str(problem.get('loc', [''])[0]).lower()
                  for problem in exc.errors(include_input=False)}
        if 'jwt_secret_key' in fields or any('jwt' in f for f in fields):
            code = 'invalid_settings_jwt'
        elif 'frontend_url' in fields:
            code = 'invalid_settings_frontend'
        elif 'database_url' in fields:
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
        print('[release-db] PASS Neon target, SQL connectivity, Alembic 0010 and required tables')
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
