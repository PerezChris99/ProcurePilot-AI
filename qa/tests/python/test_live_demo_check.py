"""Local tests for the credential-free hosted acceptance checker."""
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parents[3]
checker=runpy.run_path(str(ROOT/"qa"/"live_demo_check.py"))


def test_external_origins_are_https_without_credentials_or_unsafe_ports():
    url=checker["exact_https_origin"]
    assert url("https://APP.Example.com/")=="https://app.example.com"
    for bad in ("http://demo.example","https://localhost",
                "https://127.0.0.1","https://user:secret@demo.example",
                "https://demo.example/query","https://demo.example/?token=123",
                "https://demo.example:8080"):
        try:
            url(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Unsafe origin accepted: {bad}")


def test_checker_can_confirm_infrastructure_without_ever_calling_payment():
    seen=[]
    def fake_fetch(url, *, method="GET", headers=None):
        seen.append((url,method,headers or {}))
        if method=="OPTIONS":
            return 200,"",{"access-control-allow-origin":"https://frontend.example"}
        if url.endswith("/health"):
            return 200,'{"status":"ok"}',{"content-type":"application/json"}
        if url.endswith("/ready"):
            return 200,'{"status":"ready"}',{"content-type":"application/json"}
        if url.endswith("/purchase-orders") or url.endswith("/trust-lab/scenarios"):
            return 401,'{"detail":"Not authenticated"}',{}
        return 200,"<!DOCTYPE html><html></html>",{"content-type":"text/html"}
    rows=checker["checks"]("https://frontend.example",
                           "https://api.example",fetch=fake_fetch)
    assert len(rows)==7
    assert all(item["status"]=="PASS" for item in rows)
    assert all(verb in ("GET","OPTIONS") for _,verb,_ in seen)
    assert not any("/payments/" in url or "/webhooks/" in url for url,_,_ in seen)


def test_checker_reports_deployment_mismatch_as_failed_gate_without_secrets():
    def bad_fetch(url, *, method="GET", headers=None):
        return 503,'{"error":"offline"}',{}
    rows=checker["checks"]("https://frontend.example",
                           "https://api.example",fetch=bad_fetch)
    assert len(rows)==7
    assert all(row["status"]=="FAIL" for row in rows)


def test_preview_automation_secret_is_never_sent_to_production(monkeypatch):
    monkeypatch.setenv("VERCEL_AUTOMATION_BYPASS_SECRET", "very-private-preview-token")
    headers=checker["_protection_headers"]
    assert headers("https://procurepilotai-preview.vercel.app/api/v1/health")=={
        "x-vercel-protection-bypass":"very-private-preview-token",
    }
    assert headers("https://procurepilotai.vercel.app/api/v1/health")=={}
    assert headers("https://untrusted.example.com/api/v1/health")=={}
    assert headers("https://fake-procurepilotai-preview.vercel.app/")=={}
    monkeypatch.setenv("VERCEL_AUTOMATION_BYPASS_SECRET", "bad\\ntoken")
    assert headers("https://procurepilotai-preview.vercel.app/")=={}
