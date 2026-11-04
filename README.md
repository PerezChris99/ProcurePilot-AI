# ProcurePilot AI

**From purchasing request to approved purchase — intelligently.**

ProcurePilot AI is an AI-assisted procurement workspace for small businesses. It structures purchasing requests, discovers real products through Channel3, ranks options using deterministic evidence-based scoring, prepares purchase orders, records human approval, and demonstrates a separate PayPal Sandbox payment lifecycle.

> Hackathon prototype in active development. The repository contains the initial procurement workflow and the purchase-order/approval/PayPal integration code. Developer credentials, migrations, tests, and the complete external Sandbox round trip still require local verification. Do not treat unconfigured integrations as operational.

## Current implementation

- React 19 with JavaScript/JSX, Vite, Tailwind CSS, React Router, and TanStack Query.
- Python/FastAPI backend with PostgreSQL-ready SQLAlchemy models and Alembic migrations.
- Email/password authentication, Argon2id password hashing, and short-lived JWTs.
- User-scoped procurement requests and Channel3 product discovery.
- Deterministic product ranking and saved catalogue snapshots.
- Google ADK procurement agent with a restricted Channel3 research tool.
- Purchase-order creation from saved catalogue offers; the server calculates totals and snapshots product/offer details.
- Draft, pending approval, approved, rejected, payment pending, paid, and payment-failed lifecycle states.
- Human approval records, immutable approved amounts, payment idempotency, PayPal webhook signature verification, duplicate-event protection, and per-order audit history.
- Frontend purchase-order workflow and explicit PayPal return/capture action.

## Important integration boundary

Channel3 provides product discovery and retailer offer links. Its public developer page currently describes merchant checkout as coming soon. PayPal Sandbox is therefore a separate hackathon payment demonstration. A Sandbox payment does not pay the Channel3 retailer or prove supplier settlement. Confirm Channel3 checkout access and PayPal live merchant eligibility separately before making a commercial settlement claim.

## Technology

Frontend: React, JavaScript/JSX, Vite, Tailwind CSS, React Router, TanStack Query.

Backend: Python, FastAPI, Pydantic, SQLAlchemy, Alembic.

Database: PostgreSQL (SQLite is used by isolated API tests).

AI: Google ADK and Gemini.

Product discovery: Channel3 Product API.

Payments: PayPal Orders v2 API (Sandbox).

Tests: Vitest, React Testing Library, Pytest, HTTPX. Browser E2E and real Sandbox verification remain to be run.

No TypeScript or TSX is used in the frontend.

## Local development

See docs/development.md. Configure backend variables from .env.example and frontend variables from frontend/.env.example. Never commit secrets. Vite variables prefixed with VITE_ are public browser values; never put API keys, database URLs, JWT secrets, or PayPal credentials in frontend variables.

From backend/: install requirements, run alembic upgrade head, then start uvicorn app.main:app --reload.

From frontend/: run npm ci, npm run dev, npm run lint, npm test, and npm run build.

Backend verification: run pytest and pytest --cov=app --cov-report=term-missing from backend/.

## PayPal Sandbox setup

Set backend-only variables: PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com, PAYPAL_WEBHOOK_ID, and FRONTEND_URL.

Register the public HTTPS webhook URL /api/v1/webhooks/paypal in the PayPal Developer Dashboard. Subscribe to CHECKOUT.ORDER.APPROVED, PAYMENT.CAPTURE.COMPLETED, and PAYMENT.CAPTURE.DENIED. The backend verifies each event with PayPal before processing it.

## Transaction safety

- The agent cannot create or approve purchase orders, or capture PayPal payments.
- The browser cannot set authoritative item prices, totals, or payment amounts.
- Purchase-order totals are calculated from the saved Channel3 offer snapshot and frozen in the order.
- Only an approved purchase order can start checkout.
- Capture is allowed only after buyer approval and backend verification of the remote order ID, custom ID, amount, currency, and capture result.
- Webhooks are signature-verified and event IDs are idempotent.
- Only verified, matching completed capture evidence moves an order to paid.
- PayPal credentials remain server-side.

## Git workflow

Implementation is developed on perez, reviewed through a pull request, and merged into main after verification. No additional development branches or GitHub Actions workflows are used.

## License

MIT. See LICENSE.
