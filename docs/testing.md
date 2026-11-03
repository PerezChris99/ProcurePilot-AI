# Testing strategy

Frontend tests use Vitest and React Testing Library. Backend tests use Pytest, FastAPI TestClient, and isolated in-memory SQLite databases. Integration tests use HTTPX mock transports or monkeypatched clients so external services are not called or billed during unit tests.

Tests have been written for API health, registration/login/token-protected profile access, duplicate-account rejection, Channel3 request headers and response validation, deterministic ranking and quantity-aware budget comparison, procurement request persistence and ownership isolation, mocked Channel3 discovery snapshot persistence, mocked agent analysis persistence, dashboard rendering, and procurement request submission behavior. They have not yet been executed in a local development environment.

Required next coverage:
- Authentication rate limiting, expired/revoked tokens, and account lifecycle.
- Requirement extraction, malformed model output, and prompt injection.
- Channel3 empty results, timeouts, rate limits, pagination, and currency/offer edge cases.
- Ranking correctness, unknown attributes, and multiple offers.
- Purchase-order state transitions and approval immutability.
- PayPal order creation/capture, amount/currency mismatch, and ownership validation.
- Webhook signature validation, duplicate events, and reconciliation.
- End-to-end approved purchase and blocked unapproved/rejected purchase.
