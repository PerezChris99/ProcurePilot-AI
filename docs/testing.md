# Testing strategy

Frontend tests use Vitest and React Testing Library. Backend tests use Pytest, FastAPI TestClient, and isolated in-memory SQLite. HTTPX MockTransport and monkeypatched service clients keep unit and API tests independent of paid external services.

## Written coverage

- Health, registration/login, duplicate accounts, and protected profile access.
- Channel3 headers, response validation, pagination, discovery persistence, and user scoping.
- Deterministic ranking, mandatory attribute mismatches, quantity-aware budget scoring, and unknown delivery.
- Purchase-order total derived from the saved catalogue offer, not a browser-supplied price.
- Draft to pending approval to approved/rejected transitions.
- Rejected and unapproved purchase orders cannot create a payment.
- PayPal order creation, buyer approval precondition, amount/currency matching, completed capture, and idempotent capture replay.
- Cross-user purchase-order access denial.
- Webhook signature rejection, duplicate event handling, and completed-capture reconciliation.
- PayPal API OAuth, request idempotency header, and webhook verification payload.
- Dashboard, procurement form, and purchase-order UI rendering/actions.

## Required execution

Run from backend/: pytest and pytest --cov=app --cov-report=term-missing.

Run from frontend/: npm ci, npm run lint, npm test, and npm run build.

The repository has not yet been executed in a local runtime in this session. Passing status must be based on actual command output, not the presence of test files.

## Remaining verification

- Run all backend and frontend suites.
- Exercise Alembic upgrade/downgrade on PostgreSQL and SQLite.
- Test live Channel3 API with a developer key, including error/limit/pagination behavior.
- Test Google ADK/Gemini tool execution with a real key and hostile catalogue descriptions.
- Complete a PayPal Sandbox buyer and merchant test transaction and verify webhook delivery from an HTTPS deployment.
- Browser E2E test the whole journey, including rejected approval and amount-mismatch failure paths.
- Verify deployment secrets, CORS origins, TLS, backups, rate limiting, and production observability.
