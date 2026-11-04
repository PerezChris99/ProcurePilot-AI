# Test strategy and judge acceptance checklist

Source-authored tests are not proof of runtime success. Run the commands below on a Windows machine with the installed dependencies and a configured PostgreSQL database.

## One-command local validation

From the repository root:

~~~powershell
.\start.bat
.\verify.bat
~~~

The launcher installs missing dependencies, applies Alembic migrations through 0004_ai_budget, opens VS Code, then executes a frontend build and starts the API/React dev server in integrated terminals. If VS Code blocks automatic tasks until trust is granted, run the named task **ProcurePilot: Build then Start (VS Code Terminals)**. Stop old backend/frontend terminals before relaunching to avoid port conflicts.

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
- In Chrome/Firefox responsive mode and Safari/iOS where available, test 320px, 375px, 430px, 768px, 960px, 961px and 1440px widths, the six accessible mobile dock links, desktop flat sidebar, safe-area spacing, keyboard focus, and no horizontal overflow.
- Verify Activity lists actual saved audit events, Discovery lists the signed-in user's saved procurement requests, and neither reveals another account's data.
- System status: check all keys unset, only Channel3 URL present, PayPal client ID without secret, full Sandbox credentials, webhook ID unset/set, SQLite vs PostgreSQL, and schema missing. Confirm the UI labels these as configuration signals rather than validated provider connectivity.
- Exercise real provider operations only with authorized test credentials; compare dashboard flags with outcomes. Do not report a Sandbox payment as a supplier settlement.
