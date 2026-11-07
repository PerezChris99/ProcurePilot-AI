# ProcurePilot AI — Vercel + Neon hosting

This is a **deployment playbook**, not proof of a live functioning application.
Deployment scope: `PerezChris99/ProcurePilot-AI`, branch `main`, one
Vercel **Services** project (beta), with Vite React at `/` and FastAPI at
`/api/v1/*`. The repo root `vercel.json` is the source of truth for
the Vercel multi-service build. No GitHub Actions workflows are needed.

## Prerequisites and security gates

- Use the Vercel project under the intended team; review Hobby plan limits.
  Vercel Services beta must be available for that project.
- Use **Neon PostgreSQL** (a dedicated project / production branch),
  ideally provisioned via the **Vercel Marketplace Neon integration**.
  Connect it to the Vercel project. Run the database in a region near the
  Vercel Functions region; enable pooled connections for runtime and use
  a direct connection for migrations if required.
- Preserve public authentication throttling. After migration
  `0010_auth_throttles`, the API uses **atomic Neon PostgreSQL counters**
  when `RATE_LIMIT_REDIS_URL` is absent. Configured Redis (TLS `rediss://`)
  remains supported for higher traffic. Both paths fail closed if they cannot
  provide protection. Do not set `APP_ENV=development` to bypass safeguards.
- Configure all secrets **in the Vercel dashboard**, never in Git, logs,
  frontend `VITE_*` variables, or chat messages. Rotate any old leaked keys.
- The host must remain available for judging. Monitor credit/usage limits.

## Vercel project settings

| Setting | Value |
| --- | --- |
| Repo | `PerezChris99/ProcurePilot-AI` |
| Production branch | `main` |
| Root directory | Repository root (leave blank) |
| Framework preset | **Services** |
| Public API | Same-origin `/api/v1` |
| Vite build | `npm run build:deploy` inside frontend service |
| FastAPI entrypoint | `backend/main.py` → `app.main:app` |
| Python | 3.13 |

The top-level `vercel.json` routes `/api/*` first to FastAPI and then
`/*` to React. A frontend-service rewrite preserves SPA deep links
such as `/orders` and `/dashboard`. The existing security headers
are retained at the public ingress.

Set these environment variables in **Production** (and only scoped Preview
environments when using a separate, safe preview DB):

| Variable | Value or source |
| --- | --- |
| `APP_ENV` | `production` |
| `FRONTEND_URL` | `https://procurepilotai.vercel.app` (canonical production origin) |
| `VITE_API_BASE_URL` | `/api/v1` (same-origin; safe to expose in JS) |
| `DATABASE_URL` | **Secret**: Neon Postgres connection URI, with TLS; use a pooled URL at runtime and ensure psycopg 3 compatibility |
| `JWT_SECRET_KEY` | **Secret**: random, unique, at least 32 characters, not any development secret |
| `RATE_LIMIT_REDIS_URL` | Optional: Redis **TLS** URL, `rediss://...`; otherwise the app uses Neon PostgreSQL counters |
| `DB_POOL_SIZE` | `1` (start conservative for serverless) |
| `DB_MAX_OVERFLOW` | `1` |
| `PAYPAL_BASE_URL` | `https://api-m.sandbox.paypal.com` |
| `PAYPAL_CLIENT_ID` | **Secret**: Business Sandbox REST application's client ID |
| `PAYPAL_CLIENT_SECRET` | **Secret**: matching Business Sandbox REST application's secret |
| `PAYPAL_WEBHOOK_ID` | **Secret**: ID issued for the actual production HTTPS webhook |
| `GOOGLE_API_KEY` | **Secret**: Gemini API key |
| `CHANNEL3_API_KEY` | **Secret**: Channel3 key |
| `CHANNEL3_BASE_URL` | `https://api.trychannel3.com/v1` |
| `AI_MODEL` | Configured tested Gemini model |
| `AI_TIMEOUT_SECONDS` | `60` |

Keep backups' secrets optional: `GROQ_API_KEY` and
`OPENROUTER_API_KEY` are only necessary when those backup providers
are deliberately enabled.

**Neon variables:** the Marketplace may inject names such as
`POSTGRES_URL` or `DATABASE_URL`. FastAPI requires `DATABASE_URL`;
map the provider's **real** connection string under that name without
publishing it. The app normalizes `postgresql://` to
`postgresql+psycopg://`. Do not copy a local SQLite URL into Production.

## Migrations (must happen before user traffic)

The Vercel Function must **not** run Alembic on import or on every
request. Use the reviewed **direct Neon connection** on a trusted local machine
(on Windows, copy the Direct Neon URL first; the command securely reads the clipboard, then clears it):

```powershell
.\backend\.venv\Scripts\python.exe .\qa\initialize_neon.py
```

This applies `alembic upgrade head` without downgrading or resetting data,
then verifies database access, revision `0010_auth_throttles`, and all
required tables. Sanitized evidence is saved to ignored
`qa/reports/neon.json`. It is not a Vercel app-connectivity proof:
`/api/v1/ready` must also report 200 from the public domain.

Avoid committing a production connection URL or echoing it in logs.
The existing `/api/v1/ready` verifies database connectivity, the authentication counter migration and
required tables; `/api/v1/health` checks process liveness only.

## PayPal Sandbox

In PayPal Developer > Sandbox Apps & Credentials, use the **Business**
Sandbox REST application's Client ID + Secret. A separate **Personal**
Sandbox buyer signs in at checkout. After production domain exists,
register the webhook URL:

```text
https://procurepilotai.vercel.app/api/v1/webhooks/paypal
```

Subscribe to `CHECKOUT.ORDER.APPROVED`,
`PAYMENT.CAPTURE.COMPLETED`, and `PAYMENT.CAPTURE.DENIED`.
Copy its actual Webhook ID into `PAYPAL_WEBHOOK_ID` and redeploy.
An OAuth smoke PASS does not prove buyer approval or capture, and
`SELLER_RESTRICTION` must be resolved in the Sandbox merchant account.

## Acceptance and rollback

From repo root, once the site is online, execute:

```powershell
python .\qa\live_demo_check.py --frontend https://procurepilotai.vercel.app --api https://procurepilotai.vercel.app
```

All seven read-only checks must PASS. Then test registration/login,
real Channel3 discovery, AI analysis, required human approvals, PayPal
Sandbox separate-tab checkout, exact capture, signed and duplicate
webhooks, Decision Passport, and mobile/desktop deep links.
A frontend-only deploy is **not** a working full-stack deployment.

If deployment fails, inspect Vercel build/runtime logs. Do not declare
readiness, charge real users, disable rate limiting, or switch to Live
PayPal to force acceptance. Revert a failing deploy and preserve the
Neon database; migrations must be reviewed for rollback compatibility.
