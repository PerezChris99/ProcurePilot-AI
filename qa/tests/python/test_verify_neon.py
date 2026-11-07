"""Read-only Neon verification tests; never connect to a real database."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[3]
spec = spec_from_file_location("verify_neon", ROOT / "qa" / "verify_neon.py")
verify_neon = module_from_spec(spec)
spec.loader.exec_module(verify_neon)


def test_neon_target_parsing_preserves_privacy():
    raw = "postgresql+psycopg://user:private-pass@ep-demo.c-16.us-east-1.aws.neon.tech/procurepilot?sslmode=require"
    assert verify_neon.connection_target(raw) == (
        "ep-demo.c-16.us-east-1.aws.neon.tech", "procurepilot"
    )


@pytest.mark.parametrize("unsafe", [
    None, "", "sqlite:///local.db",
    "postgresql://user:pw@localhost/procurepilot?sslmode=require",
    "postgresql://user:pw@attackerneon.tech/procurepilot?sslmode=require",
    "postgresql://user:pw@ep-demo.neon.tech/procurepilot",
    "postgresql://user:pw@ep-demo.neon.tech/procurepilot?sslmode=disable",
    "postgresql://user:pw@ep-demo.neon.tech:9999/procurepilot?sslmode=require",
])
def test_neon_rejects_unsafe_targets(unsafe):
    with pytest.raises(ValueError):
        verify_neon.connection_target(unsafe)


def test_neon_schema_requires_all_tables_and_correct_revision():
    tables = set(verify_neon.REQUIRED_TABLES)
    assert verify_neon.analyze_schema("0010_auth_throttles", tables)["schema_ready"]
    assert not verify_neon.analyze_schema("0009_delegated_approver", tables)["schema_ready"]
    assert not verify_neon.analyze_schema("0010_auth_throttles", {"users"})["schema_ready"]


def test_failed_neon_checks_never_echo_password(monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:superSecret@localhost/procurepilot")
    assert verify_neon.main([]) == 1
    output = capsys.readouterr().out
    assert "superSecret" not in output
    assert "postgresql://" not in output
