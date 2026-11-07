"""Clipboard-based Neon initialization regression tests; no production DB calls."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

QA = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(QA))
spec = importlib.util.spec_from_file_location("initialize_neon", QA / "initialize_neon.py")
initializer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(initializer)


def test_clipboard_pastes_without_exposing_secret_in_process_arguments(monkeypatch):
    calls = []
    raw = "postgresql://role:private-token@ep-db.us-east-1.aws.neon.tech/procurepilot?sslmode=require\r\n"
    monkeypatch.setattr(initializer.sys, "platform", "win32")

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout=raw if len(calls) == 1 else "")

    monkeypatch.setattr(initializer.subprocess, "run", fake_run)
    assert initializer.obtain_connection_url("clipboard") == raw.strip()
    assert len(calls) == 2
    assert "private-token" not in str(calls)
    assert "Get-Clipboard -Raw" in calls[0][0][-1]
    assert "Set-Clipboard" in calls[1][0][-1]


def test_clipboard_fails_without_copied_value(monkeypatch):
    monkeypatch.setattr(initializer.sys, "platform", "win32")
    monkeypatch.setattr(initializer.subprocess, "run",
                        lambda *a, **k: SimpleNamespace(returncode=0, stdout=""))
    with pytest.raises(ValueError, match="empty"):
        initializer.obtain_connection_url("clipboard")


def test_env_mode_does_not_spawn_powershell(monkeypatch):
    url = "postgresql://user:pw@ep-db.us-east-1.aws.neon.tech/procurepilot?sslmode=require"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setattr(initializer.subprocess, "run", lambda *a, **k: 1 / 0)
    assert initializer.obtain_connection_url("env") == url


def test_reject_non_windows_clipboard(monkeypatch):
    monkeypatch.setattr(initializer.sys, "platform", "linux")
    with pytest.raises(ValueError, match="Windows"):
        initializer.read_windows_clipboard()


def test_windows_default_uses_clipboard_instead_of_hidden_prompt(monkeypatch):
    monkeypatch.setattr(initializer.sys, "platform", "win32")
    monkeypatch.setattr(initializer, "obtain_connection_url", lambda mode: "")
    assert initializer.main([]) == 2


def test_python_docstring_has_no_invalid_escapes():
    import ast
    ast.parse((QA / "initialize_neon.py").read_text(encoding="utf-8"))


def test_successful_upgrade_saves_only_sanitized_database_report(monkeypatch, tmp_path, capsys):
    url = "postgresql://user:SENSITIVE-VALUE@ep-db.us-east-1.aws.neon.tech/procurepilot?sslmode=require"
    report = tmp_path / "neon.json"
    monkeypatch.setattr(initializer, "REPORT", report)
    monkeypatch.setattr(initializer, "BACKEND", tmp_path)
    monkeypatch.setattr(initializer, "obtain_connection_url", lambda mode: url)
    monkeypatch.setattr(initializer, "inspect_database", lambda raw: {
        "schema_ready": True, "target": "Neon PostgreSQL", "connected": True,
        "expected_revision": "0010_auth_throttles", "actual_revision": "0010_auth_throttles",
        "missing_tables": [], "database": "procurepilot", "uses_pooler": False,
    })
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, {**kwargs, "env": dict(kwargs.get("env", {}))}))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(initializer.subprocess, "run", fake_run)
    assert initializer.main(["--input", "env"]) == 0
    assert report.exists()
    assert "SENSITIVE-VALUE" not in report.read_text()
    assert "SENSITIVE-VALUE" not in capsys.readouterr().out
    assert calls[0][1]["env"]["DATABASE_URL"] == url
    assert "SENSITIVE-VALUE" not in str(calls[0][0])


def test_invalid_clipboard_url_never_starts_alembic(monkeypatch, capsys):
    monkeypatch.setattr(initializer, "obtain_connection_url",
                        lambda mode: "not a postgres URL")
    monkeypatch.setattr(initializer.subprocess, "run", lambda *a, **k: 1 / 0)
    assert initializer.main(["--input", "clipboard"]) == 2
    assert "not a postgres URL" not in capsys.readouterr().out
