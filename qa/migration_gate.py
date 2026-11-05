"""Check Alembic head from scratch and from revision 0005 in temporary SQLite DBs."""
from __future__ import annotations
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
REQUIRED = {
    "procurement_requests": {"policy_json"},
    "purchase_orders": {"evidence_json", "offer_verification_json", "assigned_approver_id"},
    "payments": {"paypal_order_id", "capture_id"},
}
LATEST = "0009_delegated_approver"


def upgrade(revision, env):
    print("+ alembic upgrade " + revision, flush=True)
    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", revision],
        cwd=BACKEND, env=env, check=True,
    )


def verify(database):
    with sqlite3.connect(database) as connection:
        actual = connection.execute("SELECT version_num FROM alembic_version").fetchone()
        assert actual and actual[0] == LATEST, "Wrong migration revision: " + str(actual)
        for table, expected in REQUIRED.items():
            columns = {
                row[1] for row in
                connection.execute("PRAGMA table_info('{}')".format(table))
            }
            assert expected <= columns, "{} missing {}".format(table, expected - columns)
        indexes = connection.execute("PRAGMA index_list('purchase_orders')").fetchall()
        assert any(row[1] == "ix_purchase_orders_assigned_approver_id" for row in indexes)
        constraints = connection.execute(
            "PRAGMA foreign_key_list('purchase_orders')"
        ).fetchall()
        assert any(
            fk[2] == "users" and fk[3] == "assigned_approver_id"
            and fk[4] == "id" and fk[6].upper() == "SET NULL"
            for fk in constraints
        ), "Delegated approver FK must reference users.id with SET NULL"
        assert not connection.execute("PRAGMA foreign_key_check").fetchall()
    print("[PASS] Version, tables, index and foreign keys", flush=True)


def main():
    with tempfile.TemporaryDirectory(prefix="procurepilot-qa-") as directory:
        for label, first in (("fresh", "head"), ("upgrade", "0005_read_indexes")):
            db = Path(directory) / (label + ".db")
            env = os.environ.copy()
            env["APP_ENV"] = "test"
            env["DATABASE_URL"] = "sqlite:///" + db.as_posix()
            for secret in ("GOOGLE_API_KEY", "CHANNEL3_API_KEY", "PAYPAL_CLIENT_ID",
                           "PAYPAL_CLIENT_SECRET", "PAYPAL_WEBHOOK_ID"):
                env[secret] = ""
            print("\n=== Migration scenario:", label, "===", flush=True)
            upgrade(first, env)
            if first != "head":
                upgrade("head", env)
            verify(db)
    print("[PASS] Both isolated migration scenarios", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
