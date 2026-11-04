# Test strategy and judge acceptance checklist

Source-authored tests are not proof of runtime success. Run the commands below on a Windows machine with the installed dependencies and a configured PostgreSQL database.

## One-command local validation

From the repository root:

~~~powershell
.\start.bat
.\verify.bat
~~~

The launcher installs missing dependencies, applies Alembic migrations through 0005_read_indexes, opens VS Code, then executes a frontend build and starts the API/React dev server in integrated terminals. If VS Code blocks automatic tasks until trust is granted, run the named task **ProcurePilot: Build then Start (VS Code Terminals)**. Stop old backend/frontend terminals before relaunching to avoid port conflicts.

The verifier runs:
1. Python compileall across backend application and tests.
2. Backend Pytest.
3. Frontend ESLint.
4. Frontend Vitest/React Testing Library and Node deployment URL regression tests.
5. Frontend Vite production build.

It stops at the first failure. No GitHub Actions workflows are configured.

## Automated regression coverage authored

- Authentication: register/login/current user, duplicate account, invalid login, missing bearer token.
- Request lifecycle: create, ownership, Channel3 discovery snapshots and paginated merge.
- Channel3: x-api-key/user headers, page envelopes, attribute arrays, malformed/error payloads.
- Ranking: mandatory attribute match and mismatch, array-valued attributes, in-stock-only pricing, quantity and budget behavior, unknown delivery.
- AI: bounded evidence packet, adversarial seller descriptions excluded, one ADK call, provider usage metadata, caching, empty catalogue without tokens, user/global UTC daily quotas and 429 behavior.
- Purchase orders: server-derived amounts, owner constraints, only approved checkout, amount mismatch, signed webhook behavior, duplicate capture ID protections, filtered approval queue, batched serialization.
- Frontend: procurement form, dashboard status and personalized greeting, genuine Approvals route empty/action states, Orders actions and same-tab PayPal checkout.

**Not implemented:** Playwright browser E2E suite, load tests, full adversarial prompt injection benchmark, production monitoring and real-provider acceptance automation.

## Manual judge route

1. Sign up and confirm the Overview shows your own first name and empty counts.
2. Create a new procurement request with quantity, budget and USD currency.
3. Click **Ask AI to analyze** before searching. Confirm Channel3 discovery fills the product cards and the Gemini assessment appears when configured.
4. Click Ask AI again; confirm cached assessment returns without another provider call. Look at the provenance/usage note.
5. Inspect product offers: a non-HTTPS, wrong-currency, unknown/out-of-stock or over-budget offer should not have an enabled Create PO button.
6. Create a PO from a qualified real offer and submit it. Visit **Approvals** through the sidebar and approve/reject. Pending order should disappear from the queue after deciding.
7. In Orders, create a Sandbox checkout and approve in the same browser tab using the Sandbox Personal buyer account. Return and explicitly capture.
8. Review the paid state, capture ID, audit timeline and updated Overview metrics.
9. Test invalid login, unauthorized request ID access, empty-catalogue behavior, quota exhaustion and provider outage errors.
10. With a public HTTPS endpoint and registered Sandbox webhook ID, send genuine signed PayPal events and validate duplicate/late-event processing.

**Important:** A PayPal Sandbox payment is not a Channel3 merchant purchase. No credentials or actual funds should be displayed in the demo.

## External prerequisites to record as passed (not assumed)

- [ ] PostgreSQL service running, Alembic at 0004_ai_budget.
- [ ] Python packages installed and backend Pytest green.
- [ ] npm dependencies resolved, lint/Vitest/build green.
- [ ] Gemini key and chosen model return an actual bounded response with usage.
- [ ] Channel3 key returns real product/offer pages, including attributes.
- [ ] PayPal Sandbox Business merchant app and Personal buyer successfully complete a checkout and capture.
- [ ] Public HTTPS webhook receives and verifies genuine events.
- [ ] Navigation, session restoration, mobile screen sizes and the favicon inspected in browser.
- [ ] No secrets exposed, no phantom branch or unmerged PR.
- [ ] Hackathon license/submission requirements reconciled with the proprietary authorized-use license.

## Mobile and cross-platform judge acceptance matrix

- Verify `./start.sh` and `./verify.sh` on macOS and Linux, and `.\\start.bat` plus `.\\verify.bat` on Windows. The macOS/Linux default creates SQLite only if .env does not exist; do not accidentally replace a judge's PostgreSQL credentials.
- In Chrome/Firefox responsive mode and Safari/iOS where available, test 320px, 375px, 430px, 768px, 960px, 961px and 1440px widths, the six accessible original iOS-style SVG mobile dock icons and labels, desktop flat sidebar, safe-area spacing, keyboard focus, and no horizontal overflow.
- Verify Activity lists actual saved audit events, Discovery lists the signed-in user's saved procurement requests, and neither reveals another account's data.
- System status: check all keys unset, only Channel3 URL present, PayPal client ID without secret, full Sandbox credentials, webhook ID unset/set, SQLite vs PostgreSQL, and schema missing. Confirm the UI labels these as configuration signals rather than validated provider connectivity.
- Exercise real provider operations only with authorized test credentials; compare dashboard flags with outcomes. Do not report a Sandbox payment as a supplier settlement.

## Public marketing, policy, and deep-link regression checks

- Open `/` as a **signed-out judge**: public full-photo overlaid hero and real images load, controls advance all three slides, Pause/Play works, and the short Problem/Solution, How It Works, FAQ and CTA sections render without console errors or horizontal overflow.
- Exercise the photographic carousel with mouse, keyboard and a reduced-motion preference; use a browser without external image network access to check that headings, CTAs and captions remain legible. Do not describe photographs as real customers or supplier evidence.
- Open all public footer links directly without a token: `/about`, `/how-it-works`, `/privacy`, `/terms`, `/security`, `/accessibility`, `/responsible-use`, `/contact`. Test refresh on each. Confirm the login/register pages also link to the legal pages.
- Verify authenticated overview at `/dashboard` and guest redirect to `/login` on direct `/dashboard` access. After login/register, the landing should not accidentally replace the dashboard. Confirm every desktop sidebar/mobile bottom-dock Overview link targets `/dashboard`.
- Confirm that `/orders?token=...` still opens the protected order page after the PayPal Sandbox same-tab buyer return, not the public landing or a host 404. Confirm direct URL refresh works on deployed Vercel/Netlify through the SPA rewrite rules.
- Review privacy/terms text with the project owner or qualified counsel before treating them as final commercial policies. Test actual provider credentials and webhook delivery independently of the public website source/build.

## Security and scaling regression gates

Execute `.\\start.bat` then `.\\verify.bat` on Windows; on macOS/Linux use `./start.sh` then `./verify.sh`. A new Redis Python dependency and Alembic 0005 migration were introduced; do not run the verifier from an un-updated virtual environment. Back up existing databases before migrations.

- Validate `backend/tests/test_database_pool.py`, `test_database_indexes.py`, `test_http_security.py`, `test_auth_rate_limits.py`, `test_token_claims.py`, `test_untrusted_evidence_limits.py` and `test_read_path_limits.py`. Test local CORS preflight and main browser login again; token format changes intentionally require fresh login.
- On a real PostgreSQL 17 database, run `alembic upgrade head` and confirm revision `0005_read_indexes`, compound indexes and unique PayPal order/capture IDs. Investigate and reconcile any historical duplicate payment IDs before restarting a failed migration.
- Verify public auth with managed TLS Redis: 429 plus Retry-After beyond thresholds, 503 fail-closed when Redis is down, no leaked email/password in Redis key names, correct client address behind a trusted ingress proxy. Check legitimate users behind NAT are not broadly throttled.
- Validate 1 MiB incoming body/2 MiB Channel3 response rejection, finite price/maximum amount checks, malformed webhook event rejection, and default lean procurement list behavior with `include_analysis=true` as the explicit heavy legacy mode.
- Run Postgres explain/plan analysis and representative load/soak/fault/restore tests before claiming 100K or 1M users. Rehearse PayPal Sandbox/webhook race handling separately. Full procedures: [scaling and operations](scaling.md).

## Universal mobile navigation and landing polish

- At 320, 375, 390, 430, 768, and 960 CSS pixels, verify the **same** fixed translucent dock design on `/`, `/#why`, `/#how`, `/#faq`, `/about`, `/privacy`, `/login`, `/register`, `/dashboard`, `/procurement`, `/orders` and `/requests/:id`. The public destinations are Home/Why/How/FAQ/About/Account (or Workspace for a signed-in user); private routes retain the six workspace/sidebar links.
- Verify the active destination changes with a landing anchor hash and with the `/requests/:id` Discovery detail route. Anchors must scroll below the sticky header; safe-area spacing must keep the dock above the iPhone home indicator without obscuring the footer or sign-in controls.
- At widths 961px and above, the bottom dock must be hidden: the public site uses its header links and the workspace uses its desktop sidebar.
- Exercise the hero carousel manually (next/previous/dots/pause), keyboard-only and with `prefers-reduced-motion: reduce`; images must not hide readable captions or controls as they load. No external provider configuration is required to render the public landing page.
- Run the complete five-stage local verifier, including ESLint, Vitest, Node-native configuration tests and Vite production build, after pulling; also inspect the real app in a phone browser. A GitHub merge is not a substitute for local runtime verification.

## Accessibility / legibility acceptance

- Verify with real browsers on Windows and iPhone/Android: 320px, 375px, 390px, 430px, 768px, 960px and desktop widths, plus **200% text/page zoom** and **400% zoom** with common user flows. Text, controls and the six destinations must remain usable without horizontal scrolling or overlap.
- Check long metadata values in Orders, Discovery, approvals and the System Status panel at these widths. At 320px the public header hides the duplicate Sign in link; Account remains available in the bottom dock.
- Verify keyboard-only paths and visible focus on public links, CTA buttons, forms, FAQ expanders and carousel controls. With `prefers-reduced-motion:reduce`, hero entry animations and carousel auto-rotation should stop.
- Confirm sweet yellow is used selectively for the final CTA and meaningful warning states with **dark ink**. No decorative yellow dash before the hero kicker, heading underline, footer border, or colored metric-card edges. Test the browser's forced-colors/high-contrast modes, since visual color accents are never a substitute for textual status.
- Run `npm run test:deploy-config` to check actual configured CSS token pairs using the WCAG contrast formula; the checked pairs exceed 7:1 where possible, with ordinary blue-on-white links tested against 4.5:1. This is a **source-level check**, not a complete WCAG conformance audit.
- Validate with screen readers (NVDA or VoiceOver), actual pointer targets and localization/long names before any claim of broad accessibility compliance.

## Wide landing and neutral metrics visual acceptance

- At 1024px, 1440px, 1920px and ultrawide widths, the public header, hero, story, workflow, FAQ, final CTA and footer must use the same narrow responsive side clearance; do not retain the previous 1220px hard cap.
- At 961px+ confirm the photo fills **the entire 510px-high hero section**, with all headline content, two CTAs and trust disclosure legible inside it. Verify that both slideshow controls and caption remain visible without overlap at 1440px and wider; at narrower widths the secondary photo caption can be suppressed to avoid clutter. Mobile uses a taller single-section hero that cannot crop or overlap primary actions. At all widths, check that parallax is subtle and disabled when `prefers-reduced-motion: reduce` is active.
- On /dashboard, verify that the **four true saved-data metrics** appear as a single plain rectangular summary with thin neutral dividers and no colored edge/highlight, gradient tile or rounded metric card. Preserve four values, loading placeholders, recent activity, the primary button and integration status. The redundant promotional hero should no longer render.
- Confirm the shortened public and dashboard labels still honestly describe the AI, Channel3 and PayPal Sandbox limitations, and that privacy/legal pages remain intact. Verify the FAQ and slideshow controls, reduced motion, mobile dock, 200%/400% zoom, and the frontend build.
- Run `npm run test:deploy-config` for documented layout contract and color checks; the full lint, Vitest and Vite build remain separate gates.
