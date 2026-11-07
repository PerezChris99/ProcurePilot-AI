"""No sensitive exception content is reported by hosted startup probes."""
import runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
probe=runpy.run_path(str(ROOT/"qa"/"hosted_readonly_check.py"))


def test_explicit_safe_startup_category_is_reported():
    safe=probe["safe_startup_category"]
    assert safe(b'{"code":"BACKEND_STARTUP_FAILED","category":"invalid_configuration"}')=="invalid_configuration"
    assert safe(b'{"code":"BACKEND_STARTUP_FAILED","category":"missing_runtime_dependency"}')=="missing_runtime_dependency"


def test_arbitrary_payload_and_secret_content_not_exposed():
    safe=probe["safe_startup_category"]
    assert safe(b'{"code":"BACKEND_STARTUP_FAILED","category":"password=secret"}') is None
    assert safe(b'{"code":"UNRELATED","category":"invalid_configuration"}') is None
    assert safe(b'<html>Internal Error</html>') is None
    assert safe(b'not-json') is None
