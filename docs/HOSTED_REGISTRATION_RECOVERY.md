# Hosted registration recovery — 7 November 2026

This is a **diagnostic runbook**, not evidence that production registration works.

## Confirmed from repository and connected services

- The public React frontend uses the same-origin FastAPI route `/api/v1` when `VITE_API_BASE_URL=/api/v1`.
- Registration is `POST /api/v1/auth/register`. On public deployments, the rate limiter must access either Redis or PostgreSQL, and the registration handler must access PostgreSQL `users`.
- `GET /api/v1/health` checks process liveness only; `GET /api/v1/ready` checks the database and current auth-limit schema. A green frontend or `health` alone is not acceptance.
- The production Neon project is `procurepilot-ai`, database `procurepilot`, with database-owner role `procurepilot_owner`. The Neon connector in this environment is pinned to a nonexistent `owner` role, so it cannot run SQL; **this does not by itself prove the website's DATABASE_URL is wrong**.
- The connected Vercel API returned 403 for runtime logs and 404 for the project-inspection call, so deployed configuration and the exact exception have **not** been inspected.
- `perez` carries the source change that returns sanitized HTTP 503 instead of a generic unhandled 500 when registration/login encounters an SQLAlchemy database failure. This change **does not repair an incorrect environment variable or broken network connection**.

## Resolve hosted infrastructure without weakening security

1. In the Vercel project for `procurepilotai.vercel.app`, inspect the **backend service**, root Services configuration, and latest production deployment. The root directory must be repository root, not `frontend/`; routes `/api/(.*)` must target the backend service before the frontend catch-all.
2. Check `APP_ENV=production`, `FRONTEND_URL=https://procurepilotai.vercel.app`, and `VITE_API_BASE_URL=/api/v1`. Confirm `JWT_SECRET_KEY` is a private random secret of sufficient length. Never print or commit it.
3. Check **backend runtime** `DATABASE_URL` points to the production Neon project and correct database/role, using TLS (`sslmode=require`). Use a pooled Neon URL when applicable. Do not confuse the separate empty staging Neon project with production. Compare the URL's hostname/username/database **inside the dashboard**, without copying the secret into logs or chat.
4. Ensure database migration `0010_auth_throttles` was applied to **that same production database** (not merely to a local or other Neon project). Run `python .\qa\initialize_neon.py` using a securely supplied direct production connection URL, in a trusted PowerShell session, if migration verification or upgrade is needed. It applies forward migrations and must be reviewed before running against live data.
5. In Vercel, review actual backend build/runtime logs for ASGI import errors, dependency failures, database connection errors, and rate-limiter failures. The root cause of an HTTP 500 cannot be established from the browser status code alone. Verify `backend/main.py` is the ASGI entrypoint.
6. Redeploy `perez` in Preview, then call the checks below. **Do not merge into main** until live gates and user approval.

## Read-only checks

```powershell
$origin = "https://procurepilotai.vercel.app"
Invoke-WebRequest "$origin/api/v1/health" -SkipHttpErrorCheck | Select-Object StatusCode,Content
Invoke-WebRequest "$origin/api/v1/ready" -SkipHttpErrorCheck | Select-Object StatusCode,Content
python .\qa\live_demo_check.py --frontend $origin --api $origin
```

Expected: health 200/ok, readiness 200/ready, and **7/7** acceptance. If health fails, fix the Vercel API service/build/import first. If health passes but ready returns 503, inspect database connectivity/migrations. Registration must not be tested destructively against production until these gates pass.

## Controlled E2E acceptance

Run `python .\qa\initialize_neon.py --smoke` with the **separate staging** Direct TLS Neon URL, not production, to exercise real migrations, registration/login, JWT authorization, procurement persistence, policy checks and cross-user isolation. The staging project must be initialized before smoke testing. Then test preview in a browser with disposable staging-only identities: register, sign in, refresh, sign out, sign in again, request creation, discovery and approvals; separately prove provider calls and PayPal Sandbox approval/capture with their proper test accounts. Capture sanitized reports only.

**Unverified as of this runbook:** Vercel backend access/configuration; actual deployed database connection; Neon production SQL introspection; preview registration; full live provider E2E; complete local QA. Keep submission and merge gates open.


## Follow-up diagnostics — 7 November 2026

- **Verified through Neon API:** Production project `snowy-star-53343423`, default branch `br-orange-voice-bcgnkby7`, database `procurepilot`, PostgreSQL role `procurepilot_owner`. The Neon SQL connector is pinned to `owner`, a role that does **not** exist in this production branch. This is specifically a **connector SQL authorization mismatch**, not proof that the deployed FastAPI's own PostgreSQL credentials are invalid.
- **Verified through direct Neon SQL:** The isolated staging project `patient-resonance-26359977` has a login role named `owner`. A `SELECT current_user, current_database(), 1` succeeded there. Staging currently has no application tables; a connection success does **not** mean app-readiness.
- **Neon security constraint:** The connected role-pin prevents creation of a least-privilege SQL role by `create_postgres_role(access='read_only')`. Do **not** create a `neon_superuser` administrator merely to satisfy the mismatched role name. Reauthorize the Neon connector with a correct production role or an explicitly approved role policy; SQL access cannot be repaired in GitHub source.
- **Vercel status:** The linked project `procurepilot-ai` exists and its framework is Services. Production `main` at `88e2bd8` and preview `perez` at `2a73fd7` were both recorded as built and READY. Project metadata and variable *names/targets* are available without forcing a team-scope selector. The variables `DATABASE_URL`, `FRONTEND_URL`, `VITE_API_BASE_URL`, and `APP_ENV` are **sensitive**, so their values are intentionally redacted in this connector view. Empty returned strings must **not** be interpreted as blank configuration.
- **Vercel log access:** Team-scoped runtime logs still report insufficient permissions. Obtain Vercel team access consent using the platform's authorize-team flow. Until an actual response body is read, record both `/api/v1/health` and `/api/v1/ready` as unverified, not 200.
- **Release rule:** Never change the deployed production DATABASE_URL to point at the empty staging database to make a connection probe pass. Do not grant unintended admin privileges or lower `APP_ENV` to development to mask a broken deployment.
