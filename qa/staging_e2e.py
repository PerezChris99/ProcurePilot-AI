#!/usr/bin/env python3
"""Real E2E FastAPI/Neon checks, restricted to an isolated staging project."""
import json
import os
from pathlib import Path
import secrets
import sys
from verify_neon import connection_target

ROOT=Path(__file__).resolve().parents[1]
STAGING_HOST="ep-spring-silence-bc8oxuii.c-16.us-east-1.aws.neon.tech"
REPORT=ROOT/"qa"/"reports"/"staging-e2e.json"

def require_staging(url):
    hostname,database=connection_target(url)
    if hostname!=STAGING_HOST or database!="procurepilot":
        raise ValueError("Staging-only; production and unknown hosts refused")

def run():
    require_staging(os.environ.get("DATABASE_URL"))
    os.environ.update(APP_ENV="staging",
        FRONTEND_URL="https://procurepilotai-preview.vercel.app",
        JWT_SECRET_KEY=secrets.token_urlsafe(48),
        RATE_LIMIT_REDIS_URL="",GOOGLE_API_KEY="",GROQ_API_KEY="",
        OPENROUTER_API_KEY="",CHANNEL3_API_KEY="",PAYPAL_CLIENT_ID="",
        PAYPAL_CLIENT_SECRET="",PAYPAL_WEBHOOK_ID="",AI_FALLBACK_ENABLED="false")
    sys.path.insert(0,str(ROOT/"backend"))
    from fastapi.testclient import TestClient
    from app.main import app
    report={"scope":"isolated_staging_database","provider_payment_tested":False,"checks":[]}
    def check(name,response,expected):
        ok=response.status_code==expected
        report["checks"].append({"check":name,"status":"PASS" if ok else "FAIL",
                                 "http_status":response.status_code})
        if not ok: raise AssertionError("Unexpected HTTP status: "+name)
        return response.json()
    with TestClient(app) as api:
        check("health",api.get("/api/v1/health"),200)
        check("ready",api.get("/api/v1/ready"),200)
        check("auth_guard",api.get("/api/v1/auth/me"),401)
        suffix=secrets.token_hex(8)
        password=secrets.token_urlsafe(24)
        user={"email":"qa-"+suffix+"@example.org","full_name":"Staging QA Buyer","password":password}
        registered=check("register",api.post("/api/v1/auth/register",json=user),201)
        bearer={"Authorization":"Bearer "+registered["access_token"]}
        check("login",api.post("/api/v1/auth/login",json={"email":user["email"],"password":password}),200)
        profile=check("profile",api.get("/api/v1/auth/me",headers=bearer),200)
        if profile["email"]!=user["email"]:raise AssertionError("Wrong identity")
        integration=check("integrations",api.get("/api/v1/integrations/status",headers=bearer),200)
        if not integration["database"]["connected"] or not integration["database"]["schema_ready"]:
            raise AssertionError("Database integration not ready")
        payload={"request_text":"Two 27-inch monitors for the office training room",
                 "quantity":2,"budget":"500.00","currency":"USD"}
        created=check("create_request",api.post("/api/v1/procurement-requests",json=payload,headers=bearer),201)
        rid=created["id"]
        saved=check("persisted_request",api.get("/api/v1/procurement-requests/"+rid,headers=bearer),200)
        if saved["request_text"]!=payload["request_text"]:raise AssertionError("Not persisted")
        lab=check("trust_lab",api.get("/api/v1/trust-lab/scenarios",headers=bearer),200)
        if not lab["total"] or lab["passed"]!=lab["total"]:raise AssertionError("Policy results differ")
        second=check("second_register",api.post("/api/v1/auth/register",json={
            "email":"qa-review-"+suffix+"@example.org",
            "full_name":"Staging QA Reviewer","password":secrets.token_urlsafe(24)}),201)
        other={"Authorization":"Bearer "+second["access_token"]}
        check("denied_other_user",api.get("/api/v1/procurement-requests/"+rid,headers=other),404)
        own=check("isolation_list",api.get("/api/v1/procurement-requests",headers=other),200)
        if any(x.get("id")==rid for x in own):raise AssertionError("Cross-user leak")
    report["overall"]="PASS"
    return report

def main():
    report={"scope":"isolated_staging_database","provider_payment_tested":False,"overall":"FAIL"}
    try:report=run()
    except Exception as exc:report["error_category"]=type(exc).__name__
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return 0 if report["overall"]=="PASS" else 1
if __name__=="__main__":
    raise SystemExit(main())
