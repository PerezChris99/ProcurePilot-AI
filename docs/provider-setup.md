# External provider setup and verification

ProcurePilot keeps all provider credentials on the FastAPI backend. Configure them in the repository-root `.env` file (or the backend process environment). Never put provider secrets in `frontend/.env`, `VITE_*` variables, source code, screenshots, issue reports, or Git commits.

## 1. Google Gemini / Google ADK

1. Open [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Create an API key in a Google project with Gemini API access.
3. Add these values to the root `.env`:

   ```dotenv
   GOOGLE_API_KEY=your_google_ai_studio_api_key
   AI_MODEL=gemini-3.8-flash
   ```

4. Restart the backend process after changing the environment.
5. In ProcurePilot, open a procurement request and use **Ask AI to analyze**.
6. Confirm the request returns an AI explanation and that the backend logs contain no authentication, quota, or model errors.

The current default model remains configurable through `AI_MODEL`. `gemini-3.8-flash` is the selected stable model for this setup; `gemini-flash-latest` is the ADK documented rolling alias. Check Google's model availability and pricing for the project before changing models.

The agent is intentionally limited to research and explanation. It must not approve purchase orders or execute payments.

References:
- [ADK Gemini model configuration](https://adk.dev/agents/models/google-gemini/)
- [Gemini model catalogue](https://ai.google.dev/gemini-api/docs/models)

## 2. Channel3 product catalogue

1. Obtain a developer API key from the [Channel3 developer platform](https://channel3.ai/).
2. Add these values to the root `.env`:

   ```dotenv
   CHANNEL3_API_KEY=your_channel3_api_key
   CHANNEL3_BASE_URL=https://api.trychannel3.com/v1
   ```

3. Restart the backend.
4. Create a procurement request and click **Search products**.
5. Confirm the response contains real catalogue product IDs, product details, retailer offers, prices, currencies, availability, and pagination metadata.
6. Test a second page when Channel3 returns a page token.

The backend sends the key in the `x-api-key` header and calls `POST /search` relative to the configured base URL. The browser never receives the key.

Channel3 catalogue discovery and retailer checkout are separate capabilities. Do not represent a retailer offer URL as a completed purchase or claim that PayPal Sandbox pays that retailer. Confirm any merchant checkout access directly with Channel3.

Reference: [Channel3 API documentation](https://docs.trychannel3.com/).

## 3. PayPal Orders v2 Sandbox

1. Open the [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/).
2. Select **Apps & Credentials**, switch to **Sandbox**, and create a REST application.
3. Copy its **Client ID** and **Secret**. These are application credentials, not the buyer's sandbox account login.
4. Add them to the root `.env`:

   ```dotenv
   PAYPAL_CLIENT_ID=your_sandbox_rest_app_client_id
   PAYPAL_CLIENT_SECRET=your_sandbox_rest_app_secret
   PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
   ```

5. Create/use a Sandbox Business account as the receiving test merchant and a separate Sandbox Personal account as the buyer.
6. After the backend is reachable through a public HTTPS URL, register this webhook URL for the same Sandbox REST app:

   `https://YOUR_PUBLIC_API_HOST/api/v1/webhooks/paypal`

7. Subscribe to:
   - `CHECKOUT.ORDER.APPROVED`
   - `PAYMENT.CAPTURE.COMPLETED`
   - `PAYMENT.CAPTURE.DENIED`

8. Copy the webhook's ID (not the REST app Client ID) into:

   ```dotenv
   PAYPAL_WEBHOOK_ID=your_registered_sandbox_webhook_id
   ```

9. Restart the backend. Submit and approve a purchase order, create checkout, approve it using the Sandbox Personal buyer, return to ProcurePilot, and explicitly capture it.
10. Verify the completed capture and matching amount/currency in the application and Sandbox dashboard. Confirm the webhook is received and signature-verified.

The local webhook receiver cannot be reached by PayPal through `localhost`. Use a trusted HTTPS development tunnel or a deployed HTTPS backend for webhook delivery. Keep the tunnel URL stable while testing and register that exact URL in the Sandbox app.

PayPal Sandbox creates simulated transactions and does not move real funds. It also does not settle a Channel3 retailer order.

References:
- [PayPal Orders API integration](https://developer.paypal.com/api/rest/integration/orders-api)
- [PayPal webhook integration and verification](https://developer.paypal.com/api/rest/webhooks/rest/)
- [PayPal Sandbox testing](https://developer.paypal.com/sandbox-testing/overview/)

## 4. Check configuration in ProcurePilot

After restarting the backend and signing in, the dashboard's **System status** panel reads the authenticated `GET /api/v1/integrations/status` endpoint. It reports whether provider credentials are present, which Gemini model is selected, whether the PayPal webhook ID is configured, and whether PostgreSQL can answer a simple query.

This is a configuration/readiness check, not proof that an external API key is valid. Actual connectivity is verified by running the corresponding AI analysis, Channel3 discovery, and PayPal Sandbox checkout flows.

## 5. Safe verification sequence

1. Confirm PostgreSQL is connected.
2. Confirm Gemini credentials are configured, then run **Ask AI to analyze**.
3. Confirm Channel3 credentials are configured, then run **Search products**.
4. Create a purchase order from a saved, eligible Channel3 offer.
5. Submit and approve the order.
6. Configure PayPal Sandbox credentials and create checkout.
7. Approve using the Sandbox buyer account and capture.
8. Verify webhook delivery over HTTPS and inspect the purchase-order audit timeline.

Do not paste API keys or secrets into ChatGPT or commit them to Git. If a credential has been exposed, revoke and rotate it in the provider dashboard.
