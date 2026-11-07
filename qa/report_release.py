#!/usr/bin/env python3
"""Offline release-evidence review. Never merges, pushes or deploys."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

GATES = (
    "Python syntax", "Backend Pytest coverage", "Isolated Alembic migrations",
    "Node version", "Frontend ESLint", "Frontend Vitest",
    "Frontend deploy contracts", "Strict production build", "Built asset smoke",
)
HOSTED = (
    "frontend", "spa_deep_link", "api_liveness", "postgres_readiness",
    "configured_cors", "orders_auth_guard", "trust_lab_auth_guard",
)


def read_report(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        report = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, ValueError):
        return None
    return report if isinstance(report, dict) else None


def offline_ok(report: dict | None) -> bool:
    if not report or report.get("overall") != "PASS":
        return False
    gates = report.get("gates")
    if not isinstance(gates, list):
        return False
    results = {row.get("name"): row.get("status")
               for row in gates if isinstance(row, dict)}
    return len(results) == len(GATES) and all(
        results.get(name) == "PASS" for name in GATES
    )


def hosted_ok(report: dict | None) -> bool:
    if not report or report.get("overall") != "PASS" or report.get("provider_payment_tested") is not False:
        return False
    rows = report.get("checks")
    if not isinstance(rows, list):
        return False
    results = {row.get("check"): row.get("status")
               for row in rows if isinstance(row, dict)}
    return len(results) == len(HOSTED) and all(
        results.get(name) == "PASS" for name in HOSTED
    )


def neon_ok(report: dict | None) -> bool:
    return bool(report and report.get("target") == "Neon PostgreSQL" and
                report.get("status") == "PASS" and
                report.get("connected") is True and
                report.get("schema_ready") is True and
                report.get("expected_revision") == "0010_auth_throttles" and
                report.get("actual_revision") == "0010_auth_throttles" and
                report.get("missing_tables") == [])


def git_status(root: Path) -> dict:
    try:
        def git(*args):
            return subprocess.run(["git", *args], cwd=root,
                                  capture_output=True, text=True,
                                  check=True, timeout=8).stdout.strip()
        return {"branch": git("branch", "--show-current"),
                "sha": git("rev-parse", "--verify", "HEAD"),
                "clean": not bool(git("status", "--porcelain"))}
    except (subprocess.SubprocessError, OSError):
        return {"branch": None, "sha": None, "clean": False}


def run(root: Path) -> dict:
    qa = root / "qa" / "reports"
    source = git_status(root)
    offline = offline_ok(read_report(qa / "summary.json"))
    neon = neon_ok(read_report(qa / "neon.json"))
    hosted = hosted_ok(read_report(qa / "hosted.json"))
    ready = offline and neon and hosted and source["branch"] == "perez" and source["clean"]
    return {
        "mode": "read_only; no GitHub or Vercel writes",
        "branch": source["branch"], "sha": source["sha"],
        "git_clean": source["clean"],
        "offline_9_of_9": offline, "neon_schema_verified": neon,
        "hosted_7_of_7": hosted,
        "provider_payment_end_to_end": "NOT VERIFIED by this tool",
        "release_review": "ELIGIBLE_FOR_HUMAN_REVIEW" if ready else "BLOCKED",
        "merging_performed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    result = run(args.root.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["release_review"] == "ELIGIBLE_FOR_HUMAN_REVIEW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
