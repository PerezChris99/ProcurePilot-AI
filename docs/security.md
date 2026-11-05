# Security posture and threat model

**Status: 4 November 2026 — Hackathon prototype, not production-certified.** This document distinguishes source controls from external/infrastructure controls and known omissions.

## Assets, threats, and trust boundaries

| Boundary | Implemented protection | Remaining risk |
| --- | --- | --- |
| Passwords | Argon2id hashing, generic login failure and shared Redis throttling for public login/registration | Redis/edge deployment, reset, email verification and MFA remain external/additional |
| JWT access tokens | Signature, audience, issuer, exp/nbf/iat, UUID subject, bounded lifetime and active-user lookup | Frontend sessionStorage XSS exposure; no revocation/refresh rotation |
| Procurement resources | Authenticated owner SQL filters, restricted approval states | Owner-scoped workspace with optional assigned independent reviewer; no organization-wide RBAC |
| Catalogue offers | Pydantic parsing, matching currency, explicit stock, HTTPS URLs, server-frozen prices | Supplier claims can be stale or misleading; shipping not verified |
| AI inputs/outputs | Small allowlisted evidence packet, one capped ADK call, no action tools, atomic call quotas | LLMs can hallucinate or misinterpret untrusted supplier titles |
| PayPal Orders v2 | Backend OAuth, idempotency keys, remote ID/custom ID/amount/currency and capture verification | Not proven safe under all races or network-unknown outcomes |
| Webhooks | PayPal verification API, unique event IDs, capture comparison, reduced stored payload | Need actual HTTPS signature tests, out-of-order and concurrency coverage |
| Hosting and persistence | .env ignored, bounded DB pools/timeouts, API defensive headers/HSTS in production, composite read indexes and migration 0005 UNIQUE provider IDs | No verified general edge rate limits, frontend CSP, backup-restore, WAF, monitoring or real load qualification |
| Source repository | Copyright / MIT open-source license | Public reuse is permitted under standard MIT terms; third-party service and trademark rights are separate |

## Authentication and authorization

- Argon2id hashes passwords. The FastAPI dependency verifies JWT signature and expiration, looks up the authenticated user and rejects inactive accounts.
- Procurement requests, orders and the pending-approval queue are scoped to the owner in SQL.
- The Approvals page records human decisions. The personal workspace permits self-approval by default; an explicitly assigned **distinct registered reviewer** may approve or reject only that assigned order and cannot operate the owner's payment flow. This is not organization-level independent role governance.
- Audience-scoped short-lived bearer tokens live in sessionStorage. Explicit logout removes the browser token, but it does not revoke a previously issued JWT server-side. Password recovery, email verification and multi-device sessions are not implemented.

## Procurement/payment correctness

- Browser-supplied prices, totals or currencies cannot determine a purchase-order amount. The backend freezes selected Channel3 offer details, calculates line totals, checks currency, budget, stock and HTTPS URL.
- A purchase order must be human-approved before PayPal Sandbox checkout.
- PayPal Orders v2 calls run server-side with restricted official PayPal API and approval hosts and stable idempotency keys.
- Capture validates remote order ID, custom ID, amount, currency, completed capture status and final captured amount before changing order state.
- Signed webhook verification uses PayPal's verification endpoint. Event IDs are unique; conflicting capture IDs and mismatched values are not accepted as new payment evidence.
- **Residual risk:** Checkout initiation, capture and webhook handlers still need stronger cross-worker transaction locking, reconciliation after network-unknown results, refund/dispute workflows, and adversarial tests of delayed events. A Sandbox capture does not settle funds to Channel3 retailers.

## AI threat model and cost enforcement

- Procurement ranking, price validation, approvals and payments are deterministic. Gemini advice is never purchase authority.
- Normal analysis: at most **one** ADK model call, **900 output tokens** by default, **35-second** wall-time limit, and **four** shortlisted products. The normal analyst has zero action tools.
- Catalogue titles are clipped and encoded inside a short data packet. Product descriptions, arbitrary attributes, images and tracking URLs are not forwarded to the normal analysis model. Untrusted text is explicitly marked data, not instructions.
- Exact repeated assessment requests are cached until catalogue refresh; verified empty results spend no model tokens.
- Database-level UTC-day allowance: 12 user calls and 100 global calls by default, reserved atomically before external model invocation. Failed/ambiguous calls still count to prevent budget bypass. Shared Redis throttling is implemented for login/registration in staging/production, but limits for ALL other routes require ingress/edge policy and further application controls.
- Model prompts and small evidence packets reduce but do not eliminate prompt injection, hallucination, model bias, or unsafe output. Provider usage metadata can be recorded, but the budget is a **call ceiling**, not a guaranteed monetary bill.

## Secrets and deployment

- Keep DATABASE_URL, JWT_SECRET_KEY, GOOGLE_API_KEY, CHANNEL3_API_KEY, PayPal Client ID/Secret and webhook ID in backend/root environment variables. Never commit real .env files or place any secret in VITE-prefixed frontend variables.
- The authenticated integration-status endpoint exposes boolean configuration flags, model and environment; it does not expose secrets. **Configured does not mean a credential was validated by the provider.**
- CORS restricts public origins to FRONTEND_URL; local loopback aliases are development-only. JSON API responses now include no-store, nosniff, no-frame, no-referrer, restricted Permissions-Policy and API-only CSP; production responses set HSTS. Vercel/Netlify frontend CSP headers have been added but require deployed-browser confirmation and equivalent policy on other hosts, strict HTTPS edge configuration, WAF, rotation, monitoring and independent testing.
- Inspect Git history for leaked keys before sharing the repository. If exposed, revoke/rotate at the provider rather than simply deleting the file.

## Production blockers (not implemented)

1. Organization roles, invitations, independent approvers and segregation-of-duties rules.
2. Managed TLS Redis and correct trusted proxy configuration for the new public auth throttle; distributed edge/API rate limits for discovery, checkout and other endpoints.
3. Password recovery, verified email addresses, MFA and JWT revocation.
4. Stronger payment concurrency, retry/reconciliation, refunds and provider outage handling.
5. Live signed webhook delivery through public HTTPS with replay, duplicate, out-of-order and load tests.
6. Reproducible npm lockfile, dependency security scanning and pinned/approved Python dependencies.
7. Proven TLS termination and HSTS at the edge, verified frontend CSP hosting policy, WAF, secrets vault, encrypted backups, recovery drills, log retention and alerting.
8. Browser E2E, mobile viewport and load/security testing.
9. Confirm country-specific PayPal merchant receiving eligibility before any live money acceptance.
10. Verify GitHub detects the MIT license and all external third-party image/brand permissions before hackathon submission.

**Status boundary:** Source-written tests and a GitHub merge are not evidence that local Pytest, Vite, Windows startup, third-party credentials or PayPal Sandbox have passed. This is not PCI certification or a guarantee against vulnerabilities.

## Production startup configuration gate (November 2026)

When `APP_ENV=production`, application settings now reject known JWT signing-key placeholders, SQLite/uninstalled `postgresql://` driver defaults, and non-HTTPS or non-origin `FRONTEND_URL`. This is fail-closed configuration validation, not a guarantee that public DNS, PostgreSQL credentials, TLS termination, or PayPal webhooks are actually available. Configure `DATABASE_URL=postgresql+psycopg://...` and a public HTTPS frontend origin before deploying; local `APP_ENV=development` bootstrap is unchanged. A production frontend must also set its public API endpoint, `VITE_API_BASE_URL`, to the real HTTPS API URL at build time.

Production/staging APP_ENV is now normalized to lower case; unsupported values such as prod are rejected rather than silently bypassing the startup checks or exposing production API docs. The example local postgres:postgres database URL is explicitly rejected in a public environment. Local development remains unchanged.

## Hardening implementation update (November 2026)

- **API:** A pure ASGI guard caps inbound HTTP bodies (default 1 MiB), rejects bad Content-Length, adds defensive cache/content-type/frame/referrer/permission headers, strict CSP to API JSON and HSTS on production responses. Frontend CSP and edge controls remain a separate deployment task.
- **Authentication:** JWTs now require issuer, audience, expiration, issue/not-before timestamps and a valid UUID subject, with limited token length and 5–120 minute configurable lifetime. Previous JWTs lacking the new claims are deliberately invalidated: users must sign in again. Session revocation and MFA remain unimplemented.
- **Public abuse controls:** Login/register use Redis-backed atomic per-source and per-identity throttles, HMAC-obfuscated keys and fail-closed HTTP 503 when Redis is missing or unavailable in staging/production. The app requires a managed `rediss://` URL and a trusted proxy that supplies the correct `request.client` address. General API/edge WAF limits remain external.
- **Database:** Per-worker bounded SQLAlchemy PostgreSQL pool and query/lock/idle transaction timeouts; compound indexes in Alembic 0005 for actual owner/status/date reads; migration strengthens PayPal identifier uniqueness. Lean procurement metadata lists, optional legacy full list, keyset cursors and bounded order-list audit summaries prevent large unnecessary payloads.
- **Untrusted input/AI/payment:** Channel3 upstream responses are capped at 2 MiB, saved discovery to 120 products/request, finite money and numeric database range checks, and PayPal webhook event ID/type validation. The existing ADK one-call quota and absence of payment/approval tools remain intact.

All these are source changes with source-authored regression tests; **do not claim they passed on every platform or resisted a professional red-team exercise until actually executed**. Real checkout/webhook concurrency and reconciliation, organizations with separate approvers, high-load qualification, recovery and incident response are still outstanding. See [scaling and operations](scaling.md).


### Hackathon PayPal Sandbox-only safety

The PayPal client rejects the Live API host during credential checks and before any OAuth/order/capture call. A wrong live endpoint cannot make real payments while the UI declares Sandbox-only operation. This does not replace actual buyer-approval, amount-mismatch, concurrent capture or webhook validation tests.
