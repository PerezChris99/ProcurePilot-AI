# Testing strategy

Initial smoke tests cover API health and dashboard rendering. The suite will expand with each feature.

Required integration and security coverage:
- Authentication, authorization, and cross-user resource isolation.
- Requirement extraction, malformed model output, and prompt injection.
- Channel3 success, empty results, timeouts, and rate limits.
- Deterministic ranking and missing product attributes.
- Purchase-order state transitions and approval immutability.
- PayPal order creation/capture, amount and currency mismatch, and ownership validation.
- Webhook signature validation, duplicate events, and reconciliation.
- End-to-end approved purchase and blocked unapproved/rejected purchase.
