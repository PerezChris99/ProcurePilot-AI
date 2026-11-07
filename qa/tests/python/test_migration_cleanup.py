"""Migration gate must release temporary SQLite files, especially on Windows."""
from contextlib import closing
import importlib.util
from pathlib import Path
import sqlite3

import pytest


GATE_PATH = Path(__file__).resolve().parents[2] / "migration_gate.py"
spec = importlib.util.spec_from_file_location("procurepilot_migration_gate", GATE_PATH)
migration_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration_gate)


def _make_database(path, revision):
    with closing(sqlite3.connect(path)) as db:
        db.executescript("""
            CREATE TABLE alembic_version (version_num TEXT NOT NULL);
            CREATE TABLE users (id TEXT PRIMARY KEY);
            CREATE TABLE procurement_requests (policy_json TEXT);
            CREATE TABLE purchase_orders (
                evidence_json TEXT,
                offer_verification_json TEXT,
                assigned_approver_id TEXT,
                FOREIGN KEY(assigned_approver_id) REFERENCES users(id) ON DELETE SET NULL
            );
            CREATE INDEX ix_purchase_orders_assigned_approver_id
                ON purchase_orders(assigned_approver_id);
            CREATE TABLE payments (paypal_order_id TEXT, capture_id TEXT);
            CREATE TABLE auth_rate_limit_counters (
                bucket_key TEXT PRIMARY KEY, hits INTEGER, expires_at TEXT
            );
        """)
        db.execute("INSERT INTO alembic_version (version_num) VALUES (?)", (revision,))
        db.commit()


def _track_connection_closes(monkeypatch):
    original = sqlite3.connect
    closed = []

    class TrackedConnection(sqlite3.Connection):
        def close(self):
            closed.append(self)
            return super().close()

    def connect(*args, **kwargs):
        kwargs["factory"] = TrackedConnection
        return original(*args, **kwargs)

    monkeypatch.setattr(migration_gate.sqlite3, "connect", connect)
    return closed


def test_migration_verification_closes_sqlite_connection_after_success(tmp_path, monkeypatch):
    db_path = tmp_path / "fresh.db"
    _make_database(db_path, migration_gate.LATEST)
    closed = _track_connection_closes(monkeypatch)
    migration_gate.verify(db_path)
    assert len(closed) == 1
    # A closing connection must also allow the fixture to be safely deleted.
    db_path.unlink()
    assert not db_path.exists()


def test_migration_verification_closes_sqlite_connection_after_failure(tmp_path, monkeypatch):
    db_path = tmp_path / "upgrade.db"
    _make_database(db_path, "0001_users")
    closed = _track_connection_closes(monkeypatch)
    with pytest.raises(AssertionError, match="Wrong migration revision"):
        migration_gate.verify(db_path)
    assert len(closed) == 1
    db_path.unlink()
    assert not db_path.exists()
