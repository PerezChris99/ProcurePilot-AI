#!/usr/bin/env python3
"""Read-only acceptance of public or authenticated automated-preview deployment.

This tool never logs in, sends payment requests, or calls Channel3/Gemini/PayPal.
It optionally reads a protected-preview automation secret from process env. A PASS is infrastructure/access
proof only, not live provider-transaction proof.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from urllib import error, request
from urllib.parse import urlsplit


def exact_https_origin(value: str) -> str:
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or not parsed.hostname or
            parsed.username or parsed.password or parsed.path not in ("", "/") or
            parsed.query or parsed.fragment):
        raise ValueError("Expected a public HTTPS origin without credentials, path or query")
    if parsed.hostname in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("This check requires a public HTTPS deployment")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Invalid HTTPS port") from exc
    if port not in (None, 443):
        raise ValueError("Non-standard ports are not accepted for public judging")
    return "https://" + parsed.hostname.lower()


PREVIEW_ORIGIN = "procurepilotai-preview.vercel.app"

def _protection_headers(url: str) -> dict[str, str]:
    """Never send the automation bypass token to production or other hosts."""
    if urlsplit(url).hostname != PREVIEW_ORIGIN:
        return {}
    token = os.environ.get("VERCEL_AUTOMATION_BYPASS_SECRET", "").strip()
    if not token or any(c in token for c in "\r\n"):
        return {}
    return {"x-vercel-protection-bypass": token}


class _NoCrossOriginRedirect(request.HTTPRedirectHandler):
    """Protected preview requests must not forward secrets via HTTP redirects."""
    def redirect_request(self, req, fp, code, msg, hdrs, newurl):
        if "x-vercel-protection-bypass" in {k.lower() for k in req.headers}:
            return None
        return super().redirect_request(req, fp, code, msg, hdrs, newurl)


def inspect(url: str, *, method: str = "GET",
            headers: dict[str, str] | None = None) -> tuple[int, str, dict[str, str]]:
    safe_headers = {**(headers or {}), **_protection_headers(url)}
    req = request.Request(url, headers=safe_headers, method=method)
    opener = request.build_opener(_NoCrossOriginRedirect())
    try:
        with opener.open(req, timeout=12) as response:
            return response.status, response.read(8192).decode("utf-8", "replace"), {
                key.lower(): value for key, value in response.headers.items()
            }
    except error.HTTPError as exc:
        return exc.code, exc.read(8192).decode("utf-8", "replace"), {
            key.lower(): value for key, value in exc.headers.items()
        }


def checks(frontend: str, api: str, fetch=inspect) -> list[dict]:
    cases = (
        ("frontend", frontend + "/", "GET", {}, lambda s,b,h: s==200 and
         ("html" in h.get("content-type","").lower() or "<html" in b.lower())),
        ("spa_deep_link", frontend + "/orders", "GET", {},
         lambda s,b,h: s==200 and
         ("html" in h.get("content-type","").lower() or "<html" in b.lower())),
        ("api_liveness", api + "/api/v1/health", "GET", {},
         lambda s,b,h: s==200 and json.loads(b).get("status")=="ok"),
        ("postgres_readiness", api + "/api/v1/ready", "GET", {},
         lambda s,b,h: s==200 and json.loads(b).get("status")=="ready"),
        ("configured_cors", api + "/api/v1/auth/login", "OPTIONS", {
            "Origin": frontend, "Access-Control-Request-Method": "POST",
        }, lambda s,b,h: s in (200,204) and
         h.get("access-control-allow-origin")==frontend),
        ("orders_auth_guard", api + "/api/v1/purchase-orders", "GET", {},
         lambda s,b,h: s==401),
        ("trust_lab_auth_guard", api + "/api/v1/trust-lab/scenarios", "GET", {},
         lambda s,b,h: s==401),
    )
    outcomes = []
    for name,url,method,headers,verify in cases:
        try:
            status,body,response_headers = fetch(url,method=method,headers=headers)
            good = bool(verify(status,body,response_headers))
            outcomes.append({"check":name,"status":"PASS" if good else "FAIL",
                             "http_status":status})
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            outcomes.append({"check":name,"status":"FAIL",
                             "error_type":type(exc).__name__})
    return outcomes


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description="Public HTTPS judge deployment smoke check")
    parser.add_argument("--frontend",required=True,help="public frontend HTTPS origin")
    parser.add_argument("--api",required=True,help="public backend HTTPS origin")
    args=parser.parse_args(argv)
    try:
        frontend=exact_https_origin(args.frontend)
        api=exact_https_origin(args.api)
    except ValueError as exc:
        parser.error(str(exc))
    results=checks(frontend,api)
    passed=sum(row["status"]=="PASS" for row in results)
    print(json.dumps({
        "scope":"read_only_hosting_and_auth_guards",
        "provider_payment_tested":False,
        "checks":results,"passed":passed,"total":len(results),
        "overall":"PASS" if passed==len(results) else "FAIL",
        "note":"Not proof of real Channel3, Gemini, PayPal buyer approval, capture or webhook delivery.",
    },indent=2))
    return 0 if passed==len(results) else 1


if __name__=="__main__":
    raise SystemExit(main())
