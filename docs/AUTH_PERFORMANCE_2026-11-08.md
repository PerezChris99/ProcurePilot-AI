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
- **Not yet measured:** actual live browser p50/p95 auth time, first cold
  serverless invocation, JS bundle/route transition time. `main` does not
  include the optimization until owner approval and reviewed merge.

## 4. Browser A/B benchmark (same device and network)

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

## 5. Release and rollback

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
