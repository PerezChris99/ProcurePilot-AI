# Authentication

The API provides email/password registration and login with Argon2id password hashing and signed short-lived JWT access tokens. Protected routes use the HTTP Bearer scheme. The current frontend keeps the access token in sessionStorage for the lifetime of the browser tab and restores the user through GET /api/v1/auth/me after reload. This is a practical hackathon SPA approach, not the preferred final production session design; a production deployment should consider HttpOnly Secure cookies with CSRF protection and a carefully designed refresh-token lifecycle.

Passwords must be 12–128 characters. Login errors do not disclose whether an email exists. User-owned endpoints must always filter by the authenticated user ID. Never trust a user ID supplied by the browser or AI agent as proof of identity.

Production startup rejects the development JWT secret. Configure a unique random JWT_SECRET_KEY of at least 32 characters. Apply rate limits to registration and login before public production deployment.
