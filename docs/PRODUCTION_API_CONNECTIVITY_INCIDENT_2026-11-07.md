# Production API connectivity incident — 2026-11-07

**System:** ProcurePilot AI, Vercel Services Vite frontend + FastAPI backend, Neon PostgreSQL 17.

**User-observed symptoms:** account registration fails, sign-in fails, browser sometimes reports `Cannot reach the ProcurePilot API`. Earlier hosted checks reported 500 on API paths. **Do not equate a successful Vercel build with a working API or mark this incident resolved until the HTTP acceptance gates pass.**

## 1. Findings, confidence, and impact

| Investigation | Observed evidence | Result |
| --- | --- | --- |
| Frontend transport | `frontend/src/services/api.js` previously defaulted to a localhost API whenever a build-time variable was missing. Its generic `TypeError` handler masked the underlying network/CORS/host problem. | **Confirmed code defect**; fixed to enforce same-origin `/api/v1` for production Vite builds, and explicit error types for transport and HTML routing failures. |
| Deployment configuration | Vercel Services project uses a checked-in `/api/(.*)` backend rewrite followed by frontend catch-all; this is consistent with the official Services routing model. | **Confirmed repository configuration**; routing at the actual Vercel edge still needs HTTP proof. |
| AI dependency isolation | FastAPI app import eagerly loaded `app.agents.runtime` and Google ADK from `app.api.procurement_requests`, even for login/registration/health. | **Confirmed import-graph defect**; fixed by deferring AI adapter import until the `/analyze` endpoint. |
| Neon pooling | `backend/app/core/database.py` sent `options=-c statement_timeout=... -c lock_timeout=... -c idle_in_transaction_session_timeout=...` at every psycopg connection, including Neon `-pooler` hosts. Neon documents that unsupported startup options are rejected by its transaction-mode PgBouncer. | **Confirmed pooled-compatibility defect**. Whether it was the active production outage cause depends on the masked Vercel `DATABASE_URL`; it is not yet proven to use `-pooler`. |
| Postgres errors outside auth | SQLAlchemy exceptions outside authentication endpoints were not explicitly mapped to a client-safe service-unavailable response. | **Confirmed diagnostic defect**; added central 503 + `Retry-After` without leaking raw SQL/DSNs. |
| Neon SQL management connector | Production Neon has role `procurepilot_owner`, but the connected SQL plugin is restricted to nonexistent role `owner`; staging does have `owner` and passed `SELECT 1`. | **Confirmed tooling authorization mismatch**, *not* evidence of the application's own database credentials being incorrect. Do not create a superuser or rotate production credentials blindly. |
| Vercel secrets and logs | Vercel exposed project/deployment metadata and sensitive env var **names**, not decrypted values. Team-scoped runtime logs returned 403. | **Unverified production secret values**, backend error stack and DB hostname. Permission grant required for deeper runtime tracing. |
| DNS/HTTP from this execution environment | Public Vercel URLs could not be reached (DNS resolution / unsupported external fetch). | **Unable to assert HTTP 200**, successful registration, or complete live provider workflow without an independent HTTP probe. |

## 2. Fixes on `perez`

1. `backend/app/api/procurement_requests.py`: AI SDK lazily imported by `/analyze`; core routes no longer require Google ADK initialization.
2. `backend/app/core/database.py`: detect genuine Neon `-pooler` hostnames; omit unsupported startup `options`; disable psycopg named prepared statements on pooled sessions; apply validated statement/lock/idle-transaction limits with one parameterized `set_config(..., true)` command on every transaction `BEGIN`. Direct PostgreSQL retains original startup timeouts. Credentials never enter diagnostics.
3. `backend/app/main.py`: global safe SQLAlchemy service-unavailable handler, HTTP 503, `Retry-After: 15`.
4. `frontend/src/services/api.js`: production always targets same-origin `/api/v1`; clearer network versus HTML-rewrite mismatch errors; no automatic retry for payment requests.
5. `frontend/scripts/validate-deploy.mjs`: deployment fails rather than compiling an external or localhost API base; requires `VITE_API_BASE_URL=/api/v1`.
6. Regression tests: `backend/tests/test_startup_isolation_and_db_outages.py`, `backend/tests/test_database_pool.py`, `frontend/src/services/api.test.js`, `frontend/scripts/validate-deploy.test.mjs`.
7. Vercel non-secret configuration was reset to the canonical origins: `FRONTEND_URL` production `https://procurepilotai.vercel.app`, `perez` preview `https://procurepilotai-preview.vercel.app`, and `VITE_API_BASE_URL=/api/v1` for both environments. These variables require redeployment.

## 3. Security and compatibility constraints

- No weakening `APP_ENV`, JWT enforcement, CORS, user authorization, payment approval, or database authentication in order to obtain a green smoke test.
- Do not pass a production Neon password to the browser, repository, CI logs, support tickets, or chat.
- Do not auto-create production users solely to make a health check pass. Use disposable *staging* users for write tests.
- The Neon pooled timeout fix preserves transaction-local limits without leaking them across PgBouncer clients and prevents protocol rejection on startup.
- The only warranted successful response claims are explicit 200/201/401/409 statuses obtained from live HTTP probes.

## 4. Verification matrix (must be updated with actual evidence)

| Gate | Command / proof | Current recorded state |
| --- | --- | --- |
| Unit/regression suite | `python -m pytest backend/tests -q` from supported environment and `npm test -- --run` inside frontend | **New tests authored; full suite not independently executed by this investigation** |
| Client build + contract | `cd frontend; npm run test:deploy-config; npm run build:deploy` with `VITE_API_BASE_URL=/api/v1` | **Needs current source/deploy evidence** |
| Backend liveness | `GET https://procurepilotai.vercel.app/api/v1/health` ⇒ 200 JSON | **Unverified** |
| Neon schema readiness | `GET https://procurepilotai.vercel.app/api/v1/ready` ⇒ 200 JSON | **Unverified** |
| Auth guards | Unauthenticated `/auth/me`, `/purchase-orders`, `/trust-lab/scenarios` ⇒ 401 JSON | **Unverified** |
| CORS | Same-origin OPTIONS `/auth/login` from production hostname ⇒ 200/204 | **Unverified** |
| All hosted probes | `python qa/live_demo_check.py --frontend https://procurepilotai.vercel.app --api https://procurepilotai.vercel.app` ⇒ 7/7 | **Unverified** |
| Staging write/read | `python qa/initialize_neon.py --smoke` with *staging* Direct TLS connection, then browser registration/login/JWT | **Unverified** |
| Production registration/login | Fresh owner-authorized account, duplicate conflict, sign out/sign in, /me, device refresh | **Unverified — do not claim fixed** |
| Full provider flow | Channel3 → bounded Gemini/ADK → deterministic approval → PayPal Sandbox buyer confirmation and verified capture → Decision Passport | **Unverified — requires explicit live test accounts** |

## 5. If hosted checks fail after deploy

- `/health` fails: inspect Vercel backend Services rewrite, Vercel runtime invocation and import failure categories; an HTTP 500 or 503 here precedes database queries and indicates backend bootstrap/routing.
- `/health` passes but `/ready` returns 503: inspect Vercel's backend `DATABASE_URL` privately, verify host, role `procurepilot_owner`, database `procurepilot`, TLS and pooling style, and confirm Alembic version `0010_auth_throttles` **on that same database**. Classify `OperationalError` vs missing table from private logs, never from user-facing secrets.
- `/health` is HTML or redirects: the top-level Vercel Services routing does not reach FastAPI, or deployment protection intercepts it.
- Browser `TypeError` but direct health/ready pass: inspect browser DevTools Network for exact Request URL, DNS/CORS, proxy/extension and cached JS; hard refresh after deployment. Production code should use same-origin `/api/v1`.
- Registration 503 while readiness 200: inspect the shared PostgreSQL auth-throttle migration and per-request SQL / pool acquisition errors.
- Auth 401 after refresh: confirm that server JWT keys are stable across the same deployment and that session storage/expired token handling is not reusing an old token.

**Do not mark resolved until the live checks and account workflow pass.** Vercel project READY means only that its build/deployment was accepted. Existing user data and PayPal Sandbox state must be preserved.
