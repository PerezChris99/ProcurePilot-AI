# Code audit and release verification — 2026-11-04

## Changes applied on perez
- Normalized Channel3 paginated search result envelopes and rejected malformed provider responses instead of silently returning empty lists.
- Hardened PayPal webhook nested-value handling and prevented conflicting capture IDs or altered local amount/currency from updating an already paid order.
- Moved PayPal Sandbox checkout to the same tab so browser sessionStorage authentication survives return for manual capture.
- Applied Alembic migrations automatically during Windows bootstrap and as a VS Code integrated startup prerequisite.
- Replaced static dashboard counts and activity with authenticated, user-scoped SQL counts and audit events.
- Batched purchase-order list details to remove the four-queries-per-order N+1 access pattern.
- Prevented frontend Create PO actions on offers with mismatched currencies, unknown stock, missing/invalid price, non-HTTPS URL or budget overrun.
- Added code-check helper and regression tests; improved user-facing validation errors and made provider readiness explicitly configuration-only.

## Required local gates: NOT YET VERIFIED
The GitHub connector can inspect and write source but cannot execute this Windows + PostgreSQL project or install the full backend/node dependency set. Do **not** claim tests, build, migrations or checkout passed solely because the source was committed.

1. Run `start.bat` on Windows with a working PostgreSQL 17 database and correctly configured root `.env` and verify integrated VS Code tasks actually launch both services.
2. Run `verify.bat` and confirm all backend pytest, frontend lint/Vitest and production Vite build checks pass.
3. Exercise new account/login, procurement creation, Channel3 real search, AI analysis, PO creation, submit/approve, PayPal Sandbox buyer approval, capture, webhook verification, replay, denial, and account-isolation tests with real credentials.
4. Test reloads, startup order, browser session persistence across PayPal return, multi-tab sessions, and browser navigation.
5. Configure a real public HTTPS webhook endpoint and registered Sandbox webhook ID, then inspect actual delivery logs.

## Architectural boundaries still outstanding
- Self-approval is allowed for the demo's user-scoped workflow; true independent multi-actor approval needs organization roles and policies.
- No durable distributed authentication rate limiter, password reset, email verification or operational observability is implemented.
- No verified backups/recovery, production monitoring, external PayPal merchant eligibility, retailer fulfillment or real settlement.
- The project has no tracked frontend package lock; reproducible dependency resolution is not established.
- Dashboard provider configuration indicators do NOT prove API key validity.
- GitHub Actions remain intentionally absent, per project policy.
- This is a hackathon prototype, not a certified production financial platform.

## Visibility check
GitHub repository metadata returned visibility=public during this audit. If it should remain private until hackathon submission, correct this through repository settings. Never commit credentials or local .env files.
