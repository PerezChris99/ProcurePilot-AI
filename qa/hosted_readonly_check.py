#!/usr/bin/env python3
"""Read-only hosted ProcurePilot API probe. Does not create accounts or payments."""
from __future__ import annotations

import argparse
import json
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

PATHS = (
    "/api/v1/health",
    "/api/v1/ready",
    "/api/v1/auth/me",
    "/api/v1/trust-lab/scenarios",
)


def validated_origin(origin: str) -> str:
    url = urlsplit(origin)
    if (
        url.scheme != "https" or not url.hostname
        or url.username or url.password or url.query or url.fragment
        or url.path not in ("", "/") or url.port not in (None, 443)
        or url.hostname in ("localhost", "127.0.0.1", "::1")
    ):
        raise ValueError("Use a public HTTPS origin with no credentials, port, path or query")
    return "https://" + url.hostname.lower()


def inspect(origin: str) -> dict:
    base = validated_origin(origin)
    expected = {
        "/api/v1/health": 200,
        "/api/v1/ready": 200,
        "/api/v1/auth/me": 401,
        "/api/v1/trust-lab/scenarios": 401,
    }
    result = {"origin": base, "scope": "GET-only, no accounts or payments", "checks": []}
    for path in PATHS:
        req = Request(base + path, method="GET", headers={
            "Accept": "application/json",
            "User-Agent": "ProcurePilot-ReadOnly-HealthProbe/1.0",
        })
        try:
            with urlopen(req, timeout=12, context=ssl.create_default_context()) as resp:
                code, headers = resp.status, resp.headers
        except HTTPError as error:
            code, headers = error.code, error.headers
        except (URLError, TimeoutError, OSError) as error:
            result["checks"].append({"path": path, "transport_error": type(error).__name__})
            continue
        result["checks"].append({
            "path": path,
            "status": code,
            "vercel_request_id": headers.get("x-vercel-id"),
            "vercel_error_code": headers.get("x-vercel-error"),
            "content_type": headers.get("content-type"),
        })
    result["expected"] = expected
    result["all_passed"] = len(result["checks"]) == len(PATHS) and all(
        row.get("status") == expected[row["path"]] for row in result["checks"]
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", default="https://procurepilotai.vercel.app")
    args = parser.parse_args()
    try:
        result = inspect(args.origin)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
