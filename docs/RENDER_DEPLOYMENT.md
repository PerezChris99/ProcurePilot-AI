# ProcurePilot AI: Render deployment runbook

Status: configuration instructions, **not** proof of a successful live deploy.
This is a four-resource web application, **not** a Render Workflow. Do not put
third-party credentials, PostgreSQL URLs or JWT secrets in Git history.

## Stop before deployment: rotate exposed credentials

Any Google/Groq/OpenRouter/Channel3/PayPal credentials previously pasted into
a chat, shared log or public issue must be revoked and replaced in their
provider dashboards. Do not reuse the exposed values. In Render, paste only
their rotated replacements as secret Environment variables. Never import a
development .env with copied demo secrets or localhost URLs.

## 1. Provision the data services

Use one Render region (for example Frankfurt) for API, PostgreSQL and Key Value;
do not mix regions unnecessarily. Use persistent paid database capacity through
the hackathon judging period; free Render Postgres expires after 30 days.

- Render Postgres: name `procurepilot-db`, database `procurepilot`,
  PostgreSQL 17 (matching local migrations), private networking, backups.
- Render Key Value: name `procurepilot-kv`, private/internal networking,
  no public IP allowlist, `noeviction` policy so authentication limits are
  not silently evicted. Enable internal auth when offered.
- Copy Postgres **Internal Database URL** and Key Value **Internal URL**
  via Render's secure Dashboard. Do not put either URL in source control.

Render Postgres internal URL is typically `postgresql://...`. This app safely
normalizes it to `postgresql+psycopg://...` for psycopg 3. Render private Key
Value uses `redis://red-...:6379`; production validation permits this only
when `RENDER_SERVICE_ID` is present and the URL is for a private Render Key
Value endpoint on port 6379. Non-Render Redis must still use `rediss://` TLS.
Never use a public `redis://` endpoint.

## 2. Create the API (New -> Web Service, NOT Workflow)

| Setting | Value |
| --- | --- |
| Repository | `PerezChris99/ProcurePilot-AI` |
| Branch | `main` |
| Root directory | `backend` |
| Runtime | Python 3 |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health check | `/api/v1/health` |
| Pre-deploy (paid service) | `python -m alembic -c alembic.ini upgrade head` |
| Auto-deploy | Commit after initial acceptance |

Required API Environment variables (example values are NOT credentials):

| Key | Value |
| --- | --- |
| `APP_ENV` | `production` |
| `FRONTEND_URL` | Actual deployed React origin: `https://YOUR-STATIC-SITE.onrender.com` |
| `DATABASE_URL` | Actual Render Postgres **internal** URL |
| `RATE_LIMIT_REDIS_URL` | Actual Render Key Value **internal** URL |
| `JWT_SECRET_KEY` | New high-entropy random signing secret (at least 32 chars) |
| `GOOGLE_API_KEY` | Freshly rotated provider secret |
| `CHANNEL3_API_KEY` | Freshly rotated provider secret |
| `CHANNEL3_BASE_URL` | `https://api.trychannel3.com/v1` |
| `PAYPAL_CLIENT_ID` | Fresh Sandbox merchant client ID |
| `PAYPAL_CLIENT_SECRET` | Fresh Sandbox merchant secret |
| `PAYPAL_BASE_URL` | `https://api-m.sandbox.paypal.com` |
| `PAYPAL_WEBHOOK_ID` | Real webhook ID, after registering public HTTPS callback |
| `AI_MODEL` | `gemini-3.5-flash-lite` |
| `AI_FALLBACK_ENABLED` | `true` |
| `GROQ_API_KEY`, `OPENROUTER_API_KEY` | Rotated keys, optional; never required to start |
| `AI_TIMEOUT_SECONDS` | `60` (overall limit; provider attempts are more tightly bounded) |

Configure `PYTHON_VERSION` to a Render-supported Python 3.13.x (or tested
Python 3.12.x). Use a paid API instance for a judge-facing demonstration to
avoid free-instance idle spin-down.

**Migrations**: use Render's paid-instance pre-deploy command before exposing
the app. On a free service this command is unavailable: apply Alembic once
through a controlled connection to the production database before launching,
not by embedding migrations into the main build. Never silently point a live
deployment at the local Windows PostgreSQL instance.

Test API HTTPS URL `https://YOUR-API-HOST.onrender.com/api/v1/health`;
also inspect `/api/v1/ready` for DB readiness. A green health endpoint alone
does not certify external provider credentials or payment delivery.

## 3. Create the React UI (New -> Static Site)

| Setting | Value |
| --- | --- |
| Repository | `PerezChris99/ProcurePilot-AI` |
| Branch | `main` |
| Root directory | `frontend` |
| Build command | `npm install && npm run build:deploy` |
| Publish directory | `dist` |
| Environment variable | `VITE_API_BASE_URL=https://YOUR-API-HOST.onrender.com/api/v1` |
| URL rewrite | Source `/*`, destination `/index.html`, type **Rewrite** |

The strict deploy build rejects a localhost API address. Use the real HTTPS API
host before running the static build. After Render assigns a public Static Site
URL, set the backend's `FRONTEND_URL` to that exact HTTPS origin and redeploy
the API so CORS and PayPal return/cancel URLs agree.

## 4. Configure PayPal Sandbox, never Live

In the PayPal Developer dashboard create a Sandbox Business merchant REST app.
Its webhook HTTPS listener is:

`https://YOUR-API-HOST.onrender.com/api/v1/webhooks/paypal`

Register the appropriate checkout/order/capture event types and enter the
**actual** webhook ID. A webhook placeholder such as `value` is not valid.
Use a separate Sandbox Personal buyer to approve. Only the backend can create
and capture the Sandbox order; the browser redirects to PayPal only after
backend approval and a verified HTTPS checkout link.

## 5. Required acceptance before sharing Devpost URL

1. Rotate credentials, complete migrations, and confirm API + database readiness.
2. Register and sign in on the deployed frontend; check CORS and auth throttles.
3. Create a procurement request and discover real Channel3 products.
4. Confirm explicit sizes (e.g. 72-inch monitors) block wrong-sized screens,
   unknown-size listings and accessories; ineligible products cannot become POs.
5. Ask AI to analyze; verify Gemini and eligible backup selection. If all
   providers are rate-limited, check the honest rule-based catalogue response
   with a retry action. No non-AI response should be labelled a Gemini run.
6. Create one valid PO: only that offer's button should show Creating. Submit
   and record human approval before any PayPal checkout action.
7. Select Create PayPal Sandbox checkout. Verify same-tab redirect, approve
   with Sandbox Personal buyer, return, confirm capture and inspect the audit
   event and Decision Passport.
8. Verify signed webhook handling (including duplicate delivery), rejected
   checkout, invalid currency and missing provider credentials.
9. Test desktop/mobile browsers, page refresh on /dashboard and /orders,
   accessibility and navigation, including the home logo scroll.
10. Record a public demo video under three minutes and keep the deployment
    reachable for Devpost judging through December 15, 2026.

Local Windows verification before publishing:

```powershell
cd "D:\NEW PROJECTS\ProcurePilot-AI"
git switch main
git pull --ff-only origin main
.\test-all.bat
Get-Content .\qa\reports\summary.md
```

Provider smoke probes are optional and spend provider quota. Avoid repeated
calls to currently rate-limited free models. **No GitHub Actions workflows** are
required. The current production proof is incomplete until these gates and
the live Render/PayPal Sandbox acceptance actually pass.

References:
- https://render.com/docs/service-types
- https://render.com/docs/key-value
- https://render.com/docs/blueprint-spec
- https://render.com/docs/redirects-rewrites
- https://paypalaihackathon.devpost.com/rules
