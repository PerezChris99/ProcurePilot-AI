# Architecture

ProcurePilot AI is a modular monolith with a React/JavaScript frontend, Python/FastAPI backend, PostgreSQL persistence, Google ADK agent orchestration, Channel3 product discovery, and PayPal Orders API payment processing.

## Implemented flows

1. A visitor registers or signs in. Passwords are hashed with Argon2id and the API issues a short-lived JWT.
2. Authenticated users create and retrieve their own procurement requests. Request queries are scoped by the authenticated user ID; foreign request IDs return 404.
3. The procurement discovery endpoint calls Channel3 POST /v1/search, validates nested product/offer/price records, ranks products deterministically, supports Channel3 page tokens, and stores a product/score snapshot against the request.
4. The authenticated analysis endpoint runs a Google ADK agent in an ephemeral session. The agent can invoke a controlled Channel3 search/ranking tool and returns an evidence-grounded explanation.

## Trust boundaries

- The browser is untrusted. Authorization, price calculation, purchase-order validation, and payment decisions happen on the backend.
- The AI agent may call explicitly registered procurement tools. It cannot approve purchases or capture payments.
- Product catalogue text is untrusted input and must never be treated as agent instructions.
- PayPal credentials and AI/API keys remain server-side.
- A purchase order is immutable after approval; material changes require renewed approval.

## Transaction lifecycle

DRAFT -> PENDING_APPROVAL -> APPROVED -> PAYMENT_PENDING -> PAID

Exception states include REJECTED, CANCELLED, PAYMENT_FAILED, and EXPIRED. Only verified PayPal transaction evidence can move an order to PAID.

## Integration boundaries

Channel3 and PayPal clients are isolated under backend/app/integrations. Channel3 product discovery is separate from PayPal Sandbox payment; a Sandbox capture is not a retailer payment.

## Remaining work

Purchase-order creation, human approval, PayPal order/capture and webhook verification, payment reconciliation, complete audit history, rate limiting, agent evaluation, and end-to-end deployment are not yet implemented.
