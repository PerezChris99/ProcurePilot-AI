# Release and judge readiness — 4 November 2026

## Source work committed and merged previously

- Windows bootstrap and VS Code integrated startup, frontend build gate and automatic Alembic migrations.
- Channel3 paginated response handling, PayPal capture/webhook safeguards, same-tab Sandbox checkout, user-scoped dashboard analytics and batched order-list queries.
- Regression tests and the Windows verify.bat script.
- Details in Git history and PR #8.

## This audit's new implementation scope (delivered through the perez → PR → main workflow)

- Functional /approvals page with authenticated, status-filtered pending queue and human decision controls.
- Personalized time-of-day greeting from the signed-in account.
- Original procurement/verified-purchase SVG favicon and shared sidebar/auth branding.
- Preserved existing layout; theme refined to Whitesmoke, navy, sky blue and a restrained sweet yellow accent, with more legible small text.
- Evidence-first AI orchestration: one deterministic Channel3 discovery if needed, compact top-four packet, a single bounded ADK Gemini call, repeat-response caching, honest empty catalogue and token metadata.
- Atomic per-user and global UTC-day call budgets in new migration 0004_ai_budget.
- Current Channel3 attribute-array compatibility and in-stock-only price ranking. Optional ADK research tool outputs are restricted to five compact scored candidates.
- Authorized-use-only proprietary license with narrow hackathon evaluator permission.
- Rewritten README with multiple workflow diagrams, and updated security, architecture and AI engineering documents.
- Updated PayPal merchant-vs-buyer setup guide, with an explicit Merchant REST-app selection and Sandbox Business linkage.

## Local verification NOT executed in this GitHub connector session

The GitHub connection permits source reads/writes, PRs and merges. It does not provide the user's Windows PostgreSQL service, installed npm/Python dependencies or the confidential provider credentials. No report may say tests, frontend production build, live Gemini/Channel3 calls, PayPal Sandbox buyer capture, or signed HTTPS webhooks have passed solely because code was pushed.

Run start.bat, verify.bat, and the manual walkthrough in docs/testing.md. Record local failures with redacted logs. The terminal and external access needed for a real provider/payment run remains a user-side acceptance gate.

## Residual architecture and infrastructure risk

- Self-approval remains allowed in the personal-workspace demonstration (not independent enterprise governance).
- No robust distributed request rate limiting beyond the hard daily model-call reservation.
- No password reset, email verification or live token revocation.
- No complete exactly-once payment reconciliation after network uncertainty or proven cross-worker transaction safety.
- No frontend package-lock.json currently tracked; dependency resolution may vary across installations.
- No Playwright E2E suite, backup restore drill, host-level security headers, observability/alerts or verified deployment.
- No actual supplier settlement through Channel3; PayPal remains a separate Sandbox demonstration.
- Proprietary LICENSE may conflict with hackathon requirements for an OSI open-source project.
- The repository was publicly visible when last checked; keep credentials strictly out of Git.

## Acceptance status

**Code changes authored and version-controlled; runtime and commercial readiness not certified.** A smooth judge experience must be confirmed in a genuine local/browser/Sandbox rehearsal rather than inferred.

## Final source audit follow-up (November 2026)

- Gemini 3.8 Flash: removed outdated low-temperature sampling parameters and added an explicitly low thinking level to reduce cost/latency while retaining the existing 900-output-token cap and one-ADK-call limit; legacy model IDs do not receive a Gemini-3-only setting.
- Added production startup validation for persistent PostgreSQL via installed psycopg driver, a canonical HTTPS frontend origin, and the existing strong JWT secret requirement. The Windows development bootstrap remains unchanged.
- Added regression tests for model generation settings and incorrect production database/frontend URLs.
- Still not release-certified until the user runs the full Windows verify.bat (including frontend lint/Vitest/build) and exercises live provider credentials and PayPal Sandbox with signed HTTPS webhooks. No checked-in frontend lockfile or browser E2E suite exists.

- Windows bootstrap now rejects incompatible Node.js versions before attempting to install Vite 7 dependencies; package.json declares the corresponding Node engines, and the Vite dev server defaults to localhost binding.
- The model config regression accepts the SDK's enum/string representation of the low thinking level.

- Added a separate unauthenticated readiness probe at `/api/v1/ready`, which runs cheap SQL checks against the users table and latest AI-budget migration, returning 503 on unavailable database/schema. `/api/v1/health` remains process liveness; external provider validity is checked separately.

- Introduced a dedicated strict public frontend build gate, a Node-native URL test suite, and a browser runtime guard against a deployed UI calling localhost. Hosting must use npm run build:deploy explicitly, while the Windows local build remains unchanged.

- The Windows verify.bat frontend test stage now also executes the Node-only public API endpoint validator test suite before attempting the Vite build. The validator was separately exercised in this review with nine passing Node tests (not a complete frontend build).

## Judge experience / mobile-first improvements (source authored, not runtime certified)

- Executable macOS/Linux shell launch and verify scripts using a first-run-only local SQLite demo path, alongside the existing Windows VS Code Ctrl+Shift+P Tasks launcher.
- Responsive six-destination navigation with a bottom iPhone safe-area dock below 961px and a flat desktop sidebar, plus dedicated Activity and saved Discovery views instead of duplicated links.
- Authenticated, secret-safe dynamic configuration panel with database engine/schema readiness, Gemini, Channel3, PayPal credentials, separate webhook flag, actual environment and manual/periodic refresh. Configured is not the same as remotely verified.
- Release acceptance still requires native macOS/Linux/Windows script execution, all local tests/builds, responsive browser/device review and live third-party provider workflows. A SQLite local judging database is not production readiness.

## Public landing and legal site implementation (source audit, November 2026)

- Public `/` now renders a compact responsive editorial landing page with verified real Unsplash CDN photo URLs, transparent translucent mist, keyboard-operable previous/next/pause and reduced-motion awareness, evidence-first product explanation, truthful technology integration strip, FAQ and CTA. No invented customer counts/testimonials or payments claims.
- Eight actual public pages: About, How It Works, Privacy, Terms, Security, Accessibility, Responsible Use, Contact. Public footer, pre-login legal links and a thin signed-in legal footer are source-authored. Legal text is a prototype disclosure and requires owner/counsel acceptance before commercial use.
- Authenticated Overview moved to `/dashboard`, login/register redirects updated; purchase/order/approval and PayPal Sandbox `/orders` buyer return paths unchanged. Vercel and Netlify SPA fallback rules added for direct URL refresh.
- New RTL/Vitest tests cover landing hero carousel/FAQ, public legal links, public-versus-private routes and preserved order URL. The existing AppShell navigation test now targets the new authenticated dashboard route.
- Remaining acceptance: current full `verify.bat` / `verify.sh`, real responsive browser/Safari tests, remote photo loading, public HTTPS API and deployment rewrites, actual provider credentials and signed webhooks, legal publication review, and previously documented production-governance gaps. Static audit or a Git merge alone cannot certify those tests as passing.
