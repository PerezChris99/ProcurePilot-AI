# QA — run and verify ProcurePilot AI

**For evaluators and maintainers** · [Main README](../README.md) · [1:59 demo](../docs/DEMO_CHEAPEST_WRONG_PRODUCT.md) · [Judge access](../docs/JUDGES_START_HERE.md)

The local suite checks source behavior **without spending real money or calling live providers**. Passing it is not proof that production services or external Sandbox capture work.

## One-command test run (Windows)

Requires **Python 3.12+**, **Node 22.12+** (or 20.19+), npm and dependencies. From the repository root:

~~~powershell
.\qa\setup.bat        # First time only
.\test-all.bat        # All local gates
~~~

Alternative: `.\qa\run-all.bat`. Reports are written to ignored `qa/reports/summary.md` and `qa/reports/summary.json`. A failed gate returns a nonzero exit code.

~~~mermaid
flowchart TD
    A["Run test-all.bat"] --> B["Python syntax + Pytest"]
    B --> C["Isolated SQLite migrations"]
    C --> D["Node + ESLint + Vitest"]
    D --> E["API/security deployment contracts"]
    E --> F["Strict Vite production build"]
    F --> G["Asset/route checks + QA report"]
    G --> H{"All 9 gates pass?"}
    H -->|No| R["Investigate; do not claim release ready"]
    H -->|Yes| I["Continue to independent hosted/live checks"]
~~~

**Coverage includes:** authentication, user ownership, purchasing policy, Channel3/AI boundaries, orders, approvals, PayPal capture logic, signed-webhook validation paths, Decision Passport, frontend navigation and deployment contracts. Database migration tests use **temporary SQLite**, not the production Neon database.

For targeted runs:

~~~powershell
.\test-all.bat --only backend
.\test-all.bat --only frontend
.\test-all.bat --only migrations
.\test-all.bat --fail-fast
~~~

## Verify the deployed application separately

~~~powershell
python .\qa\live_demo_check.py --frontend https://procurepilotai.vercel.app --api https://procurepilotai.vercel.app
~~~

The **seven read-only hosted gates** cover public pages, API health/database readiness, CORS and protected-route behavior. Then separately test **actual** Channel3 results, the genuine Gemini/ADK response, an authorized Personal-buyer PayPal Sandbox checkout, server-validated capture and signed-webhook receipt if claimed.

| Test layer | What it establishes | Does **not** establish |
| --- | --- | --- |
| Local 9-gate suite | Code/build/regression and isolated DB behavior | Live-provider availability or merchant payments |
| Hosted 7-gate probe | Accessible HTTP routes and readiness at check time | Real AI/catalogue responses or a completed checkout |
| Manual provider and Sandbox run | Observed third-party integration and test-capture evidence | Retailer settlement, fulfillment or production-money support |

## Protect environments and evidence

- Never commit `.env`, API keys, passwords, Sandbox buyer credentials or `qa/reports` logs.
- A successful Vercel build is not a substitute for current QA or a full browser checkout.
- Use [release acceptance](../docs/RELEASE_READINESS.md), [detailed testing](../docs/testing.md), [integration verification](../docs/INTEGRATION_ACCEPTANCE.md) and [Neon/Vercel runbook](../docs/VERCEL_NEON_DEPLOYMENT.md) for staging, migrations, protected previews and reproducible diagnostics.

**Status — 10 November 2026:** GitHub confirms a successful Vercel deployment of commit `db3cd787`. The solo creator reports a completed Sandbox test transaction and submitted Devpost entry. A fresh **current-commit** 9/9 QA run, 7/7 live probe and signed-webhook delivery require separate proof; no result is fabricated here.
