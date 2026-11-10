# Release and judging acceptance — ProcurePilot AI

**Purpose:** A short, repeatable release procedure for the submitted solo project.  
[Main README](../README.md) · [Judge quick start](JUDGES_START_HERE.md) · [QA](../qa/README.md) · [1:59 demo](DEMO_CHEAPEST_WRONG_PRODUCT.md)

**Git workflow:** commit to existing `perez` → review one PR → merge into `main` → verify Vercel's exact deployed commit. **No new branches or GitHub Actions.** Keep preview/staging data separate from production.

~~~mermaid
flowchart LR
    A["perez: reviewed source"] --> B["Local 9-gate QA"]
    B --> C["Isolated preview + staging checks"]
    C --> D["PR merged to main"]
    D --> E["Vercel production deployment"]
    E --> F["7 hosted HTTP checks"]
    F --> G["Real-provider + Sandbox acceptance"]
~~~

## Three independent verification gates

| Gate | Command or evidence | What it proves |
| --- | --- | --- |
| **Local source (9)** | `.\test-all.bat` → `qa/reports/summary.md` | Python, frontend, migration, contract and build tests |
| **Database** | `python qa/verify_neon.py --output qa/reports/neon.json` using authorized private `DATABASE_URL` | TLS connection, current migration/schema readiness on the target DB |
| **Hosted HTTP (7)** | `python qa/live_demo_check.py --frontend https://procurepilotai.vercel.app --api https://procurepilotai.vercel.app` | Public page and API readiness, CORS and protected-route behavior |

**A build is not an end-to-end payment test.** After these checks, exercise a genuine Channel3 search, attributable Gemini/ADK analysis, authorized human approval, separate **Personal PayPal Sandbox buyer** authorization, explicit server-validated capture and signed webhook delivery **if claiming** live webhook proof.

## Safe release procedure

1. Pull the reviewed source on `perez` and run `.\test-all.bat`. Investigate failed gates rather than weakening them.
2. Check migrations with disposable or dedicated staging PostgreSQL first. Do not reset or seed the production database solely to force a green report.
3. Verify the protected Vercel preview with a **separate staging database**. Use a temporary, revocable deployment-protection bypass only if necessary; never store it in Git.
4. Merge a reviewed PR from `perez` into `main` once authorized. Confirm Vercel deployed the intended merge SHA.
5. Run the seven public hosted checks, then rehearse the genuine browser purchase and Decision Passport export using a dedicated Personal Sandbox buyer.
6. Inspect runtime errors, access control and data isolation. Keep the demo and judge credentials available through **15 December 2026**.

**Protected preview:** If Vercel requires authentication, supply its temporary `VERCEL_AUTOMATION_BYPASS_SECRET` only through a private terminal for the configured preview host; revoke it after testing. Do not send it to production or include it in logs, commits or screenshots.

**Database changes:** Follow [the Neon/Vercel runbook](VERCEL_NEON_DEPLOYMENT.md) and [detailed tests](testing.md) before touching production schema. Full provider acceptance guidance is in [integration checks](INTEGRATION_ACCEPTANCE.md).

## Current evidence boundary

As of **10 November 2026**, GitHub reports Vercel deployment of source commit `db3cd787` completed successfully. The solo developer reports a completed PayPal Sandbox transaction and a submitted Devpost entry. The **1:59 video duration is supplied by the creator**. None of these reports substitute for a freshly executed current-commit 9/9 local suite, 7/7 public probe or independently observed signed webhook.

**Scope:** PayPal Sandbox uses virtual money; no real Channel3 retailer payment, supplier order or fulfillment is created. Keep that distinction visible in the README, demo and judge materials.
