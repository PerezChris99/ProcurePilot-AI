#!/usr/bin/env python3
r"""One-command Neon Alembic upgrade and verification.

Windows VS Code terminals may not paste into getpass. Instead, copy the
DIRECT TLS connection URL from Neon Connect and run:
    .\backend\.venv\Scripts\python.exe .\qa\initialize_neon.py
On Windows the script reads the clipboard without displaying it, then clears
that clipboard. Use --input env for an already-set private DATABASE_URL.
No URL, password, or raw SQL driver exception is printed or saved.
"""
from __future__ import annotations

import argparse
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


def read_windows_clipboard() -> str:
    """Copy a secret through captured stdio, never through process arguments."""
    if sys.platform != "win32":
        raise ValueError("Clipboard input is available only on Windows")
    cmd = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
           "$ErrorActionPreference='Stop'; [Console]::Out.Write((Get-Clipboard -Raw))"]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=12)
    if result.returncode != 0:
        raise ValueError("Unable to read Windows clipboard")
    value = result.stdout.strip()
    if not value:
        raise ValueError("Windows clipboard is empty; copy the Neon Direct URL first")
    # Do not leave the DB password on the shared Windows clipboard.
    try:
        cleared = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive",
                                  "-Command", "Set-Clipboard -Value ''"],
                                 capture_output=True, text=True, timeout=8, check=False)
        if cleared.returncode != 0:
            print("[WARN] Could not clear clipboard. Clear it manually after setup.")
    except (OSError, subprocess.TimeoutExpired):
        print("[WARN] Could not clear clipboard. Clear it manually after setup.")
    return value


def obtain_connection_url(mode: str) -> str:
    if mode == "clipboard":
        return read_windows_clipboard()
    if mode == "env":
        return os.environ.get("DATABASE_URL", "").strip()
    if mode == "prompt":
        return getpass("Enter Neon DIRECT connection URL (input hidden): ").strip()
    raise ValueError("Unknown connection input mode")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", choices=("clipboard", "env", "prompt"),
                        default="clipboard" if sys.platform == "win32" else "prompt",
                        help="Windows default: clipboard; other systems: hidden prompt")
    parser.add_argument("--smoke", action="store_true", help="After migration test the isolated staging FastAPI/Neon workflows")
    args = parser.parse_args(argv)
    try:
        if args.input == "clipboard":
            print("[INFO] Reading the copied Neon Direct URL from Windows clipboard.")
        raw = obtain_connection_url(args.input)
        host, database = connection_target(raw)
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        # This is only our own sanitized explanation, not the underlying URL.
        print("[FAIL] Could not obtain a valid Neon Direct TLS URL:", type(exc).__name__)
        print("Copy Neon Console → procurepilot-ai → Connect → Direct URL, then rerun.")
        return 2
    if "-pooler" in host:
        print("[FAIL] Neon Direct URL required; turn Connection pooling OFF in Connect.")
        return 2
    if database != "procurepilot":
        print("[FAIL] Expected database name: procurepilot.")
        return 2

    if args.smoke and host != "ep-spring-silence-bc8oxuii.c-16.us-east-1.aws.neon.tech":
        print("[FAIL] --smoke is limited to the isolated staging Neon project.")
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
            print("[FAIL] Alembic failed. Check Neon Direct role, password, TLS, and database privileges.")
            return 1
        print("[PASS] Non-destructive Alembic upgrade head completed.")
        status = inspect_database(raw)
        status["status"] = "PASS" if status["schema_ready"] else "FAIL"
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
        if not status["schema_ready"]:
            print("[FAIL] Database connected but schema is not ready.")
            return 1
        print("[PASS] Neon connected, schema at 0010, required tables exist.")
        if args.smoke:
            check = subprocess.run([sys.executable, str(ROOT / "qa" / "staging_e2e.py")],
                cwd=ROOT, env=env, capture_output=True, text=True,
                timeout=150, check=False)
            if check.returncode:
                print("[FAIL] Staging API/Neon workflow; see qa/reports/staging-e2e.json")
                return 1
            print("[PASS] Real staging registration, JWT, procurement, policy and isolation.")
        print("Evidence: qa/reports/neon.json (credential-free and ignored by Git)")
        return 0
    except Exception as exc:
        print("[FAIL] Neon initialization stopped:", type(exc).__name__)
        return 1
    finally:
        env.pop("DATABASE_URL", None)
        raw = ""


if __name__ == "__main__":
    raise SystemExit(main())
