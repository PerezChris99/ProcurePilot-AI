#!/usr/bin/env python3
"""One-command, explicitly invoked Neon Alembic upgrade and verification.

Run from a trusted Windows/VS Code terminal with backend/.venv:
    .\backend\.venv\Scripts\python.exe .\qa\initialize_neon.py

The input is hidden. No URL, password, or raw driver error is printed.
"""
from __future__ import annotations

from getpass import getpass
from pathlib import Path
import json
import os
import subprocess
import sys

from verify_neon import connection_target, inspect_database

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
REPORT = ROOT / "qa" / "reports" / "neon.json"


def main() -> int:
    raw = getpass("Paste Neon DIRECT connection URL (input hidden): ").strip()
    try:
        host, database = connection_target(raw)
    except ValueError:
        print("[FAIL] Require the Neon direct PostgreSQL URL with TLS.")
        return 2
    if "-pooler" in host:
        print("[FAIL] Disable connection pooling in Neon Connect for Alembic.")
        return 2
    if database != "procurepilot":
        print("[FAIL] Expected database: procurepilot.")
        return 2

    env = os.environ.copy()
    env["DATABASE_URL"] = raw
    try:
        task = subprocess.run(
            [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
            cwd=BACKEND, env=env, capture_output=True, text=True, timeout=180,
            check=False,
        )
        if task.returncode:
            print("[FAIL] Alembic migration failed. Check Neon role, TLS and privileges.")
            return 1
        print("[PASS] Non-destructive Alembic upgrade head completed.")
        status = inspect_database(raw)
        status["status"] = "PASS" if status["schema_ready"] else "FAIL"
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
        if not status["schema_ready"]:
            print("[FAIL] Database connected but schema is not ready.")
            return 1
        print("[PASS] Neon connected, schema at 0010, all required tables exist.")
        print("Evidence: qa/reports/neon.json (no credentials or user data)")
        return 0
    except Exception as error:
        # SQL driver exception messages can contain host/user information.
        print("[FAIL] Neon setup or verification stopped:", type(error).__name__)
        return 1
    finally:
        env.pop("DATABASE_URL", None)


if __name__ == "__main__":
    raise SystemExit(main())
