# ProcurePilot AI

**From purchasing request to approved purchase — intelligently.**

ProcurePilot AI is an AI-assisted procurement workspace for businesses. It is designed to turn natural-language purchasing needs into structured requests, discover and compare real catalogue products, prepare purchase orders, obtain human approval, and complete a verified PayPal payment workflow.

> Hackathon prototype in active development. The repository now contains the React/JSX workspace, FastAPI account and procurement-request APIs, Channel3 search adapter, deterministic product ranking, and a Google ADK agent endpoint. These integrations have not yet been validated with live developer credentials or run through the local test suites. Do not treat unconfigured services or unfinished workflows as operational.

## Implemented code

- React, JavaScript (ES modules), JSX, Vite, Tailwind CSS, React Router, and TanStack Query frontend.
- Python/FastAPI backend with PostgreSQL-ready SQLAlchemy models and Alembic migrations.
- Email/password registration and login, Argon2id password hashing, and short-lived JWT access tokens.
- Authenticated procurement request creation, listing, detail retrieval, and user-level ownership checks.
- Channel3 product search adapter, response validation, offer normalization, and user attribution header.
- Deterministic product ranking with explicit treatment of missing attributes, price, availability, and delivery uncertainty.
- Google ADK procurement research agent with a restricted Channel3 search/ranking tool.
- Initial frontend and backend test suites written.

## Not yet complete

Purchase-order generation, human approval, PayPal Orders API integration, webhook verification, payment reconciliation, complete audit history, production deployment, and full end-to-end test execution remain to be implemented.

## Technology

- Frontend: React, JavaScript/JSX, Vite, Tailwind CSS, React Router, TanStack Query.
- Backend: Python, FastAPI, Pydantic, SQLAlchemy, Alembic.
- Database: PostgreSQL.
- AI: Google ADK and Gemini.
- Product discovery: Channel3 API.
- Payments: PayPal Orders API v2 (Sandbox for the hackathon).
- Tests: Vitest, React Testing Library, Pytest, HTTPX, and Playwright (planned for E2E coverage).

No TypeScript or TSX is used in the frontend.

## Local development

See docs/development.md. Configure frontend/.env for the public API base URL and backend/.env for private credentials. Never commit secrets. Vite exposes variables prefixed with VITE_ to browser code; never put API keys, JWT secrets, database URLs, or PayPal credentials in frontend variables.

## Transaction safety principles

- AI can research, compare, explain, and prepare purchase orders; it cannot approve purchases or capture payments.
- Human approval is mandatory before payment.
- Backend-calculated totals are authoritative.
- Approved purchase-order contents and price snapshots must be immutable; edits require reapproval.
- Only verified PayPal transaction evidence may mark a purchase order as paid.
- Channel3 product discovery and PayPal Sandbox payment are separate. A Sandbox capture is not proof that a retailer received payment.

## Git workflow

Implementation is developed on perez, reviewed through a pull request, and merged into main after verification. No additional development branches or GitHub Actions workflows are used.

## License

MIT. See LICENSE.
