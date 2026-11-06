#!/usr/bin/env python3
"""Local judge preview: isolated SQLite, zero live provider calls, no .env writes.

This is a safe UI/policy preview, NOT a substitute for the live hosted PayPal
Sandbox demonstration required to verify full external integration.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
VENV_PYTHON = BACKEND / ".venv" / (
    "Scripts/python.exe" if os.name == "nt" else "bin/python"
)
OFFLINE_DB = "sqlite:///./procurepilot_judge_preview.db"
SAFE_KEYS = (
    "GOOGLE_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY",
    "CHANNEL3_API_KEY", "PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET",
    "PAYPAL_WEBHOOK_ID", "RATE_LIMIT_REDIS_URL",
)


def isolated_env(source: dict[str, str] | None = None) -> dict[str, str]:
    """Environment overrides a developer's actual .env without changing files.

    Empty provider keys MUST be passed as process variables; merely deleting
    them from the process would re-expose keys stored in a local root .env.
    """
    env = dict(os.environ if source is None else source)
    for key in tuple(env):
        if key.startswith("VITE_"):
            del env[key]
    env.update({key: "" for key in SAFE_KEYS})
    env.update({
        "APP_ENV": "development",
        "DATABASE_URL": OFFLINE_DB,
        "JWT_SECRET_KEY": "local-judge-preview-no-production-use",
        "FRONTEND_URL": "http://localhost:5173",
        "VITE_API_BASE_URL": "http://localhost:8000/api/v1",
        "AI_FALLBACK_ENABLED": "false",
        "PAYPAL_BASE_URL": "https://api-m.sandbox.paypal.com",
        "PYTHONUNBUFFERED": "1",
        "PYTHONUTF8": "1",
    })
    return env


def command(args: list[str], cwd: Path, env: dict[str, str]) -> None:
    subprocess.run([str(part) for part in args], cwd=str(cwd), env=env, check=True)


def requirements(env: dict[str, str], *, skip_install: bool = False) -> tuple[str, str]:
    if sys.version_info < (3, 12):
        raise RuntimeError("Python 3.12+ is required. Install a supported Python release.")
    node, npm = shutil.which("node"), shutil.which("npm")
    if not node or not npm:
        raise RuntimeError("Node.js 22.12+ and npm are required.")
    command([node, FRONTEND / "scripts" / "check-node-version.cjs"], ROOT, env)

    if not VENV_PYTHON.is_file() and skip_install:
        raise RuntimeError("Missing Python venv; run without --skip-install first.")
    if not VENV_PYTHON.is_file():
        print("[1/5] Creating isolated backend Python environment", flush=True)
        command([sys.executable, "-m", "venv", BACKEND / ".venv"], ROOT, env)
    if not skip_install:
        print("[2/5] Installing backend and frontend dependencies", flush=True)
        command([VENV_PYTHON, "-m", "pip", "install", "-r",
                 BACKEND / "requirements.txt"], ROOT, env)
        command([npm, "install", "--no-package-lock", "--no-audit", "--no-fund"],
                FRONTEND, env)
    elif not (FRONTEND / "node_modules" / "vite" / "bin" / "vite.js").is_file():
        raise RuntimeError("Missing frontend dependencies; run without --skip-install.")
    return node, npm


def stop_process(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=6)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=4)


def start_preview(env: dict[str, str], *, skip_install: bool = False) -> None:
    node, npm = requirements(env, skip_install=skip_install)
    print("[3/5] Migrating ONLY the isolated preview SQLite database", flush=True)
    command([VENV_PYTHON, "-m", "alembic", "upgrade", "head"], BACKEND, env)
    print("[4/5] Building React before starting the preview", flush=True)
    command([npm, "run", "build"], FRONTEND, env)
    print("[5/5] Starting the local preview (no external provider credentials)", flush=True)
    print("Frontend: http://127.0.0.1:5173", flush=True)
    print("API:      http://127.0.0.1:8000/api/v1/ready", flush=True)
    print("Use Get started to register; see docs/JUDGES_START_HERE.md.", flush=True)
    print("Press Ctrl+C to stop both servers.", flush=True)
    backend = frontend = None
    try:
        backend = subprocess.Popen(
            [str(VENV_PYTHON), "-m", "uvicorn", "app.main:app",
             "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(BACKEND), env=env,
        )
        frontend = subprocess.Popen(
            [node, str(FRONTEND / "node_modules" / "vite" / "bin" / "vite.js"),
             "--host", "127.0.0.1", "--port", "5173", "--strictPort"],
            cwd=str(FRONTEND), env=env,
        )
        while backend.poll() is None and frontend.poll() is None:
            time.sleep(0.4)
        raise RuntimeError("A preview server exited. Inspect the terminal output.")
    finally:
        stop_process(frontend)
        stop_process(backend)


def seed_sample(env: dict[str, str], email: str) -> None:
    if not VENV_PYTHON.is_file():
        raise RuntimeError("Run the preview first to install dependencies and migrate SQLite.")
    print("Seeding clearly labelled, NON-PAYABLE sample evidence.", flush=True)
    command([VENV_PYTHON, BACKEND / "scripts" / "seed_judge_preview.py",
             "--email", email], BACKEND, env)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Safe isolated judge preview; does not use real provider keys"
    )
    parser.add_argument("--skip-install", action="store_true",
                        help="Use already installed Python/npm dependencies")
    parser.add_argument("--seed-email", metavar="EMAIL",
                        help="Seed a labelled offline example for an existing account")
    args = parser.parse_args(argv)
    env = isolated_env()
    try:
        if args.seed_email:
            seed_sample(env, args.seed_email)
        else:
            start_preview(env, skip_install=args.skip_install)
    except KeyboardInterrupt:
        print("\nLocal preview stopped.", flush=True)
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        print("[ERROR] Judge preview failed: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
