# Architecture — ProcurePilot AI

**Evidence-first procurement prototype** · [Main README](../README.md) · [Judge walkthrough](JUDGES_START_HERE.md) · [1:59 demo](DEMO_CHEAPEST_WRONG_PRODUCT.md)

**Design principle:** AI explains evidence; deterministic backend rules enforce eligibility; people approve orders; PayPal verifies Sandbox payments. No AI model is given authority to approve or capture a payment.

## Components and trust boundaries

~~~mermaid
flowchart TD
    UI["React 19 / JSX / Vite"] -->|"JWT + HTTPS"| API["Python FastAPI"]
    API <--> DB[("Neon PostgreSQL / SQLAlchemy / Alembic")]
    API --> DISC["Channel3 catalogue"]
    DISC --> RULES["Server-side eligibility + evidence snapshot"]
    RULES --> AI["Google ADK / Gemini explanation"]
    API <--> PP["PayPal Orders v2 Sandbox"]
    PP -. "Signed webhook, verified by API" .-> API
    API --> PASS["Decision Passport JSON / PDF"]
~~~

| Responsibility | Enforced by |
| --- | --- |
| Authentication and owner-scoped records | Argon2id passwords, short-lived JWTs, backend ownership checks |
| Required size/attributes, budget, currency, availability and merchant constraints | Deterministic Python policy, not model output |
| Evidence-based explanation | Google ADK/Gemini over bounded saved product evidence, with transparent fallback |
| Order creation, frozen price and transitions | Server-calculated quantity × saved offer price; approved state only |
| Permission to purchase | Authorized human reviewer; owner may self-approve unless a different reviewer is assigned |
| Capture and event reconciliation | PayPal Orders v2 Sandbox order/capture identity, exact amount/currency checks, verified webhook handlers |
| Durable accountability | PostgreSQL request, order, approval, payment, webhook and audit records |

## Purchase and payment states

~~~mermaid
stateDiagram-v2
    [*] --> draft
    draft --> pending_approval: Submit order
    pending_approval --> approved: Human approves
    pending_approval --> rejected: Human rejects
    approved --> payment_pending: Create Sandbox order
    payment_pending --> paid: Verified completed capture
    payment_pending --> payment_failed: Failure confirmed
    rejected --> [*]
    paid --> [*]
~~~

The buyer approves checkout in a **separate Personal Sandbox account**. Returning to ProcurePilot is **not** payment proof; the server must inspect the actual order and completed capture. The AI cannot bypass any of these steps.

## Evidence and data model

- `users` and `auth_rate_limit_counters`: account ownership and shared authentication throttles.
- `procurement_requests`: buyer requirements, Channel3 results and optional AI explanation.
- `purchase_orders` and `purchase_order_items`: server-frozen amount, currency and selected product snapshot.
- `approvals`, `payments`, `webhook_events` and `audit_events`: human authority and test-payment history.
- `ai_daily_budgets`: shared, bounded model usage.

Alembic migrations cover schema revisions through `0010_auth_throttles`. Read-only access and owner checks are implemented in API code; this is **not** a full multi-organization RBAC platform.

**Decision Passport:** reuses the saved selection/rejection snapshots, approval timeline and provider-linked test payment. Its price comparisons refer to observed same-currency quotes, not guaranteed current inventory or realized savings.

## API and verification

Core routes (prefix `/api/v1`): `/auth`, `/procurement-requests`, `/purchase-orders`, `/webhooks/paypal`, `/dashboard`, `/health`, `/ready` and authenticated `/trust-lab/scenarios`. See the [API reference](api.md).

**Local tests:** `.\test-all.bat`. **Hosted checks:** `python .\qa\live_demo_check.py --frontend https://procurepilotai.vercel.app --api https://procurepilotai.vercel.app`. The offline **Trust Lab** runs twelve labelled synthetic scenarios against production policy predicates; it does not call real providers or capture a payment. Full acceptance also needs real Channel3, Gemini/ADK and Sandbox buyer tests.

**Scope:** No live-money capture, actual retailer purchase/fulfillment, guaranteed stock, enterprise-wide roles or independently proven webhook delivery simply from source code. See [security](security.md), [provider setup](provider-setup.md) and [release checks](RELEASE_READINESS.md).
