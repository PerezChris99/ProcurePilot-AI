# ProcurePilot AI — Windows QA suite

Run from the repository root in an existing VS Code terminal:

    .\qa\setup.bat       (first time only)
    .\test-all.bat

Or invoke the full test runner directly:

    .\qa\run-all.bat

The scripts do not open new terminals, start application servers, migrate your configured database, create real provider requests, or move money.

## What runs

| Gate | Coverage |
| --- | --- |
| Python syntax | Backend modules and all Python tests |
| Backend Pytest | Existing Python API, AI/ADK, Channel3, PayPal, auth, webhook, policy, passport and security tests plus QA-specific regression tests |
| Python coverage | Branch coverage plus XML and console reporting; no artificial 100% claims |
| Isolated migrations | Two independent temporary SQLite databases: clean migration to head and migration from 0005 to head, validating key tables, columns and indexes |
| Node compatibility | Supported runtime for Vite 7 |
| ESLint | Entire frontend |
| Vitest | React routing, forms, authenticated API, offer eligibility, Passport, payment UI and existing frontend tests |
| Deployment contracts | Existing Node test suite for API URLs, security headers, a11y and Node runtime |
| Strict production build | npm run build:deploy, using QA-only VITE_API_BASE_URL=/api/v1 |
| Built asset checks | Generated HTML, JS, CSS, correct API base, no localhost endpoint and SPA route rewrites |

## Reports

After execution open qa/reports/summary.md. The runner also generates qa/reports/summary.json, individual gate logs, pytest.xml and coverage.xml.

qa/reports is gitignored. Do not commit reports or share them without checking for sensitive logs.

Any failing test/build returns a nonzero batch exit code. The production dist directory is deleted before building to avoid false positives from stale files.

## Separate deploy-targeted production build

For the later hosting phase, configure VITE_API_BASE_URL as an actual public
HTTPS backend URL ending /api/v1, or /api/v1 behind a working same-origin
HTTPS reverse proxy. Then run:

    .\qa\build-production.bat

This strict build refuses localhost or insecure endpoints. Unlike the offline
QA build, it uses your deployment configuration. It produces frontend/dist
but does not deploy or exercise paid or third-party integrations.

## Run selected gates

    .\test-all.bat --only backend
    .\test-all.bat --only frontend
    .\test-all.bat --only migrations
    .\test-all.bat --fail-fast

## Requirements

Python 3.12+ and Node 22.12+ (or Node 20.19+) must be installed. The optional setup batch installs packages in backend/.venv and frontend/node_modules. If frontend/package-lock.json is not committed, npm resolves semver ranges and repeat installs are not perfectly deterministic.

All QA subprocesses are given APP_ENV=test, an isolated SQLite URL and cleared provider credentials. The backend's real .env and PostgreSQL data are never changed by the suite. The demo build tests a relative /api/v1 configuration, not a deployed HTTPS API.

## Later manual/live acceptance (NOT tested by this batch)

1. Run real Channel3 catalogue and Gemini ADK requests with private credentials.
2. Use distinct PayPal Sandbox merchant and personal buyer accounts to approve and capture one real Sandbox order.
3. Confirm signed webhook delivery to a public HTTPS API endpoint, duplicate handling and amount mismatch failures.
4. Validate PostgreSQL migrations against a disposable PostgreSQL copy, not production first.
5. Check keyboard navigation, reduced motion, 320/375/768/960/1440px displays, mobile browsers and real devices.
6. Deploy a public stable backend/frontend, record and publish the video, and submit Devpost.

Do not describe mocked tests, isolated SQLite migrations or a compiled build as proof that real third-party APIs or public deployment are working.

See docs/INTEGRATION_ACCEPTANCE.md and docs/HACKATHON_SUBMISSION_KIT.md.
