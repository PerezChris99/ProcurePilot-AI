# API overview

Base path: /api/v1

## Public

- GET /health — liveness response.
- POST /auth/register — create an account and issue a short-lived bearer token.
- POST /auth/login — authenticate and issue a bearer token.

## Authenticated

- GET /auth/me — return the current user.
- POST /procurement-requests — create a purchasing request.
- GET /procurement-requests — list the current user's requests (limit 1–100).
- GET /procurement-requests/{id} — retrieve an owned request.
- POST /procurement-requests/{id}/discover — retrieve Channel3 catalogue products and persist deterministic ranking snapshots.
- POST /procurement-requests/{id}/discover?next_page=true — load the next Channel3 page using the opaque token saved by the backend; the backend merges and re-ranks the product set.
- POST /procurement-requests/{id}/analyze — run the ADK procurement agent, which can invoke the Channel3 search/ranking tool, and persist its explanation.

Resource lookup always scopes by the authenticated user ID. A request owned by another user is returned as 404.
