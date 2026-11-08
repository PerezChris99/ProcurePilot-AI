# PayPal merchant and System Status diagnosis — 8 November 2026

## What is verified

- Hosted ProcurePilot can create PayPal Sandbox orders and merchant OAuth succeeds.
- A distinct Sandbox Personal buyer login passed the seller-account test but PayPal refused checkout: **"The merchant isn’t able to accept PayPal payments at this time."**
- The refusal happens at PayPal's merchant eligibility / buyer approval stage, **before capture**. A webhook does not make a restricted merchant eligible to receive a payment.
- A **one-shot, read-only** Vercel Preview inspection used the same configured merchant REST app to list PayPal webhooks. The build returned fixed exit **85 = `paypal_webhook_not_in_rest_app`**. The exact production HTTPS callback `https://procurepilotai.vercel.app/api/v1/webhooks/paypal` is **not subscribed in that REST app**, even though Vercel has an entry for `PAYPAL_WEBHOOK_ID`.
- The webhook ID value is marked Sensitive in Vercel and cannot be decrypted from the connected Vercel tool. Do not copy an ID from another REST app or use the callback URL as the ID.
- The old existing PayPal order was NOT captured, refunded or recreated by this investigation. Read-only inspection stopped at the webhook mismatch, so it did **not** retrieve an independent PayPal account restriction code for that order.

**Therefore there are TWO independent outstanding provider-side gates:** (1) subscribe the correct webhook URL under the active merchant REST app and set its matching ID in Vercel, and (2) make the Business Sandbox merchant eligible to accept checkout payments. Both are required for a complete capture-and-reconcile journey.

## Product changes made

1. Backend `GET /api/v1/integrations/status` now reads Pydantic environment `PAYPAL_WEBHOOK_URL` and `PAYPAL_WEBHOOK_ID` from the current Vercel deployment; responds with flags, a **masked** ID suffix, callback URL presence and most recent verified/processed PayPal event from Neon. Credentials and full provider IDs are NEVER returned.
2. It separately reports whether any completed and capture-ID-backed PayPal payment is actually recorded. Configured API credentials are **not** represented as a successful payment.
3. System Status Refresh now makes fresh browser requests with `cache: no-store` to `/api/v1/health` and `/api/v1/integrations/status`, updates the same React Query cache as the automatic polls, and displays pending, completion or failure state. Passive polling no longer disables manual Refresh.
4. The existing PayPal webhook endpoint still verifies the transmission signature using `PAYPAL_WEBHOOK_ID`, records signed events and deduplicates processed event IDs; no security checks were disabled.

**Status labels are precise:** "Configured" means server settings are present, not that PayPal has accepted a buyer or delivered an event. "Signed delivery recorded" requires an existing real verified webhook row. "Checkout verified by capture" requires an actual completed payment with capture ID. An empty ID displays Not configured, an incomplete ID/callback Incomplete, and API errors Unavailable.

## Permanent merchant acceptance procedure (cannot be bypassed in code)

1. Go to https://developer.paypal.com/dashboard/applications/sandbox and identify the **actual REST app** whose Client ID was loaded into Vercel. Confirm its linked **Business Sandbox merchant account** (seller).
2. Open https://developer.paypal.com/dashboard/accounts, select that Business account and inspect **Settings**. **Turn Negative Testing off** unless deliberately running a negative test. Check account status, receiving eligibility, supported country/currency and any restriction. The presence of an OAuth token is not enough.
3. Use a different **Personal Sandbox** buyer account. If the Business test account is restricted, unsupported for receiving USD or otherwise unable to receive payments, resolve that with PayPal or create a new eligible Business Sandbox seller and matching REST app. **Do not rotate Client IDs until the account is verified**.
4. Under that same REST app, add/reuse webhook:
   `https://procurepilotai.vercel.app/api/v1/webhooks/paypal`
   with exactly `CHECKOUT.ORDER.APPROVED`, `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.CAPTURE.DENIED`.
5. Copy its **PayPal-issued Webhook ID** into **Vercel Production `PAYPAL_WEBHOOK_ID` as a sensitive value**. Keep `PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com`, paired Business Client ID/Secret, and the registered URL consistent. Redeploy after modifying environment values.
6. Only after a receiving-capable merchant is established, create **one fresh approved procurement purchase order** in Sandbox if the merchant REST app changed; old PayPal orders remain tied to the original seller. Approve using distinct Personal Sandbox credentials, perform explicit capture, and confirm the exact amount/currency/order/capture IDs and a genuinely signed delivered webhook.
7. Resend the actual provider event from PayPal Sandbox Webhooks Events dashboard to confirm idempotent duplicate handling. Never fabricate a paid state, bypass signature verification, disable rate limits or auto-capture unapproved orders.

**Until PayPal reports an actionable issue / restriction for the specific merchant, we cannot claim the merchant's exact eligibility defect is proven.** Possibilities include a receiving restriction, wrong merchant app, negative testing, or an unsupported region/currency; a real PayPal provider error code or merchant account settings are needed to distinguish them. These are account/provider controls, not bugs fixable by bypassing PayPal rules.

## Acceptance gates

- [x] Backend exposes environment-driven webhook/configuration status without revealing secrets
- [x] Dashboard manual refresh makes explicit live GET requests and reports outcomes
- [x] Provider management API established that canonical webhook subscription is absent on the current REST app (exit 85)
- [ ] Matching provider webhook registered and Webhook ID synchronized to Vercel
- [ ] Merchant Business Sandbox payment receiving eligibility confirmed
- [ ] Distinct Personal buyer approves a real Sandbox test order
- [ ] Exact approved order captured once with valid amount and currency
- [ ] PayPal delivers signed `PAYMENT.CAPTURE.COMPLETED`, verified and deduplicated
- [ ] Full local backend pytest and frontend Vitest plus public browser E2E completed on current build

Official sources:
- https://developer.paypal.com/api/errors/overview/
- https://developer.paypal.com/api/rest/webhooks/rest/
- https://developer.paypal.com/api/rest/webhooks/events-dashboard/
- https://github.com/paypaldev/getting-started-with-paypal-sandbox
