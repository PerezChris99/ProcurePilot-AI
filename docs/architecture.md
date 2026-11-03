# Architecture

ProcurePilot AI is a modular monolith with a React/JavaScript frontend, Python/FastAPI backend, PostgreSQL persistence, Google ADK agent orchestration, Channel3 product discovery, and PayPal Orders API payment processing.

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

Channel3 and PayPal clients are isolated under backend/app/integrations. Agent tools call application services rather than manipulating database tables directly. Channel3 product discovery is separate from PayPal Sandbox payment; a Sandbox capture is not proof that a retailer received payment.

## Current implementation

The repository currently contains the React workspace shell, API health endpoint, email/password authentication foundation, user persistence model/migration, Channel3 client and schema validation, deterministic recommendation scoring, and an ADK procurement research agent. Product persistence, procurement request endpoints, approval workflows, and PayPal integration are not complete yet.
