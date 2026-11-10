# ProcurePilot AI

**Every Purchase Has a Reason.**

> **The question:** What happens when the cheapest product is the wrong product?

ProcurePilot AI is a **solo-built, evidence-first procurement prototype**. It checks real catalogue offers against a buyer's requirements, uses AI to explain qualified options, requires human approval and records a **PayPal Sandbox** payment in an auditable **Decision Passport**.

**Demo video: 1 minute 59 seconds** (duration supplied by the creator). Watch it on the [Devpost project page](https://devpost.com/software/procurepilot-ai).

**[Open the application](https://procurepilotai.vercel.app)** · **[Watch / submission](https://devpost.com/software/procurepilot-ai)** · **[Judge quick start](docs/JUDGES_START_HERE.md)** · **[Sandbox buyer instructions](docs/JUDGE_ACCESS_PLAYBOOK.md)** · **[Technical architecture](docs/architecture.md)** · **[Tests](qa/README.md)**

## Why it matters

A cheaper 24-inch monitor does not satisfy a requirement for a 27-inch monitor. **Price is only useful after eligibility.** ProcurePilot preserves the requirement, reasons rejected offers failed, approved price, human decision and test-payment evidence. Rejected cheap quotes are **not** reported as realized savings.

## Product flow

~~~mermaid
flowchart TD
    A["Buyer: request + hard requirements + budget"] --> B["Channel3: real product offers"]
    B --> C{"Backend policy: eligible?"}
    C -->|No| D["Show rejection reason"]
    C -->|Yes| E["Qualified offers"]
    D --> E
    E --> F["Gemini via Google ADK: explain evidence"]
    F --> G["Select eligible offer; freeze order amount"]
    G --> H{"Human approval"}
    H -->|Reject| R["Record rejection"]
    H -->|Approve| I["PayPal Orders v2 Sandbox"]
    I --> J["Separate Personal test buyer approves"]
    J --> K["Server verifies completed capture"]
    K --> L["Decision Passport: evidence + approval + payment"]
~~~

**Trust model:** AI explains; **server rules decide eligibility**; a human authorizes; PayPal confirms a **test** payment. Neither the AI nor a browser redirect can approve spending or prove a capture by itself.

## Technical overview

~~~mermaid
flowchart LR
    UI["React + JSX / Vite"] --> API["Python / FastAPI"]
    API <--> DB[("Neon PostgreSQL + Alembic")]
    API --> C["Channel3"]
    API --> AI["Google ADK / Gemini"]
    API <--> PP["PayPal Sandbox"]
    API --> P["Decision Passport JSON / PDF"]
~~~

| Component | What it does |
| --- | --- |
| **React 19 + JavaScript/JSX + Vite** | Responsive procurement, approval and payment interfaces |
| **FastAPI + Python** | Authentication, policy checks, pricing, order state and payment verification |
| **PostgreSQL / Neon + SQLAlchemy / Alembic** | Durable purchase requests, approvals, payment and audit records |
| **Channel3** | Real catalogue products, merchant offers and observed attributes/prices |
| **Google Gemini through ADK** | Evidence-grounded explanations; no order/payment authority |
| **PayPal Orders v2 Sandbox** | Test buyer authorization, validated capture and signed-webhook handling |
| **Decision Passport** | Chosen and rejected offers, approval history and test-payment details, exportable as JSON/PDF |

## Judge access — 2 paths

**1. Hosted, real integrations:** Open [the live app](https://procurepilotai.vercel.app), select **Get started**, and follow [the 8-step judge guide](docs/JUDGE_ACCESS_PLAYBOOK.md). A **separate Personal PayPal Sandbox buyer** is required for checkout; dedicated credentials are shared **privately through the submission**, never in this repository.

**2. Offline, no provider credentials:** Inspect the same policy behavior with clearly labelled synthetic fixtures. This cannot perform actual catalogue, AI or PayPal transactions.

Windows PowerShell (Python 3.12+, Node 22.12+ or 20.19+, Git):

~~~powershell
git clone https://github.com/PerezChris99/ProcurePilot-AI.git
cd ProcurePilot-AI
.\judge-preview.bat
~~~

macOS/Linux:

~~~bash
git clone https://github.com/PerezChris99/ProcurePilot-AI.git
cd ProcurePilot-AI
python3 judge-preview.py
~~~

Open `http://127.0.0.1:5173`. To seed an **explicitly labelled offline sample** for your registered account, run `.\judge-preview.bat --seed-email YOUR_REGISTERED_EMAIL` on Windows (or `python3 judge-preview.py --seed-email YOUR_REGISTERED_EMAIL` on macOS/Linux). Offline samples are **non-payable**. For real-provider local development, follow [provider setup](docs/provider-setup.md) and use `.\start.bat` on Windows.

## Verify

From the repository root:

~~~powershell
.\test-all.bat
python .\qa\live_demo_check.py --frontend https://procurepilotai.vercel.app --api https://procurepilotai.vercel.app
~~~

The first command runs local build/security/functionality gates; the second checks **seven public HTTP gates**. Neither alone proves a live Channel3 result, Gemini reply, signed webhook or captured Sandbox transaction. See [QA details](qa/README.md) and [release acceptance](docs/RELEASE_READINESS.md).

**Deployment:** GitHub's Vercel integration reports a successful deployment of source commit `db3cd787` on 10 November 2026. The creator reports a completed PayPal Sandbox transaction and a submitted Devpost entry; those reports are distinct from independently reproduced end-to-end acceptance.

## Scope and ownership

- **This is a hackathon prototype.** PayPal Sandbox uses virtual money; the listed Channel3 retailer is **not** paid, ordered from or responsible for fulfillment. Product stock/prices are historical provider observations. Full organization-wide RBAC, real merchant ordering and live-money settlement are not implemented.
- **Created and developed independently by Kweezi Perez Christopher** for the [PayPal AI Hackathon](https://paypalaihackathon.devpost.com/).
- **License:** [MIT](LICENSE) · [Attribution](NOTICE) · [Security model](docs/security.md) · [Architecture details](docs/architecture.md) · [Development history](docs/HACKATHON_CHANGELOG.md).

*ProcurePilot AI is independent of PayPal, Google, Channel3, Neon and Vercel. Every purchase has a reason—and evidence to explain it.*
