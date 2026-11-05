"""Offline QA orchestrator. Does not use real provider credentials or user DB."""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
REPORTS = ROOT / "qa" / "reports"
PYTHON = BACKEND / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def isolated_env():
    env = os.environ.copy()
    for name in ("GOOGLE_API_KEY", "CHANNEL3_API_KEY", "PAYPAL_CLIENT_ID",
                 "PAYPAL_CLIENT_SECRET", "PAYPAL_WEBHOOK_ID", "RATE_LIMIT_REDIS_URL"):
        env[name] = ""
    env.update({
        "APP_ENV": "test",
        "DATABASE_URL": "sqlite:///" + (REPORTS / "pytest-isolated.db").resolve().as_posix(),
        "PAYPAL_BASE_URL": "https://api-m.sandbox.paypal.com",
        "VITE_API_BASE_URL": "/api/v1",
        "PYTHONUNBUFFERED": "1",
    })
    return env


def execute(name, command, cwd, env, outcomes):
    logfile = REPORTS / (name.lower().replace(" ", "-") + ".log")
    print("\n" + "=" * 58, "\nGATE:", name, "\n" + "=" * 58, flush=True)
    began = time.monotonic()
    code = 1
    with logfile.open("w", encoding="utf-8") as output:
        try:
            with subprocess.Popen(
                [str(arg) for arg in command], cwd=str(cwd), env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, errors="replace", bufsize=1,
            ) as process:
                for line in process.stdout:
                    print(line, end="", flush=True)
                    output.write(line)
                code = process.wait()
        except (OSError, ValueError) as exc:
            message = type(exc).__name__ + ": " + str(exc)
            output.write(message + "\n")
            print("[ERROR]", message)
    result = {
        "name": name, "status": "PASS" if code == 0 else "FAIL",
        "exit_code": code, "seconds": round(time.monotonic() - began, 2),
        "log": logfile.relative_to(ROOT).as_posix(),
    }
    outcomes.append(result)
    print("[{}] {}".format(result["status"], name), flush=True)
    return code == 0


def summary(outcomes, started, selection):
    passed = sum(row["status"] == "PASS" for row in outcomes)
    failed = len(outcomes) - passed
    report = {
        "suite": "ProcurePilot offline QA", "started": started,
        "finished": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "selection": selection, "overall": "PASS" if outcomes and failed == 0 else "FAIL",
        "passed": passed, "failed": failed, "gates": outcomes,
        "live_providers": "NOT TESTED: Channel3, Gemini, PayPal buyer/capture and HTTPS webhooks",
    }
    (REPORTS / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# ProcurePilot offline QA report", "",
        "**Result: {}**. Passed: {}. Failed: {}.".format(report["overall"], passed, failed),
        "", "| Gate | Result | Seconds | Log |", "| --- | --- | ---: | --- |",
    ]
    for row in outcomes:
        lines.append("| {} | {} | {} | {} |".format(
            row["name"], row["status"], row["seconds"], row["log"]))
    lines += [
        "", "This does not verify real provider credentials, PayPal Sandbox buyer",
        "approval/capture, signed HTTPS webhook delivery, PostgreSQL upgrades,",
        "physical browsers, production hosting or the Devpost submission.",
        "",
        "Production build uses VITE_API_BASE_URL=/api/v1 as a QA-only value.",
        "A public deployment must configure an actual HTTPS API or reverse proxy.",
        "",
        "Logs stay local and may contain diagnostic data; redact before sharing.",
    ]
    (REPORTS / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nOVERALL: {} ({} passed, {} failed)".format(report["overall"], passed, failed))
    print("Report:", REPORTS / "summary.md")
    return failed == 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline tests and strict production build")
    parser.add_argument("--only", choices=["all", "backend", "frontend", "migrations"], default="all")
    parser.add_argument("--fail-fast", action="store_true")
    args = parser.parse_args(argv)
    REPORTS.mkdir(parents=True, exist_ok=True)
    if sys.version_info < (3, 12) or not PYTHON.is_file():
        print("[ERROR] Python 3.12+ and backend/.venv required. Run qa/setup.bat.")
        return 2
    frontend_needed = args.only in ("all", "frontend")
    node, npm = shutil.which("node"), shutil.which("npm")
    if frontend_needed and (not node or not npm or not (FRONTEND / "node_modules").is_dir()):
        print("[ERROR] Node/npm or frontend/node_modules missing. Run qa/setup.bat.")
        return 2

    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    env, results = isolated_env(), []
    def run(name, argv, cwd):
        ok = execute(name, argv, cwd, env, results)
        if args.fail_fast and not ok:
            summary(results, started, args.only)
            raise SystemExit(1)
        return ok

    if args.only in ("all", "backend"):
        run("Python syntax", [
            PYTHON, "-m", "compileall", "-q", "app", "tests", "../qa/tests/python",
            "../qa/migration_gate.py", "../qa/run.py",
        ], BACKEND)
        run("Backend Pytest coverage", [
            PYTHON, "-m", "pytest", "-q", "tests", "../qa/tests/python",
            "--junitxml=" + str(REPORTS / "pytest.xml"), "--cov=app",
            "--cov-branch", "--cov-report=term-missing:skip-covered",
            "--cov-report=xml:" + str(REPORTS / "coverage.xml"),
        ], BACKEND)
    if args.only in ("all", "backend", "migrations"):
        run("Isolated Alembic migrations", [PYTHON, ROOT / "qa" / "migration_gate.py"], ROOT)
    if frontend_needed:
        run("Node version", [node, FRONTEND / "scripts" / "check-node-version.cjs"], ROOT)
        run("Frontend ESLint", [npm, "run", "lint"], FRONTEND)
        run("Frontend Vitest", [npm, "test"], FRONTEND)
        run("Frontend deploy contracts", [npm, "run", "test:deploy-config"], FRONTEND)
        # Prevent a previous build being mistaken for a clean new build.
        dist = FRONTEND / "dist"
        if dist.is_dir():
            shutil.rmtree(dist)
        if run("Strict production build", [npm, "run", "build:deploy"], FRONTEND):
            run("Built asset smoke", [
                node, "--test", ROOT / "qa" / "tests" / "frontend" / "build-output.test.mjs",
            ], ROOT)
        else:
            results.append({
                "name": "Built asset smoke", "status": "FAIL", "exit_code": 1,
                "seconds": 0, "log": "skipped: production build failed",
            })
    return 0 if summary(results, started, args.only) else 1


if __name__ == "__main__":
    raise SystemExit(main())
