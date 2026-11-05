# ProcurePilot — Provider Integration Acceptance (2026-11-05)

## What “fully functional” must mean

A successful repository merge, passing mocked tests, and an authenticated
`/api/v1/integrations/status` dashboard are **not** proof of real third-party
operations. That status API deliberately reports configuration flags only.
Accept the demo only after *all* six gates below pass on a real machine with
authorized credentials.

| Gate | Acceptance | Evidence | Status in GitHub-only review |
| --- | --- | --- | --- |
| G1 — Local build | `verify.bat` or `verify.sh` succeeds, Python unit/integration, ESLint, Vitest, deploy tests and Vite production build | Redacted terminal log and exact git commit SHA | NOT EXECUTED |
| G2 — Gemini/ADK | One real benign model response, correct configured model, bounded/grounded answer and safe failure behavior | JSON summary from smoke CLI; then visible UI analysis | NOT EXECUTED — credentials unavailable |
| G3 — Channel3 | One live `POST /v1/search` returns real product IDs and valid USD-priced offers; test pagination/stock/empty/error paths | JSON smoke summary + actual signed-in UI search | NOT EXECUTED — credentials unavailable |
| G4 — PayPal Sandbox OAuth | Valid merchant REST app credentials authenticate against the Sandbox host; invalid credentials fail safely | JSON smoke summary | NOT EXECUTED — credentials unavailable |
| G5 — PayPal buyer→capture | Explicitly human-approved PO; real Sandbox personal buyer approval and server capture; amount/currency/capture IDs match, replay causes no duplicate capture | Redacted UI order/audit page + PayPal Sandbox merchant transaction | NOT EXECUTED — buyer access unavailable |
| G6 — HTTPS signed webhook | PayPal delivers real event to public HTTPS API; signature verification succeeds; duplicate/rejected/mismatched events do not double-mark paid | Redacted API event/audit details | NOT EXECUTED — HTTPS endpoint and credentials unavailable |

### Immediate local procedure

1. Checkout/pull the latest `main` commit, ensure Python 3.12+ and a Node version meeting `frontend/package.json` engines; run `start.bat` on Windows (or `./start.sh`). Run backend migrations. Use `verify.bat` to execute all local code gates; capture failure logs with secrets redacted.
2. Configure the repository-root **uncommitted** `.env` (not `frontend/.env`): `GOOGLE_API_KEY`, `AI_MODEL=gemini-3.8-flash`, `CHANNEL3_API_KEY`, `CHANNEL3_BASE_URL=https://api.trychannel3.com/v1`, `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com`, `PAYPAL_WEBHOOK_ID`. Create Sandbox **Business** merchant + separate **Personal** buyer accounts. Never copy these secrets into git, Devpost public text, ChatGPT, issue comments or logs.
3. Run **read-only** provider smoke checks from the `backend` directory using the current Python environment:

   ```powershell
   cd backend
   .\.venv\Scripts\python.exe scripts\provider_smoke.py --provider all
   ```

   On macOS/Linux: `./.venv/bin/python scripts/provider_smoke.py --provider all`.
   To isolate failures, run `--provider channel3`, `--provider paypal`, or `--provider gemini` separately.
   The Gemini probe makes **one real model call** (which may consume quota/credits). Channel3 makes one real product search. PayPal only validates **OAuth credentials**—**it does not create or capture payments**. Output includes only status/counts/error class, no secrets or provider links. A failure is an actual FAIL, not a fallback to mocked success.
4. In the UI: register/login → create a two-monitor USD budget request → Search Channel3 → Ask AI to analyze → inspect actual ranked offers and available/stale/unknown data → create PO → submit → approve. Verify the amount comes from saved Channel3 offers and is never supplied by the client.
5. Choose **PayPal Sandbox checkout**. Use the **Personal** Sandbox buyer on the official Sandbox domain in the same tab; return to ProcurePilot and capture. Confirm the returned provider order ID, capture ID, `COMPLETED` capture status, exact USD amount, paid PO state, and audit timeline. Repeat capture and create to check idempotency; reject a PO to check that payment is blocked. **No real funds or Channel3 retailer settlement occur.**
6. Register `https://YOUR_PUBLIC_API_HOST/api/v1/webhooks/paypal` as a Sandbox webhook (same REST app). Run through the valid event, duplicate/replay, forged/invalid-signature, amount mismatch, and unknown provider order scenarios. A localhost-only backend cannot receive direct PayPal webhooks; use a stable HTTPS deployment/tunnel.
7. Test signed-out judge link/access on fresh Chrome and mobile Safari/Chrome. Check 320/375/768/961/1440px widths, keyboard operation, failed provider messages, retries and reduced-motion settings. **Do not** mark the project as finished until the functional demo works when judge credentials are used.

### Automated coverage: what it proves

- `backend/tests/test_provider_end_to_end.py` exercises one **mocked** API journey across authentication, request, Channel3 response, bounded Gemini assessment, PO creation, human approval, PayPal order/capture, repeat idempotency and webhook audit. All third-party calls and webhook verification are deliberately stubbed; it is a *code integration regression*, not a provider certification.
- `backend/tests/test_channel3_client.py` checks real Channel3 `price.price` wire format, pagination and documented 30-result cap with MockTransport.
- `backend/tests/test_paypal_client.py` checks OAuth error handling and accurate created order payload, amount/currency, shipping preference and idempotency headers with MockTransport.
- `backend/tests/test_integrations_status.py` ensures the **default** Channel3 HTTPS endpoint is reflected honestly by the dashboard configuration flag.
- `backend/tests/test_provider_smoke.py` checks smoke runner pass/fail output and exception-redaction behavior without network access.
- `backend/scripts/provider_smoke.py` is an **optional** real-credential probe; it does not run in ordinary test/build scripts or place orders.

### Known blockers / risk inventory

1. **Open-source eligibility**: current LICENSE is explicitly proprietary. PayPal Devpost requires a visible open-source license. This needs a deliberate owner/license decision and change before the deadline; see [HACKATHON_TOP3_STRATEGY.md](HACKATHON_TOP3_STRATEGY.md). Do not treat test coverage as a workaround.
2. **Real service credentials and hosted HTTPS API**: absent from the GitHub connection; cannot be fabricated. The user must provision or connect these in the target runtime.
3. **No installed frontend dependency lockfile**: reproducibility on the judges' machine cannot yet be assumed, even if `npm install` passes once. A lockfile is a sensible separately authorized build change.
4. **Payment reconciliation after uncertain network failures and concurrent captures** needs real provider/race validation. Do not claim exactly-once remote settlement based on idempotency alone.
5. **AI evidence** is a bounded model summary. Do not let it authorize payment, invent prices/stock, or suggest retailer settlement.
6. **Live credentials check** cannot be inferred from presence of environment variables; a green mock test is not a live integration pass.

### References

- Official hackathon rules: https://paypalaihackathon.devpost.com/rules
- Channel3 official API guide (search max 30, wire price.price, page_token): https://github.com/channel3-ai/skills/blob/main/skills/channel3-api/references/api-reference.md
- Google Gemini stable model: https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash
- PayPal Sandbox guide: https://developer.paypal.com/sandbox-testing/overview/
- PayPal Orders API: https://developer.paypal.com/api/rest/integration/orders-api
- PayPal webhook verification: https://developer.paypal.com/api/rest/webhooks
