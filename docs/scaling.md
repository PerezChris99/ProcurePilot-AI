# Scalability, database operations and security

**Status:** Architecture and controls implemented in the repository; **100,000 and 1,000,000 user capacity is not measured or certified**. The numbers below are planning examples, not observed results.

## 1. What load actually means

Distinguish **registered accounts**, **daily active users**, **simultaneous sessions**, **HTTP requests per second**, **AI calls**, and **payment captures**. A million accounts with 1,000 concurrent users is fundamentally different from a million simultaneous database connections. Never set `max_connections=1000000`.

Define traffic assumptions before sizing: sign-in rate, active purchase orders per user, monthly historical audit events, catalogue sizes, Gemini/API quotas, transaction writes and peak-to-average burst factor. Use actual data, representative peaks and an explicit SLO.

## 2. Implemented safeguards

| Layer | Actual code-level behavior | Operational dependency |
| --- | --- | --- |
| Database pool | Bounded SQLAlchemy pool, pre-ping/recycle, checkout/connect timeouts | Tune over all API replicas against DB capacity |
| Postgres query | Per-session 15s statement limit, 3s lock limit, 15s idle transaction limit | Validate against production query plans; scheduled migrations may require a different role/session |
| Read paths | Composite user/status/created indexes, 1-query order counts, latest-eight activity, slim saved-request lists, keyset pagination | Monitor slow SQL and index utilization |
| Money | Decimal finite/precision/range validation, server-derived totals, PayPal amount and capture evidence checks | Live-provider reconciliation and concurrency acceptance still pending |
| Provider payloads | Global 1 MiB incoming request ceiling, 2 MiB Channel3 response ceiling, maximum 120 saved catalogue products per request | Ingress/egress timeouts, provider rate limits and alerting |
| Auth | Argon2id, expiring JWT, SQL owner scoping, Redis atomic per-source/per-email attempt throttling in public environments | Managed TLS Redis, trusted proxy identity, WAF/edge abuse controls |
| Response headers | X-Content-Type-Options, X-Frame-Options, no-referrer, API no-store, API-only restrictive CSP, production HSTS | HTTPS edge termination, frontend CSP and full browser security testing |
| Financial identifiers | Unique DB indexes for PayPal order ID and capture ID in Alembic 0005 | Review existing data before migration; do not bypass uniqueness errors |

User-owned endpoints always apply SQL ownership checks. This is **not** a substitute for database permission isolation or organization-level RBAC.

## 3. PostgreSQL connection budgeting

Configuration keys in the root environment:

```dotenv
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=5
DB_POOL_TIMEOUT_SECONDS=10
DB_CONNECT_TIMEOUT_SECONDS=5
DB_STATEMENT_TIMEOUT_MS=15000
DB_LOCK_TIMEOUT_MS=3000
DB_IDLE_TRANSACTION_TIMEOUT_MS=15000
```

The maximum number of application-to-database connections can approach:

`replicas × API workers per replica × (pool size + max overflow)`.

For example, **10 replicas × 2 workers × (5 + 5) = 200 potential backend connections**, before migrations, admin sessions and auxiliary jobs. That may already exceed a small Postgres instance's practical budget. Prefer a monitored **PgBouncer**/provider pooler and modest per-worker pools, not unbounded DB connections.

Use separate roles for the runtime API and Alembic migrations: runtime grants only required DML and SELECT on application tables/sequences, no superuser/CREATEDB/CREATEROLE/BYPASSRLS; migrations use an isolated owner role in controlled deploys. Use SCRAM authentication, authenticated TLS, private networking and secret rotation. Do not use the local `postgres:postgres` example outside local development.

PgBouncer mode must be tested with psycopg prepared-statement and transaction behavior. Keep payment state changes and atomic AI quota reservations on the **primary** database; do not route these consistency-sensitive paths to lagging replicas.

## 4. Query and storage practices

- Use `EXPLAIN (ANALYZE, BUFFERS)` in a controlled environment for the authenticated dashboard, pending approvals, purchase-order lists and audit history with realistic distributions. Confirm the planned composite indexes are used where beneficial.
- Procurement list responses exclude large `analysis_json` by default. Fetch full evidence by request ID. `include_analysis=true` is an explicit heavy legacy override, not the preferred UI path.
- Saved requests support `before_created_at` plus `before_id` keyset pagination (no deep OFFSET). Purchase-order list remains capped at 100, with latest 25 audit events **per order in lists** and full history in individual order details.
- Indexes accelerate targeted reads at a write/disk cost. Run `ANALYZE`, check vacuum/autovacuum throughput and index bloat, and review indexes against workload before adding more.
- Apply Alembic 0005 in a maintenance-controlled migration after backup. It upgrades legacy PayPal identifier indexes to UNIQUE: if historical duplicates exist, **stop and investigate** rather than deleting or silently merging payment records. Some index operations take locks; plan maintenance for large tables.
- Retain immutable payment/audit evidence according to a documented legal retention policy. Introduce table partitioning (for time-growing audit/event tables), cold-storage archives or read replicas only after actual workload and retention analysis, never as a speculative blanket change.
- Enforce disk/IO/memory headroom, WAL retention, PITR backups, replication health and tested restore procedures. Backups that have never been restored are not a recovery strategy.

## 5. Authentication, AI and payment abuse

- For `APP_ENV=staging` or `production`, set `RATE_LIMIT_REDIS_URL=rediss://...` to a managed TLS Redis service. Register/login fail with HTTP 503 when this limiter is not configured or cannot be reached—**fail-closed, not silently unthrottled**. Thresholds are eight attempts/minute per normalized email identity and 120/minute per source IP, enforced with atomic Redis counters. Identifier keys are HMAC hashed.
- Make sure the reverse proxy passes a **validated real client address** to ASGI; do not naively trust arbitrary `X-Forwarded-For` headers. If `request.client` resolves only to one load balancer for everyone, the source quota can block legitimate traffic. Verify it before launch.
- An ingress WAF/CDN and distributed limits for **all** routes—not just login/registration—remain required for high-scale deployments. Credential stuffing, abuse from botnets, distributed IP rotation, scraping, API cost exhaustion and DDoS cannot be solved by a fixed Python or Redis rule alone.
- The normal Gemini analysis is bounded to one model call, short allowlisted evidence and atomic per-user/global daily quotas. It cannot approve or capture payments. Prompt injection is treated as a residual risk; backend rules, not model text, determine purchases.
- The PayPal path uses Sandbox and server-side verification; do not accept real funds until concurrency-safe state transitions, webhook replay/out-of-order handling, unknown-outcome reconciliation and merchant eligibility are independently tested.

## 6. Practical load and failure qualification

Before claiming any 100K/1M scale, run an isolated staging exercise (never against public third-party provider accounts):

1. Create representative users, procurements, product snapshots, orders and long audit trails. Snapshot/restore this seeded dataset safely.
2. Establish baseline p50/p95/p99 for auth, list, dashboard, approvals and state transitions. Simulate API calls without spending real model tokens or capturing real payments.
3. Step through realistic concurrency and RPS levels (e.g. 100, 1,000, 10,000 connections as infrastructure allows), then soak for hours, with separately measured write-heavy peaks.
4. Measure API CPU/RAM, DB active/idle connections, checkout queue wait, lock contention, slow queries, query plans, WAL, disk IO, Redis pool/latency, 429/503/5xx frequency and network saturation.
5. Deliberately terminate DB/Redis/worker connections, exhaust pools, restart instances and delay webhook processing. Verify failure is controlled and authenticated actions neither duplicate payments nor lose accepted events.
6. Validate backups with a **complete restore** and measure recovery point/objectives. Add external synthetic monitoring, SLO alerts, log retention, fraud signals and an incident escalation process.
7. Document hardware, database size, concurrency/RPS and observed p95/p99. Never equate users registered with concurrently supported sessions.

## 7. Remaining production requirements

This prototype still lacks proven independent approver roles and organization isolation, complete payment race/reconciliation handling, general distributed API throttling/WAF, MFA/email verification/password reset/token revocation, signed-webhook live delivery acceptance, frontend CSP, automated database restore drills, complete browser/device E2E coverage and independently measured scale. Continuous dependency and security testing, network policy, auditing, threat-model updates and incident response must accompany every production deployment.

Reference material: [OWASP ASVS 5.0](https://asvs.owasp.org/), [OWASP API security](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x13-V4-API-and-Web-Service.md), [PostgreSQL 17 connection settings](https://www.postgresql.org/docs/17/libpq-connect.html), and [Redis async client pooling](https://redis.io/docs/latest/develop/clients/redis-py/async/).
