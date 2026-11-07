# Judges — start here

**ProcurePilot AI · Every Purchase Has a Reason**

This page is an honest route to inspecting or exercising the application in the
[PayPal AI Hackathon](https://paypalaihackathon.devpost.com/). It distinguishes
the no-credentials **offline preview** from a **real integrated Sandbox run**.

## Route A: Hosted experience (preferred after 7/7 acceptance)

The configured frontend URL is **https://procurepilotai.vercel.app** (Vercel
Services frontend and FastAPI; Neon PostgreSQL). The landing page and SPA
routing passed a public HTTP probe, but the last maintainer-reported probe
still showed **HTTP 500 on five API checks**. A successful Vercel build is not
proof of full end-to-end availability. Re-run the seven-check public HTTPS probe
and publish judge credentials through secure submission instructions only
after **7/7 PASS** and successful provider acceptance.

A suitable hosted run must support registration/login, live Channel3
discovery, a real Google ADK Gemini analysis or disclosed model fallback,
eligible PO creation, human approval, PayPal **Sandbox** buyer approval and
explicit verified capture, plus Decision Passport export. No test real-world
merchant payment is claimed.

**Do not** put a Sandbox Personal test password, PayPal REST client secret,
JWT signing secret or API token in public docs, videos, issues or logs.

## Route B: One-command safe local preview — no provider secrets

Install:
- Git
- Python **3.12+**
- Node.js **22.12+** (or 20.19+) and npm
- An internet connection for one-time installation of dependencies

Windows PowerShell:

```powershell
git clone https://github.com/PerezChris99/ProcurePilot-AI.git
cd ProcurePilot-AI
.\judge-preview.bat
```

macOS/Linux terminal:

```bash
git clone https://github.com/PerezChris99/ProcurePilot-AI.git
cd ProcurePilot-AI
python3 judge-preview.py
```

The launcher uses **its own SQLite file** under `backend/`, migrates it,
installs backend and frontend packages, builds the UI first, then serves
`http://127.0.0.1:5173` and `http://127.0.0.1:8000`. No PostgreSQL server,
Redis, VS Code or real API keys are needed. It does **not** overwrite `.env`
or alter an existing PostgreSQL database. If you already installed the packages,
rerun with `--skip-install`. Ctrl+C stops the servers.

1. Open the frontend in the browser.
2. Choose **Get started** and register an account you own.
3. Open a second terminal in the same repository directory.
4. On Windows run `.\judge-preview.bat --seed-email YOUR_REGISTERED_EMAIL`,
   or on macOS/Linux `python3 judge-preview.py --seed-email YOUR_REGISTERED_EMAIL`.
5. Refresh **Product discovery** and open the explicitly marked
   `[OFFLINE SAMPLE]` request.
6. Inspect the 27-inch screen match, 24-inch specification rejection and
   out-of-stock listing. This sample cannot create payable POs or claim real
   stock, AI tokens or PayPal transactions.

**This route is an inspection preview**, not the complete functional
third-party demo required to prove live integration. Never present sample
catalogue entries or their explanation as live Channel3/Gemini responses.

## Route C: Full local provider run

The intended project needs **real, authorized test credentials**. Follow
[provider setup](provider-setup.md) and [integration acceptance](INTEGRATION_ACCEPTANCE.md).

- On Windows, the development launcher `start.bat` uses your configured
  root `.env`, applies migrations and starts the VS Code workspace tasks.
  The ordinary template uses local PostgreSQL; configure it first.
- On macOS/Linux, `./start.sh` uses a local SQLite development database
  when no root `.env` yet exists; `./start.sh --postgres` uses the
  PostgreSQL template. Both preserve an existing environment file.
- Supply rotated `CHANNEL3_API_KEY`, `GOOGLE_API_KEY` (optional fallbacks),
  `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET` and the Sandbox API host.
- For remote signature-verified PayPal webhooks, deploy a public HTTPS API
  and register its webhook ID. Localhost cannot receive PayPal deliveries.

### Live browser walkthrough (5 minutes)

1. Sign in and open **New procurement**.
2. Enter *Two 27-inch office monitors*, quantity **2**, USD, budget **1000**.
   This is an example request, not a fabricated inventory guarantee.
3. Select **Search products**. Inspect actual Channel3 product IDs, seller
   URLs and offer price. Note why an out-of-stock/wrong-sized item fails.
4. Select **Ask AI to analyze**. Review the evidence-grounded Gemini
   assessment and its actual attribution. When providers are unavailable,
   look for the accurately labelled **catalogue-only** fallback and retry.
5. Choose an **eligible** offer and click **Create PO**, then **Submit for
   approval**. Open **Approvals** and approve as the authorized reviewer.
   If a different approver was assigned, sign in as that registered reviewer.
6. In **Purchase orders**, click **Create PayPal Sandbox checkout**. A
   **separate browser tab** opens to the official PayPal Sandbox buyer flow;
   ProcurePilot remains open in the original tab. Sign in with the separate
   **Sandbox Personal buyer** (not your real PayPal, Developer Dashboard, or
   Sandbox Business merchant credentials). After approval, PayPal returns to
   the app in that checkout tab. Select **Confirm buyer approval & capture**;
   this explicit final action is never automatic. If popups are blocked,
   follow the saved order's **Open PayPal in new tab** link and sign in to
   ProcurePilot again if the return tab requires it.
7. Open the **audit timeline** and **Decision Passport**; inspect source
   evidence, frozen pricing, approval actor/timestamp and provider capture
   proof. Export the PDF if useful.

### Negative case worth watching

Ask for **72-inch monitors**. A 24-inch screen, an unknown-diagonal display
or a monitor stand must **not** be orderable simply because its price is
within budget. The request's hard specifications remain authoritative.

## Optional: reproduce twelve policy safeguards without spending money

While signed in, select **Open Decision Trust Lab** on Overview, then
**Run policy checks**. All twelve cases execute against the same deterministic
purchase eligibility and matching logic used by the API. One valid monitor
passes; eleven disallowed cases are rejected (including wrong specifications,
missing evidence, budget, merchant restrictions, unauthorized delegated
review and altered payment amounts). Inputs are explicitly synthetic: no
payment or third-party interaction is performed.

For a **real saved purchase order**, open its **Decision Passport** to inspect
the lowest eligible quote, the cheapest rejected same-currency listing with
its policy violation, approval events, and actual Sandbox status. Rejected
quotes are not called savings, and merchant settlement remains unverified.

## How to verify the repo

Windows PowerShell after dependencies are installed:

```powershell
.\test-all.bat
Get-Content .\qa\reports\summary.md
```

The maintainer reported all **nine offline gates passing before these recent updates** on Windows on
November 6, 2026. The local suite writes its report to ignored `qa/reports`;
it does not use live provider credentials, exercise real remote webhooks or
represent a hosted payment checkout. Source changes after that report require
the suite to be rerun.

When the public UI/API exists, run [the credential-free hosted readiness
checker](LIVE_HOSTING_ACCEPTANCE.md) to verify seven HTTPS, schema, CORS and
authorization gates. It does not prove external integration acceptance.

## What counts as a meaningful integration

| Piece | Verifiable behavior | What it does not imply |
| --- | --- | --- |
| Channel3 | Real product and HTTPS retailer offers, prices, stock and snapshots | A retailer purchase, fulfilled stock or confirmed delivery |
| Google ADK / Gemini | Short evidence-only analysis; bounded retries/failover and provider metadata | AI authority to create/approve/pay for orders |
| Human approval | Approved PO from signed-in authorized actor | Enterprise-wide independent procurement governance |
| PayPal Orders v2 | Sandbox OAuth, order creation, buyer approval, explicit capture, idempotency and amount checks | Production funds, a Channel3 retailer payout or real-world merchant receiving |
| Decision Passport | Frozen selection, alternatives, source timestamp, approval/payment audit and PDF | Guarantee that a vendor's catalogue statement was objectively true |

Documentation: [Architecture](architecture.md) · [Threat model](security.md) ·
[API](api.md) · [Devpost submission kit](HACKATHON_SUBMISSION_KIT.md) ·
[Render deployment](RENDER_DEPLOYMENT.md).

## Access through judging

The official rules require a freely accessible working project through the
judging period ending **December 15, 2026**. The entrant must ensure hosting
uptime, stable test-account access, required authorized Sandbox details,
application logs/monitoring, and an English-language demonstration video
under three minutes uploaded publicly to YouTube. The judges may evaluate the
project solely from its text and video, so the recorded journey must be real,
readable, truthful and complete.

**Private test access should be shared through the Devpost testing field or
an authorized private channel, not through GitHub.** Do not log or display
secrets when recording the video.
