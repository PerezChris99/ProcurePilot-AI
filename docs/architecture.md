# Architecture: evidence-first procurement monolith

ProcurePilot AI is a modular monolith: React 19/JavaScript frontend, FastAPI/Python backend, PostgreSQL persistence, Channel3 product discovery, Google ADK/Gemini explanation, and a distinct PayPal Orders v2 Sandbox payment demonstration.

## Boundaries and responsibilities

~~~mermaid
flowchart TB
  Browser[React / JWT session] --> API[FastAPI auth and procurement routes]
  API --> DB[(PostgreSQL / Alembic)]
  API --> Channel3[Channel3 product API]
  API --> Rules[Deterministic ranking and PO validation]
  Rules --> Packet[Compact evidence packet]
  Packet --> Budget[Atomic UTC-day AI budget]
  Budget --> ADK[One-call Google ADK analyst]
  ADK --> Gemini[Gemini]
  API --> Paypal[PayPal Orders v2 Sandbox]
  Paypal --> Webhook[Verified HTTPS webhook]
  Webhook --> API
~~~

### Domain flow

1. A new registered personal-workspace user gets an Argon2id-hashed password and short-lived JWT; sessionStorage holds the browser access token. The logged-in landing view greets them by first name.
2. The buyer creates a user-scoped procurement request with description, quantity, currency and optional budget.
3. Product discovery calls Channel3, validates paginated products/offers/attribute arrays and persists deterministically ranked results.
4. Asking for AI first triggers a single Channel3 discovery if necessary; if ranked evidence already exists, it is reused. Repeated unchanged AI assessments return cached text. A verified empty catalogue returns no model hallucination or spend.
5. An allowlisted evidence packet of at most four candidates is passed to the ADK analysis_agent with one-call and output/time limits. A global+user call reservation in ai_daily_budgets prevents unbounded call volume. The normal analyst has NO order/payment tools.
6. The buyer selects a saved real Channel3 offer. Server code verifies its exact product and offer URL, price, currency, stock, mandatory attributes and budget; it derives quantity*unit price, then freezes a PO and item snapshot.
7. Submission moves a draft PO to pending_approval. The dedicated Approvals route loads owner-scoped pending items and records approve/reject actions. **The owner may self-approve when no reviewer is assigned. A distinct registered reviewer can instead be assigned to decide a specific order without operating its payment; organization-wide RBAC/invitations are not implemented.**
8. Approved orders may create a separate PayPal Sandbox checkout. Buyer approves in the SAME browser tab to preserve the session on return. Capture validates remote order/custom IDs, currency, amounts and final completed capture evidence.
9. PayPal webhooks are validated through PayPal's signature endpoint. Event IDs and capture matching reduce duplicates and mismatch risk; a real HTTPS webhook still needs environment configuration.
10. The dashboard reads user-scoped SQL counts and recent order audit history. Provider status displays configuration flags, not proof of live connectivity.

## Purchase lifecycle

~~~mermaid
stateDiagram-v2
  [*] --> draft
  draft --> pending_approval: Submit
  pending_approval --> approved: Owner records approval (demo)
  pending_approval --> rejected: Owner rejects
  approved --> payment_pending: Sandbox order created
  payment_pending --> paid: Verified capture
  payment_pending --> payment_failed: Denied capture
  paid --> [*]
  rejected --> [*]
~~~

## Verifiable policy lab and impact accounting

`GET /api/v1/trust-lab/scenarios` (authenticated) executes twelve labelled
fixtures through the real `evaluate_offer`, delegated reviewer and PayPal
order-match predicates, without calling providers or storing purchases.
An incorrect scenario outcome is shown as **FAIL**, never silently fixed.
This is a deterministic scenario test, not a penetration test or live provider
certification.

The Decision Passport is calculated from the **immutable-at-PO-creation saved
source snapshot**. Eligible same-currency offers determine the lowest
orderable comparison; ineligible same-currency offers may be shown as
rejected examples with policy reasons, but never counted as savings. Delivery,
tax, inventory truth, and retailer settlement remain unverified.

## Tables / data ownership

| Table | Purpose |
| --- | --- |
| users | Email, Argon2id hash, active flag |
| procurement_requests | Owner, requirements, quantity/budget/currency, ranked Channel3 snapshot, optional cached explanation and usage |
| purchase_orders | Frozen currency/amount, request/owner, approval and payment state |
| purchase_order_items | Saved catalogue ID, title, merchant, HTTPS offer URL, quantity, unit price, full product snapshot |
| approvals | Actor, decision, comment and timestamp |
| payments | PayPal order/capture IDs, stable idempotency key, status, amount and currency |
| webhook_events | Unique verified event ID, minimal payload and processed time |
| audit_events | User/order/request actions and time |
| ai_daily_budgets | Atomic per-scope UTC-day call count; no prompts or secrets |

Migration chain: 0001_users → 0002_requests → 0003_orders → 0004_ai_budget → 0005_read_indexes → 0006_purchase_policy → 0007_decision_evidence → 0008_offer_verification → 0009_delegated_approver. Windows startup automatically runs Alembic upgrade head before serving the app.

## API surface

Auth: POST /api/v1/auth/register, POST /api/v1/auth/login, GET /api/v1/auth/me.

Procurement: POST and GET /api/v1/procurement-requests, GET /{id}, POST /{id}/discover, POST /{id}/analyze.

Orders: POST /api/v1/procurement-requests/{request_id}/purchase-orders, GET /api/v1/purchase-orders (optional status filter), GET /{id}, POST /{id}/submit, /approve, /reject.

Payments: POST /api/v1/purchase-orders/{id}/payments/paypal/create and /capture; POST /api/v1/webhooks/paypal.

Trust Lab: GET /api/v1/trust-lab/scenarios (authenticated, synthetic fixture execution only). Liveness: GET /api/v1/health. Database readiness: GET /api/v1/ready. Authenticated configuration status: GET /api/v1/integrations/status; overview: GET /api/v1/dashboard/summary.

## Security/trust boundaries

Browser controls and catalogue content are untrusted. Amounts and transitions are determined by server code; the AI cannot modify PO/payment state. JWT ownership checks constrain records. Database-backed daily model quotas avoid process-local budget bypass. Payment authenticity is checked with PayPal and not inferred from browser redirects or webhook headers alone.

## Outstanding engineering work

No organization-wide RBAC/invitations, reconciliation worker, distributed discovery/checkout rate limiter, session revocation, live provider acceptance tests, end-to-end browser suite, independently anchored audit ledger or proven production monitoring/recovery. Public login/register use Redis-backed throttling, and per-order registered delegated reviewers are supported. Channel3 merchant checkout is separate from PayPal Sandbox and is not implemented. The project is a demonstration, not a live multi-merchant payment processor.
