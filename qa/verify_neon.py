#!/usr/bin/env python3
"""Read-only Neon connectivity and Alembic schema verification.

Pass DATABASE_URL as a private environment variable, never a CLI argument.
No migrations, writes, credentials, SQL exception texts or user rows printed.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

EXPECTED_REVISION = "0010_auth_throttles"
REQUIRED_TABLES = frozenset({
    "alembic_version", "users", "procurement_requests", "purchase_orders",
    "purchase_order_items", "approvals", "payments", "webhook_events",
    "audit_events", "ai_daily_budgets", "auth_rate_limit_counters",
})


def connection_target(raw: str | None) -> tuple[str, str]:
    if not raw:
        raise ValueError("Missing DATABASE_URL")
    normalized = raw.replace("postgresql+psycopg://", "postgresql://", 1)
    if normalized.startswith("postgres://"):
        normalized = "postgresql://" + normalized.partition("://")[2]
    parsed = urlsplit(normalized)
    host = (parsed.hostname or "").lower()
    db_name = parsed.path.removeprefix("/")
    if parsed.scheme != "postgresql" or not host.endswith(".neon.tech"):
        raise ValueError("Not a Neon PostgreSQL connection")
    if not db_name or "/" in db_name or not parsed.username or not parsed.password:
        raise ValueError("Database, role or password absent")
    if "sslmode=require" not in parsed.query and "sslmode=verify-full" not in parsed.query:
        raise ValueError("TLS must be required")
    if parsed.port not in (None, 5432):
        raise ValueError("Unexpected Postgres port")
    return host, db_name


def analyze_schema(revision: str | None, tables: set[str]) -> dict:
    missing = sorted(REQUIRED_TABLES - tables)
    return {
        "expected_revision": EXPECTED_REVISION,
        "actual_revision": revision,
        "required_tables": len(REQUIRED_TABLES),
        "missing_tables": missing,
        "migration_current": revision == EXPECTED_REVISION,
        "schema_ready": revision == EXPECTED_REVISION and not missing,
    }


def inspect_database(raw_url: str) -> dict:
    host, expected_name = connection_target(raw_url)
    from sqlalchemy import create_engine, text
    from sqlalchemy.pool import NullPool

    sqlalchemy_url = raw_url
    if sqlalchemy_url.startswith(("postgresql://", "postgres://")):
        sqlalchemy_url = "postgresql+psycopg://" + sqlalchemy_url.split("://", 1)[1]
    engine = create_engine(sqlalchemy_url, poolclass=NullPool,
                           connect_args={"connect_timeout": 6})
    try:
        with engine.connect() as db:
            meta = db.execute(text(
                "SELECT current_database(), current_setting('server_version_num')"
            )).one()
            database_name, version_num = str(meta[0]), int(meta[1])
            if database_name != expected_name:
                raise ValueError("Connected database differs from URI")
            table_names = set(db.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
            )).scalars().all())
            revision = None
            if "alembic_version" in table_names:
                revision = db.execute(text(
                    "SELECT version_num FROM alembic_version LIMIT 1"
                )).scalar()
            return {
                "postgres_major_version": version_num // 10000,
                "target": "Neon PostgreSQL",
                "database": database_name,
                "uses_pooler": "-pooler" in host,
                "connected": True,
                **analyze_schema(revision, table_names),
            }
    finally:
        engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-direct", action="store_true",
                        help="Reject pooled Neon endpoints")
    parser.add_argument("--output", type=Path, default=None,
                        help="Write a secret-free JSON evidence report")
    args = parser.parse_args(argv)
    try:
        result = inspect_database(os.environ.get("DATABASE_URL", ""))
        if args.require_direct and result["uses_pooler"]:
            result["schema_ready"] = False
            result["reason"] = "Use a direct Neon URL for migration verification"
        result["status"] = "PASS" if result["schema_ready"] else "FAIL"
    except Exception as error:
        # Exceptions can embed connection URI components: never print str(error).
        result = {"target": "Neon PostgreSQL", "connected": False,
                  "status": "FAIL", "error_category": type(error).__name__,
                  "next_action": "Check Neon role, password, TLS and database name"}
    output = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
