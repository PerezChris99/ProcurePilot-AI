# Security baseline

## Implemented controls

- Argon2id password hashing and short-lived JWT authentication.
- Authenticated owner checks for procurement requests and purchase orders.
- Backend-derived prices and totals; client-supplied amount fields are ignored.
- Purchase-order item/price snapshots sourced from saved Channel3 data.
- HTTPS retailer-offer validation and rejection of offers not marked in stock.
- Explicit human approval before PayPal checkout.
- PayPal API credentials remain backend-only.
- PayPal OAuth and Orders v2 API calls are server-side.
- Stable PayPal request IDs for order creation and capture.
- PayPal webhook signature verification using the provider verification endpoint.
- Unique webhook event IDs and duplicate delivery handling.
- Matching PayPal order/custom IDs, amount, currency, and capture status are required before paid state.
- Minimal provider response snapshots and redacted webhook payload storage.
- Bounded external request timeouts and generic provider errors.

## Important limitations before production

- Add rate limiting at the edge/API for authentication, discovery, AI, and payment endpoints.
- Add a multi-user organization/role model with separation-of-duties policy for approvers.
- Add robust transaction locking for simultaneous checkout creation/capture and webhook races.
- Add operational reconciliation for a network timeout after PayPal accepts a create/capture request.
- Add database backup/restore validation, monitoring, alerting, and retention policy.
- Add deployment-specific CORS, HTTPS, secret rotation, and security headers.
- Confirm PayPal live receiving eligibility for the target merchant country before any real-money rollout.
- Never describe PayPal Sandbox as a live retailer payment or supplier settlement.
