# API overview

Base path: /api/v1

## Public

- GET /health — process liveness, independent of database availability.
- GET /ready — checks database access and the required users/AI-budget schema; HTTP 503 if the database or latest required migration is unavailable. Point deployment readiness probes here instead of /health.
- POST /auth/register — create account and issue a bearer token.
- POST /auth/login — authenticate and issue a bearer token.
- POST /webhooks/paypal — public PayPal webhook receiver; every event is verified with PayPal before processing.

## Authenticated

- GET /auth/me — current user.
- GET /integrations/status — safe configuration indicators for PostgreSQL, Google Gemini, Channel3, and PayPal. Never returns credentials or webhook IDs; provider configuration does not prove credentials are valid.
- POST /procurement-requests — create request.
- GET /procurement-requests — list the current user's requests.
- GET /procurement-requests/{id} — retrieve an owned request.
- POST /procurement-requests/{id}/discover — retrieve and rank Channel3 products.
- POST /procurement-requests/{id}/discover?next_page=true — load the next saved Channel3 page token.
- POST /procurement-requests/{id}/analyze — run bounded, tool-free ADK evidence assessment using saved Channel3 results (or perform discovery first).
- POST /procurement-requests/{id}/purchase-orders — create a draft PO from a product ID and exact offer URL in the saved discovery snapshot. The server derives price, currency, and quantity.
- GET /purchase-orders — list the current user's POs, payment summaries, approvals, and audit events.
- GET /purchase-orders/{id} — retrieve an owned PO.
- POST /purchase-orders/{id}/submit — submit a draft for human approval.
- POST /purchase-orders/{id}/approve — record explicit human approval.
- POST /purchase-orders/{id}/reject — record rejection and optional reason.
- POST /purchase-orders/{id}/payments/paypal/create — create PayPal Sandbox checkout for an approved PO.
- POST /purchase-orders/{id}/payments/paypal/capture — verify buyer-approved PayPal order and capture it.

## Invariants

- Every authenticated PO endpoint scopes the resource by authenticated user ID.
- The client cannot supply item prices, totals, or currency.
- The server uses the stored Channel3 snapshot and refuses offers not in that snapshot, offers in a different currency, and offers not marked in stock.
- Only approved orders may start PayPal checkout.
- PayPal order ID, custom ID, amount, and currency must match the frozen PO before capture.
- A PO is marked paid only after a matching completed capture response or a signature-verified matching completed-capture webhook.
- PayPal webhook event IDs are unique and duplicate deliveries are idempotent.

Foreign-owned resources return 404.

## Dashboard

Authenticated `GET /api/v1/dashboard/summary` returns user-scoped counts of completed, active and awaiting-approval orders; requests with discovered products; and the latest eight order audit events. It does not sum amounts in unrelated currencies. Provider status is separately available via `GET /api/v1/integrations/status`.

## Approval queue, AI-budgeted analysis and demo operation

- GET /api/v1/purchase-orders?status=pending_approval returns only pending orders owned by the authenticated user. Unsupported status values return 422. The screen at /approvals is a real authenticated view rather than a redirect.
- POST /api/v1/procurement-requests/{request_id}/analyze automatically performs one Channel3 discovery if needed, then uses a saved compact evidence shortlist for one Gemini/ADK call. Responses include request_id, explanation, status, cached, source (gemini or catalogue_only), and optional usage token counters.
- Identical repeated analyses return cached=true and do not re-invoke Gemini. A verified empty catalogue returns source=catalogue_only, usage=null, without a Gemini call.
- Daily exhausted global/user LLM allowance returns HTTP 429 with Retry-After, while product discovery/PO paths remain usable. Missing model key returns 503; live provider failure is reported separately. AI budget defaults are documented in docs/agent.md.
- Latest database migration: 0004_ai_budget, auto-applied by start.bat and the VS Code startup task.
- PayPal Sandbox buyer approval must return in the same tab for frontend sessionStorage continuity. The browser return does not establish paid status; capture verification does.

## Integration status contract (non-secret)

Authenticated `GET /api/v1/integrations/status` returns `runtime.environment`, `runtime.provider_checks=configuration_only`; `database.connected/schema_ready/engine`; `ai.configured/api_key_set/model`; `channel3.configured/api_key_set/base_url_configured`; `paypal.credentials_configured/client_id_set/client_secret_set/webhook_configured/environment`. Empty or obvious template key values count as missing, and Channel3 requires a valid HTTPS API endpoint. The endpoint performs database SELECT checks only; it does **not** call Google Gemini, Channel3 or PayPal to claim provider availability, return tokens or expose backend credentials. The browser refetches periodically and provides a manual refresh action.

## Bounded read endpoints and operational responses

### Procurement request list

`GET /api/v1/procurement-requests?limit=50` returns a **user-owned, chronologically sorted metadata list**. Each row intentionally includes `analysis_json: null` so a busy workspace does not download large product snapshots for each card. `limit` accepts 1–100. The detail endpoint `GET /api/v1/procurement-requests/{id}` returns the full saved analysis and product evidence. `include_analysis=true` preserves the former full-list payload when deliberately requested, but has higher DB/response cost.

For **keyset pagination**, pass both `before_created_at` (ISO 8601 timestamp from the last returned row) and `before_id` (its ID), together with `limit`. Results use a stable `created_at DESC, id DESC` order. Invalid/partial cursors return 422.

### Purchase orders and audit

`GET /api/v1/purchase-orders?limit=50&status=pending_approval` is owner-scoped and bounded to 100 orders. Embedded `audit_events` in **list** results includes the most recent 25 events per purchase order to bound response size. `GET /api/v1/purchase-orders/{id}` still returns the full saved order-specific audit history. These safeguards limit list payloads, not underlying immutable financial evidence.

### Authentication and throttling

In staging/production, register/login are guarded by distributed Redis fixed-window attempt limits. A limit violation returns `429` with `Retry-After`; a missing/unavailable Redis protection service returns `503` rather than accepting unthrottled public authentication. Development remains offline-compatible. JWTs now have bound issuer/audience and required timestamps; previously issued tokens without those claims must be replaced by signing in again.

### API security and health

API responses send `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`, anti-framing/permission headers and an API-only CSP. Oversized request bodies return 413; source schema/money errors return 422. Liveness `GET /api/v1/health` does not depend on external services; readiness `GET /api/v1/ready` checks core/AI quota database schema and returns 503 on DB migration outage. Neither endpoint certifies Redis, PayPal, Gemini or Channel3 remote availability. Use the authenticated integration status flags for configured values and explicit provider workflow tests for actual connectivity.
