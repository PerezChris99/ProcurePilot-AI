# ProcurePilot AI — QA and deployment acceptance

**Post-submission note (10 November 2026):** The solo developer reports submitting the project to Devpost. GitHub records a successful Vercel deployment of `be87bc3` on 9 November; this does not establish a current full test pass. The procedures below remain necessary before any new production release.

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
6. For every post-submission release, confirm the Vercel commit, inspect runtime errors and maintain a working hosted demo and private judge buyer access through the judging window.

Do not describe mocked tests, isolated SQLite migrations or a compiled build as proof that real third-party APIs or public deployment are working.

See [integration acceptance](../docs/INTEGRATION_ACCEPTANCE.md), [release procedure](../docs/RELEASE_READINESS.md) and [judge instructions](../docs/JUDGE_ACCESS_PLAYBOOK.md).

## Neon / release evidence (read-only except explicit migration)

To initialize the **real** Neon database, run the explicitly user-triggered
`python qa/initialize_neon.py` with the **backend virtualenv interpreter**;
it reads a copied **Direct** TLS URL from the Windows clipboard (no hidden paste), clears the clipboard, applies only `alembic upgrade
head`, and writes sanitized `qa/reports/neon.json`.

For a verification-only database probe, set `DATABASE_URL` privately in
your terminal and run `python qa/verify_neon.py --output qa/reports/neon.json`.
Never paste a URL into arguments, logs, commits, or the frontend.

For public hosted acceptance, save the seven read-only checks as
`qa/reports/hosted.json`. Then invoke `python qa/report_release.py`.
It requires 9/9 offline checks, a real Neon 0010 schema PASS, 7/7 hosted
checks, a clean `perez` tree, and refuses to treat these as PayPal capture
or provider certification. It **never merges or deploys**.

## Staging E2E and protected Preview

The separate Neon `procurepilot-ai-staging` project has no production data.
Copy its **Direct** PostgreSQL TLS URL from the Neon Console (project
`procurepilot-ai-staging`, database `procurepilot`, pooling OFF). Then run
this single staging-only command from the repository root:

```powershell
.\backend\.venv\Scripts\python.exe .\qa\initialize_neon.py --smoke
```

It applies Alembic and runs actual FastAPI registration, login, JWT
authorization, persistent procurement writes, DB status, policy scenarios and
cross-user isolation. It creates disposable **staging** users and one
staging procurement request, never calls providers and refuses production's
Neon hostname. A sanitized report is saved to
`qa/reports/staging-e2e.json`.

The `perez` preview is `https://procurepilotai-preview.vercel.app` and
may require Vercel Authentication. For protected HTTP acceptance, create a
temporary revocable **Protection Bypass for Automation** secret in the
Vercel dashboard and set `VERCEL_AUTOMATION_BYPASS_SECRET` privately in
your terminal, then run:

```powershell
python .\qa\live_demo_check.py --frontend https://procurepilotai-preview.vercel.app --api https://procurepilotai-preview.vercel.app
```

The script never sends the bypass secret to production or arbitrary domains
and blocks redirects when using it. Revoke the temporary bypass after QA.
Never paste passwords, bypass tokens or provider keys into chats or Git.
