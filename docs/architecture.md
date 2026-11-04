# Architecture

ProcurePilot AI is a modular monolith: React/JavaScript frontend, Python/FastAPI backend, PostgreSQL persistence, Google ADK agent orchestration, Channel3 product discovery, and PayPal Orders v2 Sandbox.

## Implemented flows

1. Registration and login use Argon2id password hashing and short-lived JWT access tokens.
2. Procurement requests are scoped to their authenticated owner.
3. Channel3 product search validates nested product, offer, price, and pagination data. Results and ranking snapshots are persisted on the request.
4. The ADK agent can research and explain products through a controlled Channel3 tool. It has no purchase approval or payment capability.
5. A buyer selects a product and retailer offer from the saved Channel3 snapshot. The backend verifies the product and exact offer URL, currency, price, and stock status, calculates quantity multiplied by unit price, checks the request budget, and freezes a purchase-order item snapshot.
6. A purchase order progresses from DRAFT to PENDING_APPROVAL. Human approval or rejection is recorded in the approvals table and audit log.
7. Only APPROVED orders can create a PayPal Orders v2 checkout. The server calculates the amount from the frozen order, requests an OAuth token, creates the Sandbox order, and returns its approval URL.
8. After the buyer approves at PayPal and returns, the user explicitly requests capture. The backend fetches the PayPal order and validates its ID, status, custom ID, amount, and currency before capture. It then validates the completed capture and exact amount before marking the purchase order PAID.
9. PayPal webhooks are verified through PayPal's webhook signature verification endpoint. CHECKOUT.ORDER.APPROVED records buyer approval for a later explicit capture; capture events are reconciled against the saved PayPal order and approved amount. Event IDs are unique and duplicate deliveries are idempotent.

## Transaction state

DRAFT -> PENDING_APPROVAL -> APPROVED -> PAYMENT_PENDING -> PAID

Alternative states: REJECTED, PAYMENT_FAILED, CANCELLED, and EXPIRED.

A failed or incomplete payment never marks an order paid. Approved order contents are immutable; a changed item or amount must be represented by a new order and approval.

## Persistence

- purchase_orders: owner, request, PO reference, frozen currency/total, status, approval metadata.
- purchase_order_items: product and retailer offer snapshot, quantity, unit price, line total.
- approvals: human actor, decision, comment, timestamp.
- payments: PayPal order/capture IDs, idempotency key, status, frozen amount/currency, approval URL.
- webhook_events: unique provider event ID, verified flag, redacted event snapshot, processed timestamp.
- audit_events: user, order/request, action, minimal details, timestamp.

## Trust boundaries

- The browser is untrusted; it never supplies authoritative amounts.
- All user-owned resources are queried with the authenticated user ID.
- The AI agent is limited to product research and explanation.
- Channel3 product descriptions are untrusted data, not instructions.
- PayPal credentials and API calls remain server-side.
- Webhook authenticity is established through PayPal's verification API, not by trusting request headers alone.
- Channel3 retailer checkout and PayPal Sandbox are separate systems. Sandbox payment is not retailer settlement.

## Known scope limitations

The current approval model records the authenticated owner as the human approver; role-based multi-person approval and organization workspaces are not yet implemented. The integration still needs live developer-credential verification, browser E2E testing, deployment, and operational monitoring.
