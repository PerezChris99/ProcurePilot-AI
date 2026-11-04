# Security posture and threat model

**Status: 4 November 2026 — Hackathon prototype, not production-certified.** This document distinguishes source controls from external/infrastructure controls and known omissions.

## Assets, threats, and trust boundaries

| Boundary | Implemented protection | Remaining risk |
| --- | --- | --- |
| Passwords | Argon2id hashing and generic login failure | Missing distributed auth rate limiting, reset, verification and MFA |
| JWT access tokens | Signature/expiry check, active-user lookup, user-scoped data | Frontend sessionStorage risks under XSS; no revocation/refresh rotation |
| Procurement resources | Authenticated owner SQL filters, restricted approval states | Personal single-user demo; no organization RBAC or independent approvals |
| Catalogue offers | Pydantic parsing, matching currency, explicit stock, HTTPS URLs, server-frozen prices | Supplier claims can be stale or misleading; shipping not verified |
| AI inputs/outputs | Small allowlisted evidence packet, one capped ADK call, no action tools, atomic call quotas | LLMs can hallucinate or misinterpret untrusted supplier titles |
| PayPal Orders v2 | Backend OAuth, idempotency keys, remote ID/custom ID/amount/currency and capture verification | Not proven safe under all races or network-unknown outcomes |
| Webhooks | PayPal verification API, unique event IDs, capture comparison, reduced stored payload | Need actual HTTPS signature tests, out-of-order and concurrency coverage |
| Hosting and persistence | .env excluded from Git, backend-only secrets, bounded provider timeouts, Alembic migrations | No verified edge rate limits, CSP/HSTS, backup-restore, WAF or monitoring |
| Source repository | Copyright / authorized-use license | GitHub visibility was reported public; public visibility is not an open license |

## Authentication and authorization

- Argon2id hashes passwords. The FastAPI dependency verifies JWT signature and expiration, looks up the authenticated user and rejects inactive accounts.
- Procurement requests, orders and the pending-approval queue are scoped to the owner in SQL.
- The Approvals page now exists and records user decisions. **The signed-in requester may approve their own purchase in this personal-workspace prototype**. This is not true separation of duties and should not be advertised as independent maker-checker approval.
- Short-lived bearer tokens live in sessionStorage. Explicit logout removes the browser token, but it does not revoke a previously issued JWT server-side. Password recovery, email verification and multi-device sessions are not implemented.

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
- Database-level UTC-day allowance: 12 user calls and 100 global calls by default, reserved atomically before external model invocation. Failed/ambiguous calls still count to prevent budget bypass. Rate limits on ALL HTTP requests are **not** implemented.
- Model prompts and small evidence packets reduce but do not eliminate prompt injection, hallucination, model bias, or unsafe output. Provider usage metadata can be recorded, but the budget is a **call ceiling**, not a guaranteed monetary bill.

## Secrets and deployment

- Keep DATABASE_URL, JWT_SECRET_KEY, GOOGLE_API_KEY, CHANNEL3_API_KEY, PayPal Client ID/Secret and webhook ID in backend/root environment variables. Never commit real .env files or place any secret in VITE-prefixed frontend variables.
- The authenticated integration-status endpoint exposes boolean configuration flags, model and environment; it does not expose secrets. **Configured does not mean a credential was validated by the provider.**
- CORS restricts allowed origins to FRONTEND_URL in source. Deploying securely still requires HTTPS termination, headers, WAF/abuse controls, monitoring, rotation and independent checks.
- Inspect Git history for leaked keys before sharing the repository. If exposed, revoke/rotate at the provider rather than simply deleting the file.

## Production blockers (not implemented)

1. Organization roles, invitations, independent approvers and segregation-of-duties rules.
2. Durable distributed request rate limiting for auth, discovery, checkout and other endpoints.
3. Password recovery, verified email addresses, MFA and JWT revocation.
4. Stronger payment concurrency, retry/reconciliation, refunds and provider outage handling.
5. Live signed webhook delivery through public HTTPS with replay, duplicate, out-of-order and load tests.
6. Reproducible npm lockfile, dependency security scanning and pinned/approved Python dependencies.
7. TLS, CSP, HSTS, WAF, secrets vault, encrypted backups, recovery drills, log retention and alerting.
8. Browser E2E, mobile viewport and load/security testing.
9. Confirm country-specific PayPal merchant receiving eligibility before any live money acceptance.
10. Verify hackathon license rules: authorized-use LICENSE is proprietary, not OSI open source.

**Status boundary:** Source-written tests and a GitHub merge are not evidence that local Pytest, Vite, Windows startup, third-party credentials or PayPal Sandbox have passed. This is not PCI certification or a guarantee against vulnerabilities.
