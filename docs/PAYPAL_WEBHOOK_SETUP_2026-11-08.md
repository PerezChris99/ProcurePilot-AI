# PayPal Sandbox webhook setup — ProcurePilot AI

**Status: PARTIAL.** The FastAPI handler already exists and the canonical public callback URL has been added to the Vercel Production environment as `PAYPAL_WEBHOOK_URL`. The sensitive `PAYPAL_WEBHOOK_ID` variable also exists for Production and Preview, but the connected Vercel service **redacts its value**, so we have NOT confirmed a genuine matching provider Webhook ID or successful signed event delivery.

> **This does not cure the separate checkout error**
> "The merchant isn’t able to accept PayPal payments at this time."
> PayPal OAuth success and PayPal order creation do not prove that the Business Sandbox merchant can receive payments. Resolve the merchant account eligibility/payment configuration separately; a webhook only reconciles provider events after an eligible payment is attempted.

## Exact production configuration

| Setting | Required value | Status |
| --- | --- | --- |
| `PAYPAL_BASE_URL` | `https://api-m.sandbox.paypal.com` | Existing sensitive environment entry; actual value concealed |
| `PAYPAL_CLIENT_ID` | Existing **Business seller** REST app client ID | Existing sensitive entry; value concealed |
| `PAYPAL_CLIENT_SECRET` | Matching Business seller REST app secret | Existing sensitive entry; value concealed |
| `PAYPAL_WEBHOOK_URL` | `https://procurepilotai.vercel.app/api/v1/webhooks/paypal` | **Added to Vercel Production** |
| `PAYPAL_WEBHOOK_ID` | **Real ID returned by registering that exact listener in the same PayPal Sandbox REST app** | Existing Vercel sensitive entry; provider match and value **not verified** |

Do **not** enter the URL in `PAYPAL_WEBHOOK_ID`. The URL and Webhook ID are different things. Do not guess or fabricate an ID or copy one from a different Sandbox REST app. When rotating the merchant app, register a new matching listener and update the ID.

### PayPal Developer UI — exact safe one-time setup

1. Visit https://developer.paypal.com/dashboard/applications/sandbox.
2. Select the **same Sandbox REST app** whose Client ID is in Vercel's `PAYPAL_CLIENT_ID`. The app must be linked to the intended, eligible **Sandbox Business merchant** account.
3. Under that REST app's **Webhooks**, inspect whether `https://procurepilotai.vercel.app/api/v1/webhooks/paypal` is already listed. If so, **reuse** it; do not create a duplicate.
4. Otherwise add that URL, and subscribe to exactly the events this handler currently processes:
   - `CHECKOUT.ORDER.APPROVED`
   - `PAYMENT.CAPTURE.COMPLETED`
   - `PAYMENT.CAPTURE.DENIED`
5. Save. Copy the **Webhook ID returned by PayPal**, not the REST app Client ID. Ensure those event names are on the saved subscription.
6. Vercel → Project `procurepilot-ai` → Settings → Environment Variables → `PAYPAL_WEBHOOK_ID`: set the genuine ID as a **sensitive** backend variable. If the existing variable holds another app's ID, replace it. Apply to Production; apply to Preview only when a separate preview webhook has been provisioned (avoid linking unrelated staging results to production).
7. Redeploy Production, preserving `PAYPAL_BASE_URL`, `PAYPAL_CLIENT_ID`, and `PAYPAL_CLIENT_SECRET`. This code uses `PAYPAL_WEBHOOK_ID` on the server for REST signature verification.
8. Run a legitimate, **separate Personal Sandbox buyer** approval, explicit capture, and confirm PayPal's Webhook Events dashboard shows `PAYMENT.CAPTURE.COMPLETED` delivered to the production endpoint. Inspect the saved PO and audit trail. Replay the same provider event to verify duplicate protection. Do not use a fabricated event or mark payment paid without capture.

### Optional idempotent CLI (trusted backend environment only)

If you have the **correct merchant credentials privately loaded**, run from `backend/`:

```powershell
python -m scripts.configure_paypal_webhook --check
# If the callback is missing:
python -m scripts.configure_paypal_webhook --register
```

The script lists existing subscriptions for the current REST app, matches the exact canonical HTTPS URL, checks the required events, and only creates a subscription after explicit `--register`. It prints the genuine provider `PAYPAL_WEBHOOK_ID` (a resource identifier, **not** a client secret) for you to set in Vercel. It **does not automatically write Vercel environment variables** or fix merchant payment-acceptance restrictions.

If an existing callback lacks required events, edit its event subscriptions in PayPal Developer; the script refuses to create a duplicate. On missing/misconfigured merchant credentials it fails without logging secrets.

### Verification and failure interpretation

- **FastAPI route:** `POST /api/v1/webhooks/paypal`, server-only and unauthenticated by design, verifies PayPal transmission headers/signature with the app-specific Webhook ID before processing records; unsigned messages fail closed.
- **Configured does not mean delivered:** `GET /api/v1/integrations/status` is authenticated, returns only whether the environment variable looks set and explicitly labels provider checks configuration-only. It does not prove PayPal has a matching subscription or that public webhooks arrive.
- **Actual receiver acceptance:** Only after a real Sandbox capture and PayPal webhook transmission is delivered/verified and an audit entry persisted can the webhook acceptance gate be marked done.
- **Payment refusal before approval:** Seller unable to accept payments is an independent provider-side merchant issue. Fix that account/app first; a registered webhook will not make that restriction disappear.

Official references:
- https://developer.paypal.com/api/rest/webhooks/rest/
- https://developer.paypal.com/payment-methods/webhooks/
- https://developer.paypal.com/api/rest/webhooks/
