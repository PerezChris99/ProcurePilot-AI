# Security baseline

- Keep all API credentials on the backend.
- Use Argon2id for password hashing and a strong random JWT signing secret.
- Enforce ownership checks on every user-owned resource.
- Calculate totals and currency on the server; never trust client-supplied totals.
- Freeze purchase-order item and price snapshots at approval.
- Require explicit human approval before payment initiation.
- Verify PayPal webhook signatures and process event IDs idempotently.
- Verify PayPal order ownership, amount, currency, and state before capture.
- Treat product descriptions and external catalogue data as untrusted.
- Redact credentials, access tokens, and sensitive payment data from logs.
- Apply request validation, rate limits, bounded timeouts, and safe error responses.
- Never represent a Sandbox payment as a live supplier settlement.
