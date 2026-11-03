# Testing strategy

Frontend tests use Vitest and React Testing Library. Backend tests use Pytest, FastAPI TestClient, and isolated in-memory SQLite databases. Integration tests use HTTPX mock transports so external services are not called or billed during unit tests.

Current test coverage includes health endpoints, dashboard rendering, registration/login/token-protected profile access, duplicate-account rejection, Channel3 request shape and response validation, and deterministic product ranking.

Required next coverage:
- Authentication authorization and cross-user resource isolation.
- Requirement extraction, malformed model output, and prompt injection.
- Channel3 empty results, timeouts, rate limits, and pagination.
- Ranking correctness, unknown attributes, and multi-currency offers.
- Purchase-order state transitions and approval immutability.
- PayPal order creation/capture, amount/currency mismatch, and ownership validation.
- Webhook signature validation, duplicate events, and reconciliation.
- End-to-end approved purchase and blocked unapproved/rejected purchase.
