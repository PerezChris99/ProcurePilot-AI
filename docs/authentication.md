# Authentication

The API provides email/password registration and login with Argon2id password hashing and signed short-lived JWT access tokens. Protected routes use the HTTP Bearer scheme. The current foundation includes individual user accounts; organization membership, roles, invitations, refresh-token rotation, and account recovery remain subsequent hardening tasks.

Passwords must be 12–128 characters. Login errors do not disclose whether an email exists. User-owned endpoints must always filter by the authenticated user ID. Never trust a user ID supplied by the browser or AI agent as proof of identity.

Production startup rejects the development JWT secret. Configure a unique random JWT_SECRET_KEY of at least 32 characters.
