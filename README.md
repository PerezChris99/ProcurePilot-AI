# ProcurePilot AI

**From purchasing request to approved purchase — intelligently.**

ProcurePilot AI is an AI-assisted procurement workspace designed to help businesses translate natural-language purchasing needs into structured requirements, discover and compare products, prepare purchase orders, obtain human approval, and complete a verified PayPal payment workflow.

> Hackathon prototype in active development. The current UI and API foundation are being built incrementally. Channel3, Google ADK/Gemini, and PayPal Sandbox integrations are not represented as operational until independently connected and tested.

## Technology

- Frontend: React, JavaScript (ES modules), JSX, Vite, Tailwind CSS, React Router, TanStack Query.
- Backend: Python, FastAPI, Pydantic, SQLAlchemy, Alembic.
- Database: PostgreSQL.
- AI: Google ADK and Gemini.
- Product discovery: Channel3 API.
- Payments: PayPal Orders API v2 (Sandbox for the hackathon).
- Tests: Vitest, React Testing Library, Pytest, HTTPX, Playwright.

No TypeScript or TSX is used in the frontend.

## Repository layout

- frontend/ — React application.
- backend/ — FastAPI application and business services.
- docs/ — architecture, development, security, and testing notes.

## Local development

See docs/development.md. Copy .env.example to an untracked local environment file and supply credentials there. Never commit secrets. The frontend uses VITE_API_BASE_URL for the API origin; backend credentials must never use VITE_ variables.

## Safety and transaction integrity

- AI can research, compare, explain, and prepare purchase orders; it cannot approve or capture payments.
- Human approval is mandatory before payment.
- Backend-calculated totals are authoritative.
- Approved purchase-order contents and prices must be immutable; edits require reapproval.
- Only verified PayPal transaction evidence may mark a purchase order as paid.
- PayPal Sandbox activity must not be described as live supplier settlement.

## Git workflow

Implementation is developed on perez, reviewed through a pull request, and merged into main after verification. No additional development branches or GitHub Actions workflows are used.

## License

MIT. See LICENSE.
