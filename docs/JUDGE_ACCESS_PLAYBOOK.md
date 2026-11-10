# Judge access and PayPal Sandbox — quick guide

**ProcurePilot AI** · **Demo video: 1:59** (creator-reported)  
[Live app](https://procurepilotai.vercel.app) · [Devpost entry](https://devpost.com/software/procurepilot-ai) · [Full judge walkthrough](JUDGES_START_HERE.md)

## What you need

| Access | How to obtain it |
| --- | --- |
| **ProcurePilot account** | Select **Get started** and register, or use an isolated judge account if the entrant supplies one privately |
| **PayPal Sandbox Personal buyer** | Use the dedicated **test buyer** credentials supplied in the private Devpost judging/testing field or organizer-approved secure channel |
| **Not required** | Real PayPal login, PayPal Developer Dashboard, merchant Business login, REST API keys or database credentials |

**Important:** PayPal Sandbox uses **virtual money**. Do not use a real PayPal account. The Personal test buyer must be **different** from the Business Sandbox merchant.

## Complete a test purchase

~~~mermaid
flowchart TD
    A["Sign in to ProcurePilot"] --> B["Create request + search Channel3"]
    B --> C["Select eligible offer + create PO"]
    C --> D["Submit and approve PO"]
    D --> E["Create PayPal Sandbox checkout"]
    E --> F["Separate Personal buyer approves"]
    F --> G["Return and confirm capture"]
    G --> H["Paid record + Decision Passport"]
~~~

1. Open [ProcurePilot AI](https://procurepilotai.vercel.app) and sign in.
2. **New procurement:** try two 27-inch monitors, quantity **2**, budget **$1,000 USD**, with 27-inch size mandatory.
3. **Search products:** review actual offers and reasons ineligible listings were rejected. **Ask AI to analyze** for a real model explanation or a clearly marked non-AI fallback.
4. Select an eligible offer, **Create PO**, then **Submit for approval**. In **Approvals**, an authorized user approves it. A separately assigned reviewer must log in independently.
5. Under **Purchase orders**, start **PayPal Sandbox checkout**. In the PayPal tab, sign in as the **Personal Sandbox buyer** and approve the test transaction.
6. Return to ProcurePilot and select **Confirm buyer approval & capture**. The redirect alone does **not** mean payment completed.
7. Check that the order shows paid and open the **Decision Passport**. Compare order, amount/currency, approval and payment/capture evidence; export JSON/PDF if useful.

## If checkout does not finish

- **Login rejected?** Sign out of any real PayPal or Sandbox Business session and use the **Personal Sandbox buyer** credentials.
- **Popup blocked?** Use the saved order's **Open PayPal** link, then return to ProcurePilot.
- **Session expired?** Sign in again and open the *same* saved order. Do not create unnecessary duplicate payments.
- **Capture uncertain?** Inspect the saved payment status and order IDs before trying again. Do not assume a canceled redirect proves success.
- **Third-party service unavailable?** Use the [offline inspection route](JUDGES_START_HERE.md#offline-inspection-if-providers-are-unavailable); it is **synthetic and non-payable**, not evidence of real provider integration.

## What is and is not demonstrated

**Demonstrated in source:** Channel3 catalogue comparisons, deterministic purchasing eligibility, Google ADK/Gemini analysis with labelled fallback, human authorization, PayPal Orders v2 Sandbox capture validation, signed-webhook handlers and an evidence-backed Decision Passport.

**Not claimed:** A real supplier order, actual retailer payout, guaranteed current stock, full enterprise approvals or independently confirmed live webhook delivery.

**Credential handling:** Never post the Sandbox buyer password or merchant/API secrets in GitHub, public PDFs, screenshots or videos. Private judging access should remain functional through **15 December 2026**; rotate disposable test credentials afterward.

**Status:** The creator reports a working Sandbox buyer and a submitted Devpost entry. GitHub shows the Vercel deployment for `db3cd787` completed on 10 November 2026. These are not a replacement for current end-to-end testing.
