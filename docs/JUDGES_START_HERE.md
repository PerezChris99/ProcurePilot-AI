# Judges — start here

**ProcurePilot AI · Every Purchase Has a Reason**  
**Demo video: 1:59** (creator-reported runtime) · [Devpost entry](https://devpost.com/software/procurepilot-ai) · [Live app](https://procurepilotai.vercel.app)

## The idea in 20 seconds

**What happens when the cheapest product is the wrong product?**

ProcurePilot checks **real Channel3 offers** against mandatory buyer specifications before an AI explains the qualified options. A human authorizes the selected order, **PayPal Sandbox** confirms the test capture, and a **Decision Passport** preserves the reasons, approver and payment evidence.

~~~mermaid
flowchart LR
    A["Requirement"] --> B["Channel3 offers"]
    B --> C{"Meets policy?"}
    C -->|No| D["Visible rejection"]
    C -->|Yes| E["Gemini explains"]
    E --> F["Human approval"]
    F --> G["PayPal Sandbox test"]
    G --> H["Decision Passport"]
~~~

## Try the real hosted workflow

**Start:** [https://procurepilotai.vercel.app](https://procurepilotai.vercel.app)

1. Select **Get started**; register or sign in.
2. Create **New procurement**: for example, *two 27-inch office monitors*, quantity **2**, USD budget **$1,000**, 27-inch display mandatory. The example does **not** guarantee current listings.
3. Choose **Search products**; compare real Channel3 prices, merchants, eligibility and rejection reasons. Only describe a rejected option as *the cheapest* when saved same-currency prices prove that.
4. Choose **Ask AI to analyze**; read the attributed Gemini/ADK response, or an explicitly labelled rules-only fallback.
5. Select an **eligible** offer, **Create PO**, then **Submit for approval**. An authorized reviewer approves it in **Approvals** (the owner can self-approve unless a separate reviewer was assigned).
6. Under **Purchase orders**, create **PayPal Sandbox checkout**. Use a **Personal Sandbox buyer** separate from the app's Business merchant, approve in the PayPal tab, return, and choose **Confirm buyer approval & capture**. Returning alone does not constitute capture.
7. Inspect the paid order, audit history and **Decision Passport** (JSON/PDF), including selected/rejected evidence and capture proof.

**Access:** A dedicated **Personal Sandbox buyer** can be provided through the private Devpost testing instructions. Never publish a password, real PayPal login or API secret in GitHub. See [judge payment details](JUDGE_ACCESS_PLAYBOOK.md).

## What the Decision Passport proves

~~~mermaid
flowchart TD
    REQ["Saved requirements + Channel3 snapshot"] --> PASS["Decision Passport"]
    RULE["Eligibility and rejection reasons"] --> PASS
    AUTH["Human decision and timestamp"] --> PASS
    CAP["Validated PayPal Sandbox capture"] --> PASS
    PASS --> EXP["Inspect or export JSON / PDF"]
~~~

A rejected cheaper quote is **not savings**. Catalogue attributes are historical observations, not live guarantees. A Sandbox capture moves **no real money to a Channel3 retailer** and does **not** place a supplier order.

## Offline inspection, if providers are unavailable

This runs **clearly labelled synthetic data**, not actual Channel3/Gemini/PayPal activity.

Requires Git, Python **3.12+** and Node **22.12+** (or **20.19+**).

**Windows:**

~~~powershell
git clone https://github.com/PerezChris99/ProcurePilot-AI.git
cd ProcurePilot-AI
.\judge-preview.bat
~~~

**macOS / Linux:**

~~~bash
git clone https://github.com/PerezChris99/ProcurePilot-AI.git
cd ProcurePilot-AI
python3 judge-preview.py
~~~

Open `http://127.0.0.1:5173`, register, then optionally seed an explicitly marked sample by running `.\judge-preview.bat --seed-email YOUR_REGISTERED_EMAIL` (Windows) or `python3 judge-preview.py --seed-email YOUR_REGISTERED_EMAIL` (macOS/Linux). Offline sample orders are **non-payable**.

The authenticated **Decision Trust Lab** runs twelve labelled synthetic policy/authorization/payment-matching scenarios. These exercise real policy predicates without third-party calls, live payments or invented merchant evidence.

## Verify and read more

- **Automated local QA (Windows):** `.\test-all.bat`; [what it covers](../qa/README.md).
- **Hosted 7-gate read-only check:** `python .\qa\live_demo_check.py --frontend https://procurepilotai.vercel.app --api https://procurepilotai.vercel.app`.
- **Deep dive:** [Architecture](architecture.md) · [API](api.md) · [Security](security.md) · [Provider setup](provider-setup.md).

**Status:** The solo creator reports a completed Sandbox test transaction and Devpost submission. GitHub recorded a successful Vercel deployment of commit `db3cd787` on 10 November 2026. These reports do not substitute for independently re-running live providers, signed webhooks or all current QA checks. Keep test access available through the December 15 judging-period end.
