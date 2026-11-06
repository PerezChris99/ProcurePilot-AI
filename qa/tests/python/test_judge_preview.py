"""Offline launcher contracts: do not read secrets or contact providers."""
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[3]
module = runpy.run_path(str(ROOT / "judge-preview.py"))


def test_judge_environment_uses_isolated_sqlite_and_never_inherits_secret_keys():
    given = {
        "PATH": "safe",
        "DATABASE_URL": "postgresql+psycopg://admin:secret@prod-db/procurepilot",
        "GOOGLE_API_KEY": "secret-gemini",
        "GROQ_API_KEY": "secret-groq",
        "CHANNEL3_API_KEY": "secret-channel3",
        "PAYPAL_CLIENT_SECRET": "secret-paypal",
        "VITE_EXPOSED_PROVIDER_KEY": "should-never-ship",
        "VITE_API_BASE_URL": "https://previous-production.example/api/v1",
        "APP_ENV": "production",
    }
    result = module["isolated_env"](given)
    assert result["PATH"] == "safe"
    assert result["APP_ENV"] == "development"
    assert result["DATABASE_URL"] == "sqlite:///./procurepilot_judge_preview.db"
    assert result["VITE_API_BASE_URL"] == "http://localhost:8000/api/v1"
    assert result["AI_FALLBACK_ENABLED"] == "false"
    assert result["FRONTEND_URL"] == "http://localhost:5173"
    for key in module["SAFE_KEYS"]:
        assert result[key] == ""
    assert "VITE_EXPOSED_PROVIDER_KEY" not in result
    assert given["GOOGLE_API_KEY"] == "secret-gemini"  # original untouched


def test_judge_preview_is_transparent_about_external_execution():
    runner = (ROOT / "judge-preview.py").read_text(encoding="utf-8")
    assert "--seed-email" in runner
    assert "seed_judge_preview.py" in runner
    assert "AI_FALLBACK_ENABLED" in runner
    assert "npm" in runner and "alembic" in runner
    assert ".env" not in runner.split("def start_preview", 1)[1].split("def seed_sample", 1)[0]
