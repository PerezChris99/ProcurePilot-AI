# API overview

Base path: /api/v1

## Public

- GET /health — liveness response.
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
- POST /procurement-requests/{id}/analyze — run the ADK research agent.
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
