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


## 6. Execution evidence acquired during the incident

- **Staging PostgreSQL execution (PASS):** On the isolated Neon staging project, ran a single SELECT using `set_config('statement_timeout','9000',true)`, `set_config('lock_timeout','2500',true)`, and `set_config('idle_in_transaction_session_timeout','10000',true)`. PostgreSQL returned `9s`, `2500ms`, and `10s` respectively. The exact parameterized SQL is tested by unit assertions; this staging query was executed with literals only and made no durable changes.
- **SQLAlchemy BEGIN hook lifecycle (PASS):** A local SQLite-engine experiment confirmed an event listener can execute one SQL command on transaction begin without recursive begin; the committed backend test similarly verifies the application listener wiring.
- **Node deployment gate (PASS):** Twelve standalone Node tests of the committed same-origin URL validation logic passed; a non-same-origin URL was rejected with exit code 1. This was an isolated reproduction, **not** the full frontend `npm test` suite against an installed checkout.
- **Vercel Services Preview (READY):** New `perez` deployment `dpl_529NgvrXDkCnvpN8gK5qoLV6ZXZA` completed on commit `ab474436c79baa0d7aecf606dbe9104e9c008087`, and the preview alias was attached. READY is build/deploy evidence only. Later test-only commit(s) must be verified before final release.
- **Production HTTP and user transaction checks:** Still **NOT VERIFIED**. This environment's outbound public DNS/Web fetch fails, Vercel team-scoped runtime logs are denied pending authorization, and production Neon SQL queries are blocked by a role-pinned connector. No claim of 200/201/7-of-7 or working public sign-in is supported by the evidence.

### External reference

Neon connection troubleshooting: https://neon.tech/docs/connect/connection-errors — transaction PgBouncer may reject unsupported PostgreSQL startup parameters. This is the documented reason for moving connection timeouts to transaction-local SQL on Neon pooled hosts.


## 7. Forensic root cause and recovery — 7 November 2026 (follow-up)

### Confirmed startup blocker, isolated on live Vercel Preview build

- The backend's own Pydantic `Settings` validation failed with the deterministic release-gate category **`invalid_settings_jwt` (exit code 40)**. The public-production configuration rejects weak, empty, or templated `JWT_SECRET_KEY` values. This prevented FastAPI startup independently of database connectivity. The previous READY Vercel deployments did not execute this validation as a build gate.
- Rotated the Vercel **sensitive** `JWT_SECRET_KEY` environment variable for Production and Preview to a cryptographically random, high-entropy value (never logged, stored, or committed). This invalidates older tokens, intentionally requiring reauthentication.
- The first Alembic deployment-time gate reported exit 25; follow-up diagnostics exposed a bug in its own Pydantic model-error classification (empty `loc=()`). That diagnostic bug was corrected before proceeding. This chain is recorded to distinguish the underlying JWT error from instrumentation issues.

### Verified repair on isolated staging Neon and Vercel Preview

- Staging Neon SQL access works under its native `owner` role. A known-target, TLS-only, direct-connection build gate successfully upgraded the isolated staging schema from empty to the reviewed Alembic head `0010_auth_throttles`.
- Independent Neon queries verified `0010_auth_throttles` and all **11** required app tables.
- Vercel Preview build `dpl_HdCCwubyn2eUuTemDQ1d193KWZJS` finished **READY** with in-process FastAPI checks: `GET /api/v1/health = 200`, `GET /api/v1/ready = 200`, `GET /api/v1/auth/me = 401`, production-equivalent CORS, **POST registration = 201**, **POST login = 200**, JWT-authenticated user read = 200, and authenticated procurement request creation = 201. These are actual SQL-backed staging operations, not provider mocks.
- The disposable staging user and procurement request were removed in `finally`; independent staging SQL queries showed **0** matching residual users and **0** matching requests.
- The Vercel build validates the exact production vs staging Neon hostname, database and role, requires TLS, and refuses unknown or unversioned existing schemas. Forward migrations need the explicit `PROCUREPILOT_RUN_REVIEWED_MIGRATIONS=1` environment gate. No migration runs on a public API request.
- Existing Production was intentionally left unchanged while Preview diagnostics failed. `main` deployment and production schema verification are separate steps.

### Production release requirements

1. Production Vercel backend must have the intended `DATABASE_URL` for `ep-blue-band-bcjqtqrc.c-16.us-east-1.aws.neon.tech` (direct or pooled), role `procurepilot_owner`, database `procurepilot`, and `sslmode=require`. Do not log the full URI. **Do not use the staging database for production.**
2. A reviewed one-time migration gate (`PROCUREPILOT_RUN_REVIEWED_MIGRATIONS=1`) is enabled only during the release. The backend build must check the actual schema revision and run only known forward Alembic upgrades if needed; it then asserts live SQL and FastAPI health/readiness without creating production test users.
3. On successful deployment, set `PROCUREPILOT_RUN_REVIEWED_MIGRATIONS=0` in both environments so future deployment builds verify schema rather than silently applying future migrations. Likewise disable the Preview-only disposable auth smoke.
4. Confirm real public HTTP responses with `python qa/live_demo_check.py --frontend https://procurepilotai.vercel.app --api https://procurepilotai.vercel.app`, then register and sign in from the browser. In-process build checks are **not a substitute for external Vercel routing, DNS or browser verification**.
5. If the production build gate fails, its fixed exit code identifies the safe category (e.g., 22 wrong Neon target/role, 24 database connection, 40 weak JWT, 25 migration failure, 60 API import, 62 readiness). Investigate without weakening authentication or changing DB identities arbitrarily.

**External HTTP and production registration remain unverified until independently observed.**


## 8. Deployment and recovery evidence — post-merge on 7 November 2026

**GitHub:** PR #54 merged into `main` as `c21083849195a79c30e1b074ef127a62de6f2a6c` with the defended Vercel build gate and staging end-to-end tests.

**Production Vercel:** deployment `dpl_DNApTYnhRbzHieVxnuYacwew8nBD` was **READY** and assigned the canonical `procurepilotai.vercel.app` alias on that exact merge SHA. The backend release build executed with the newly rotated strong JWT secret and its production-specific Neon allowlist. A successful gate requires Pydantic Settings validation, Neon SQL connectivity, Alembic `0010_auth_throttles`, all 11 required tables, and in-process FastAPI GET health/ready 200, auth/me 401, and same-origin CORS checks. The production migration flag was explicitly enabled only for that release; it applies known forward revisions if necessary. **No production test users or payments were created.**

**Production Neon management confirmation:** the project's `ep-blue-band-bcjqtqrc` compute recorded new activity at `2026-11-07T18:11:51Z` with the compute active during the release. This independently corroborates actual production Neon use, rather than a build that never opened a database connection. The Neon SQL connector itself remains role-pinned to a nonexistent `owner` role, so an independent direct SQL `SELECT version_num` against production is still inaccessible from that specific connector. The Vercel backend gate performed the required SQL verification using the **application's** database role.

**Staging:** Preview deployment `dpl_HdCCwubyn2eUuTemDQ1d193KWZJS` was READY after real database-backed 201 registration, 200 login, 200 JWT /me, 201 procurement creation and read-only API guard/CORS checks. Independent Neon SQL showed revision `0010_auth_throttles`, all required tables, and no residual disposable test records.

**Post-acceptance controls:** the Vercel non-secret `PROCUREPILOT_RUN_REVIEWED_MIGRATIONS` switches were returned to `0` for Production and `perez` Preview; `PROCUREPILOT_STAGING_AUTH_SMOKE` was returned to `0`. Future builds retain a **read-only** schema/API readiness gate and will fail closed if schema is unexpectedly outdated rather than silently mutating a live database. Fresh deployments after those flag changes are the final configuration check.

**Outstanding distinction:** a Vercel READY result and in-process HTTP 200/201 do not prove that external browser requests traverse Vercel's public routing successfully. This execution environment cannot resolve the public hostname and the connected Vercel runtime-log API still denies access. Thus real public HTTPS /health, /ready and a user-driven browser sign-in remain to be observed before claiming complete outside-in recovery.

### Root-cause conclusion

The reproducible startup blocker was an **invalid/weak Vercel JWT secret** (diagnostic exit 40 from the same Pydantic Settings validation used by FastAPI). Its rotation removed the startup misconfiguration. The absence of a deployment-time Alembic gate meant freshly provisioned Neon databases could remain without the required authentication throttling schema; adding a narrowly controlled, verified forward-migration gate restored the isolated staging schema and established production schema-readiness checks. Both issues were addressed without bypassing security or modifying real payments.
