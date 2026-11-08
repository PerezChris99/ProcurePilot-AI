# Authentication speed optimization — 8 November 2026

**Purpose:** reduce hosted signup and sign-in latency without weakening Argon2id
password security, identity/source rate limits, Neon transaction safety, or
existing account/payment data.

## 1. Profiling and root cause

The source path in production before this change:

1. Browser POST /api/v1/auth/register or /login to Vercel FastAPI.
2. Shared authentication rate limit: PostgreSQL transaction sends **two sequential**
   `INSERT ... ON CONFLICT DO UPDATE ... RETURNING` statements, one for IP/source
   and one for HMAC(email)/identity.
3. Registration: SELECT user by email → Argon2 hash → INSERT user/COMMIT
   → explicit `db.refresh(user)` SELECT → JWT response.
4. Login: SELECT user by indexed email → Argon2.verify → JWT response.

Vercel and Neon are both in US East. Excess database round trips are a
reliable optimization opportunity, but their wall-clock contribution depends
on remote connection, pool, Vercel cold starts and actual query latency.

## 2. Implemented reductions

| Operation | Before | After | Savings |
| --- | --- | --- | --- |
| Shared source+identity auth throttle | 2 sequential network SQL UPSERT statements | 1 atomic multi-row UPSERT with both RETURNING counters | **1 fewer DB SQL statement per login/register attempt** |
| Successful registration response | Extra SELECT via `db.refresh(user)` after INSERT/COMMIT | `db.flush()` assigns UUID/timestamp, validates immutable response snapshot **before** successful commit; no refresh after | **1 fewer post-commit SELECT** |
| Successful sign-in | Existing indexed user lookup + Argon2 verification | Same, no hashing-strength reduction | Security unchanged |
| Denied throttle | Every attempted request commits incremented counters | Same, both bucket limits enforce before acceptance | Security unchanged |

The practical reduction is **two unnecessary remote database statements for
registration** and **one for login**. This is not a claim that total login is
twice as fast. Time still includes high-cost, deliberate Argon2 verification,
cold start, TLS handshake, Neon server processing and frontend work.

## 3. Tested evidence and boundaries

- **Standalone SQLAlchemy/SQLite execution** with real SQL compiler: three
  simulated authentication attempts executed exactly three batched UPSERT
  statements, updating both counters from 1→2→3; no missing counters.
- Automated repository regression tests authored for 8/min identity, 120/min
  source, expired window reset, committed denied attempts, missing limiter
  migration 503, and registration correctness without a post-commit refresh.
- **Real staging Neon / Vercel Preview acceptance:** deployment
  `dpl_C8bcQ9WgAzi8tMjmfruEbVopV7TM` at SHA `4334437` reached READY
  after real staging signup **201**, login **200**, JWT /me **200**,
  procurement creation **201**, FastAPI health/readiness **200**, and an
  instrumented SQLAlchemy event asserted **exactly one auth-throttle INSERT
  statement for registration and one for login**. Independent staging Neon
  SQL: Alembic revision `0010_auth_throttles`, zero leftover test users,
  zero leftover test requests.
- **Preview test tooling limitation:** the optional pytest runner was not
  installed in Vercel's backend build environment (safe code 73), so pytest
  was removed from that build and replaced with the real staging SQL-backed
  acceptance gate. Do not describe this as a passing full pytest suite.
- **Still not measured:** current live browser p50/p95 login/signup time, first cold serverless invocation and JS chunk-to-interactive timing. The batched SQL and registration snapshot improvements have already been merged into the live source baseline; this document must not describe them as an unmerged branch candidate.

## 4. Fast judge-entry frontend pass (8 November)

The application previously imported the entire authenticated page tree, including procurement, order views and Recharts-based screens, on the initial sign-in/register route. The revised React app keeps **LoginPage** and **RegisterPage** eagerly available while deferring unrelated public and authenticated screens through `React.lazy` and `Suspense`. Only the destination workspace route plus its shell are prefetched after the person submits the login or registration form; that download overlaps the same backend POST and adds **no server/provider API calls**. Normal React Router navigation and the PayPal `/orders?paypal=return&po=...` redirect remain intact.

A labelled **indeterminate progress bar** immediately appears while credentials are checked or a new workspace is committed. Session restoration and delayed route chunk loading also show an explicit pending state. There are no fake percentages or artificial waiting delays; animation respects reduced-motion preferences. Failed authentication continues to show the actual backend error rather than a fabricated success screen. The final homepage footer credits the developer below the existing photography source link.

**Limits:** Frontend splitting cannot make Argon2 verification, remote Neon database transactions or Vercel cold starts instantaneous. No p50/p95 reduction or bandwidth savings figure is claimed until measured on the same network. Route loading may involve a small additional code request but substantially reduces unnecessary initial module evaluation.

**Verification before next rollout:** `frontend/src/App.test.jsx`, `components/ui/AsyncProgress.test.jsx` and `components/layout/PublicFooter.test.jsx` now cover asynchronous navigation, progress semantics and footer link placement. Run `./test-all.bat` and a strict Vite production build, then inspect the login/register Network waterfall (downloaded JS, time to interactive, POST duration, post-auth route time). A slow backend needs separate timing analysis; a progress bar only communicates that work is ongoing.

**Deployment hold:** The current Vercel team reported HTTP 402 `api-deployments-free-per-day` after exceeding 100 deployments in 24 hours. The user requested no further deployment attempts until the quota period has elapsed. Source changes can be committed/merged meanwhile without claiming they are already visible on the production domain.

## 5. Browser A/B benchmark (same device and network)

1. Open Chrome DevTools → **Network**, enable **Preserve log**, hide sensitive
   request payloads in screenshots, and avoid sharing bearer tokens.
2. Record `/api/v1/auth/login` and `/api/v1/auth/register` duration
   and server waiting/TTFB; distinguish cold first-hit from warm requests.
3. Test a fresh disposable Preview account, then use the same network/browser
   for Production **only after approved rollout**. Do not create multiple
   production accounts to benchmark.
4. Keep auth attempt limits: no more than **8 attempts/min per identity**.
   Space attempts across windows instead of temporarily disabling throttling.
5. Record response statuses, network timing, redirects, errors and dashboard
   usable time; sample enough requests to estimate median and p95.
6. Only claim a numerical speed-up after saving both baseline and candidate
   latency samples. A successful build and lower SQL query count alone do not
   prove specific milliseconds saved.

## 6. Release and rollback

- The code is on existing `perez`; no new branch or GitHub Actions.
- Do not merge `perez` until the current full offline QA checks pass and
  the owner approves the Preview release.
- On production release, confirm source SHA, 200 health/ready, new-account 201,
  valid login 200, incorrect login 401, rate-limit 429, existing account
  password verification and purchase state unaffected.
- Preserve the ability to revert this isolated performance commit if timing
  or counter behavior regresses. Never disable Argon2 or distributed throttling.

See [master checklist](SUBMISSION_READINESS.md) and
[winning execution plan](WINNING_EXECUTION_PLAN_2026-11-08.md).
