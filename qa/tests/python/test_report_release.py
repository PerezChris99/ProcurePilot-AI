"""Release evidence is never assumed from an incomplete report."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = spec_from_file_location("report_release", ROOT / "qa" / "report_release.py")
report_release = module_from_spec(spec)
spec.loader.exec_module(report_release)


def test_offline_requires_nine_nine():
    sample = {"overall": "PASS", "gates": [
        {"name": name, "status": "PASS"} for name in report_release.GATES
    ]}
    assert report_release.offline_ok(sample)
    sample["gates"].pop()
    assert not report_release.offline_ok(sample)


def test_hosted_seven_seven_does_not_claim_payment():
    sample = {"overall": "PASS", "provider_payment_tested": False, "checks": [
        {"check": name, "status": "PASS"} for name in report_release.HOSTED
    ]}
    assert report_release.hosted_ok(sample)
    sample["provider_payment_tested"] = True
    assert not report_release.hosted_ok(sample)


def test_neon_requires_proven_schema():
    sample = {"status": "PASS", "target": "Neon PostgreSQL",
              "connected": True, "schema_ready": True,
              "expected_revision": "0010_auth_throttles",
              "actual_revision": "0010_auth_throttles", "missing_tables": []}
    assert report_release.neon_ok(sample)
    sample["actual_revision"] = "0009_delegated_approver"
    assert not report_release.neon_ok(sample)


def test_missing_reports_do_not_authorize_merge(tmp_path):
    assert report_release.read_report(tmp_path / "missing.json") is None
    result = report_release.run(tmp_path)
    assert result["release_review"] == "BLOCKED"
    assert result["merging_performed"] is False
