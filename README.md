# ProcurePilot AI

## Judges: run locally in minutes

**The quickest demo needs Python 3.12+, Node.js 22.12+ (or 20.19+), npm and Git.** Mac/Linux first-run mode uses a local SQLite file so a PostgreSQL service is **not required just to open the app**. A real Channel3 search, Gemini analysis or PayPal Sandbox checkout requires the corresponding private provider credentials in the root `.env`; the app never invents provider results.

| Platform | Start | Verify |
| --- | --- | --- |
| Windows / VS Code | ` .\\start.bat ` | ` .\\verify.bat ` |
| macOS / Linux | `./start.sh` | `./verify.sh` |

### macOS: judge quickstart

Install [Homebrew](https://brew.sh/) if needed, then open Terminal:

~~~bash
brew install git python@3.12 node
git clone https://github.com/PerezChris99/ProcurePilot-AI.git
cd ProcurePilot-AI
./start.sh
~~~

First launch creates local `.env` and `frontend/.env`, installs dependencies, applies database migrations, **builds React before starting**, then launches the backend and frontend in the current terminal. The command preserves any existing `.env`. Keep Terminal open; **Ctrl+C** stops both servers.

### Linux (Ubuntu / Debian): judge quickstart

Install Python 3.12+ and its venv package, Git, and Node.js 22 LTS from the [official Node.js downloads](https://nodejs.org/en/download). Ubuntu 24.04 users can start with:

~~~bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip
node --version    # must be at least 22.12, or 20.19
python3 --version # must be at least 3.12
git clone https://github.com/PerezChris99/ProcurePilot-AI.git
cd ProcurePilot-AI
./start.sh
~~~

For other Linux distributions use the distribution's equivalent Python/Git packages, install a supported Node.js, and run the same `./start.sh`. Run `./verify.sh` from a second terminal for all source, test and build checks.

### Windows: exactly how this project is currently run in VS Code

~~~powershell
cd "D:\NEW PROJECTS\ProcurePilot-AI"
git switch perez
git pull origin perez
.\start.bat
~~~

The Windows launcher installs requirements, applies the configured PostgreSQL migrations, opens the project in VS Code, builds React and starts the **FastAPI and React servers in VS Code integrated terminals**.

If VS Code does not start them automatically:

1. Open the project folder in VS Code and accept workspace trust.
2. Press **Ctrl+Shift+P** to open **Command Palette**.
3. Type **Tasks: Run Task** and press Enter.
4. Choose **ProcurePilot: Build then Start (VS Code Terminals)**.
5. Open **Terminal → New Terminal** and run `.\verify.bat` to verify Python, frontend lint, Vitest and Vite build.

**Local addresses:** [UI](http://127.0.0.1:5173) · [API](http://127.0.0.1:8000) · [API docs](http://127.0.0.1:8000/docs) · [Database readiness](http://127.0.0.1:8000/api/v1/ready).

### Optional PostgreSQL and external providers

On macOS/Linux, `./start.sh --postgres` starts from the PostgreSQL template **only when no `.env` exists**. For an existing `.env`, change `DATABASE_URL` yourself; the script never overwrites it. Development SQLite is useful for judging UI and local flows; **production requires PostgreSQL**. In Windows, configure PostgreSQL before `.\start.bat`.

Supply `GOOGLE_API_KEY`, `CHANNEL3_API_KEY`, `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET` and an optional `PAYPAL_WEBHOOK_ID` to unlock those real provider workflows. The authenticated System status panel reports exactly which credential categories are set and which are missing. A configured key **does not** prove a provider API call works; live transactions and signed HTTPS webhooks must be demonstrated separately.

---

**From purchasing request to approved purchase — intelligently.**

An evidence-first procurement demonstrator that brings real product discovery, deterministic purchase governance, a carefully budgeted Gemini/Google ADK analyst, and an independent PayPal Sandbox payment demonstration into one approachable workflow.

> **Evaluation status:** Hackathon prototype, not a production purchasing platform. Real Gemini, Channel3, PostgreSQL and PayPal Sandbox credentials/services must be configured and verified. A successful build does not prove real-provider availability or merchant settlement.

## Why ProcurePilot exists

A business purchase is more than a product-search query. Teams must express requirements, compare trustworthy offer evidence, stay within budget, document decisions, request human sign-off and reconcile a payment. Generic chatbots may invent stock or prices and cannot substitute for purchase controls.

ProcurePilot separates responsibilities: **the model explains, deterministic code decides what is orderable, people approve, and PayPal Sandbox demonstrates a verified payment lifecycle.** This makes a sophisticated workflow usable from a small set of clear screens.

## A judge's five-minute tour

1. **Register or sign in.** The dashboard greets you by your first name and displays your own saved purchase activity.
2. **New procurement.** Enter an unambiguous requirement, e.g. "Two 27-inch office monitors with IPS displays", quantity 2, currency USD and a reasonable budget. Product availability depends on the live catalogue.
3. **Ask AI to analyze** or **Search products**. Asking AI first automatically performs one Channel3 discovery if none has been saved, ranks the returned products in backend code, and sends a short shortlist to Gemini. Repeating an unchanged assessment uses its saved response without a new model call.
4. **Inspect the offers.** Only verified-in-stock, matching-currency, HTTPS offers within budget can become a purchase order. Review the retailer link, select **Create PO**, then **Submit for approval**.
5. **Approvals.** Open the dedicated Approvals screen, inspect the frozen item and price, and approve or reject. The personal-workspace demo permits the requester to approve their own order; this is explicitly **not independent segregation of duties**.
6. **Purchase orders → PayPal Sandbox.** Create a Sandbox checkout, sign in at PayPal using the **Sandbox Personal buyer**, approve in the same tab, return to ProcurePilot, and confirm capture. The backend checks the PayPal order and completed capture before marking it paid.
7. **Review the audit trail.** The order timeline and user-scoped dashboard show the actual events. A separate public HTTPS webhook can reconcile signed PayPal notifications.

**Required for a full payment demo:** a Sandbox **Business merchant** REST application and credentials, a Sandbox **Personal buyer**, and the appropriate order/currency. A PayPal Sandbox payment does **not** pay a Channel3 retailer.

### Screen map

| Screen | What a judge can do |
| --- | --- |
| Overview | Personalized greeting, persisted order/approval statistics, recent audit events, live-refreshing integration-configuration indicators (configured vs missing, not provider connectivity) |
| New procurement | Enter business requirements, quantity, currency and budget |
| Product discovery | Reopen saved requests and their catalogue evidence, with a searchable user-scoped history |
| Approvals | Review pending purchase orders and record a human approve/reject decision |
| Purchase orders | Submit, review status, create a Sandbox checkout, capture after buyer approval, inspect the audit timeline |
| Activity | Review the latest eight stored purchasing events and open full order-level audit trails |

## System architecture

~~~mermaid
flowchart LR
    UI["React 19 · JavaScript/JSX · Vite"] -->|"JWT / HTTPS"| API["FastAPI · Python"]
    API --> DB[("PostgreSQL · Alembic")]
    API -->|"Product search"| C3["Channel3 Product API"]
    API -->|"Compact evidence"| ADK["Google ADK · bounded analyst"]
    ADK -->|"One model call"| GEM["Gemini"]
    API -->|"OAuth · Orders v2"| PP["PayPal Sandbox"]
    PP -->|"Verified HTTPS webhooks"| API
    API -->|"Server-derived PO totals"| DB
~~~

**Frontend:** React 19, JavaScript/JSX, Vite, Tailwind CSS, React Router, TanStack Query, Vitest and Testing Library. No TS/TSX files.

**Backend:** FastAPI, Pydantic, SQLAlchemy, PostgreSQL, Alembic, HTTPX, Argon2id, JWT authentication and Pytest.

**AI:** Google ADK/Gemini for explanation. Channel3 is the actual catalogue source. Deterministic Python scoring and order validation are the authority for eligibility, quantity, budgets and saved prices.

**Payments:** PayPal REST Orders v2 **Sandbox**. Webhook signature verification is server-side. There is no merchant fulfillment, Channel3 checkout or live supplier settlement integration.

## End-to-end purchasing workflow

~~~mermaid
sequenceDiagram
    autonumber
    actor Buyer
    participant UI as React UI
    participant API as FastAPI
    participant C3 as Channel3
    participant AI as Gemini via ADK
    participant DB as PostgreSQL
    participant PP as PayPal Sandbox

    Buyer->>UI: Describe purchase and budget
    UI->>API: POST procurement request
    API->>DB: Save user-scoped request
    Buyer->>UI: Search or Ask AI
    UI->>API: Discover / Analyze
    API->>C3: Search real catalogue once
    C3-->>API: Offers and product evidence
    API->>API: Validate and rank deterministically
    API->>DB: Save ranked snapshot
    opt AI requested and daily budget remains
        API->>DB: Reserve one model call
        API->>AI: Compact top-ranked evidence
        AI-->>API: Bounded assessment + usage
        API->>DB: Cache explanation
    end
    API-->>UI: Ranked products / assessment
    Buyer->>UI: Select qualified offer
    UI->>API: Create purchase order
    API->>DB: Freeze price, quantity, URL and audit
    Buyer->>UI: Submit purchase order
    UI->>API: Submit for approval
    Buyer->>UI: Open Approvals and approve
    UI->>API: Record decision
    API->>DB: Approval and audit event
    Buyer->>UI: Start Sandbox checkout
    UI->>API: Create PayPal order
    API->>PP: Orders v2 create
    PP-->>UI: Approval URL (same tab)
    Buyer->>PP: Approve with Sandbox Personal account
    PP-->>UI: Return to ProcurePilot
    UI->>API: Capture request
    API->>PP: Verify order and capture
    PP-->>API: Confirmed capture evidence
    API->>DB: Mark paid only on matching evidence
~~~

### Order state machine

~~~mermaid
stateDiagram-v2
    [*] --> draft: Create PO from saved offer
    draft --> pending_approval: Submit
    pending_approval --> approved: Human approves
    pending_approval --> rejected: Human rejects
    approved --> payment_pending: Sandbox checkout created
    payment_pending --> paid: Verified completed capture
    payment_pending --> payment_failed: Capture denied
    rejected --> [*]
    paid --> [*]
~~~

No LLM can directly approve a purchase or capture money. A product price, stock status or delivery promise generated in free text does not become authoritative purchasing evidence.

## Economical, guarded AI engineering

The normal analysis path favors deterministic work and predictable spend:

~~~mermaid
flowchart TD
    A["Analyze request"] --> B{"Saved assessment?"}
    B -->|Yes| C["Return cached answer · 0 calls"]
    B -->|No| D{"Saved Channel3 results?"}
    D -->|No| E["One product search + deterministic ranking"]
    D -->|Yes| F["Reuse saved evidence"]
    E --> F
    F --> G{"Any catalogue products?"}
    G -->|No| H["Honest catalogue-only result · 0 calls"]
    G -->|Yes| I["Allowlist up to 4 candidate summaries"]
    I --> J{"Daily global and user budgets available?"}
    J -->|No| K["429 · preserve catalogue results"]
    J -->|Yes| L["Reserve call atomically in PostgreSQL"]
    L --> M["One ADK Gemini call · capped output/time"]
    M --> N["Persist explanation + available usage metadata"]
~~~

| Safeguard | Current default |
| --- | --- |
| ADK calls per normal assessment | **1 maximum** |
| Model output cap | **900 tokens** |
| Assessment timeout | **35 seconds** |
| Evidence shortlist | **4 products** |
| Daily calls per user | **12** |
| Daily calls across the app | **100** |
| Repeat unchanged assessment | **Cached: no model call** |
| Empty verified catalogue | **No Gemini call** |
| Model tools able to approve/pay | **None** |

Daily allowances use atomic UTC-date reservations in the database. Limits bound **call count**, not a guaranteed monetary bill; token prices vary, and metadata may be unavailable. The model sees a short JSON evidence packet without raw seller descriptions, tracking URLs or the complete catalogue. Product data remain untrusted; backend offer/price validation and human approvals remain separate from AI.

See [AI engineering and safeguards](docs/agent.md).

## Windows / VS Code setup

**Prerequisites:** Git, Python **3.12+**, Node.js LTS + npm, VS Code, a running PostgreSQL instance and a database named for your configured connection string. For real external operations you must also obtain the relevant provider credentials; no secrets ship in the repository.

~~~powershell
Set-Location "D:\NEW PROJECTS"
git clone https://github.com/PerezChris99/ProcurePilot-AI.git
Set-Location ".\ProcurePilot-AI"
code .
~~~

1. Copy root [`.env.example`](.env.example) to `.env` and supply `DATABASE_URL`, a unique `JWT_SECRET_KEY`, and the relevant backend-only provider keys. The launcher can create the template files automatically if missing, but **cannot invent credentials or start PostgreSQL for you**.
2. From the repository root run:

   ~~~powershell
   .\start.bat
   ~~~

3. The launcher prepares the Python virtual environment and npm dependencies, applies Alembic migrations, then opens a dedicated VS Code window. Trust the workspace and allow folder-open tasks. The task runs a frontend production build, verifies migrations, and starts FastAPI and Vite in VS Code's **integrated terminals**.
4. If folder-open tasks are disabled, run **Terminal → Run Task → ProcurePilot: Build then Start (VS Code Terminals)**.

| Local address | Purpose |
| --- | --- |
| http://localhost:5173 | React UI |
| http://localhost:8000 | FastAPI |
| http://localhost:8000/docs | API schema (development only) |

### Backend-only environment

~~~dotenv
GOOGLE_API_KEY=
AI_MODEL=gemini-3.8-flash
CHANNEL3_API_KEY=
CHANNEL3_BASE_URL=https://api.trychannel3.com/v1
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
PAYPAL_WEBHOOK_ID=
~~~

See the [full provider setup guide](docs/provider-setup.md) for merchant vs buyer Sandbox accounts and webhook registration. `PAYPAL_WEBHOOK_ID` requires a webhook registered against a **public HTTPS** endpoint; localhost cannot accept PayPal's remote webhook deliveries. Keep all keys in the backend/root environment, never a `VITE_*` frontend setting or a commit.

### Checks before a judge demonstration

~~~powershell
.\verify.bat
~~~

This runs backend Pytest, frontend ESLint, Vitest and a Vite production build. It stops at the first failure. **Source-authored tests do not count as passing tests** until this command completes on a machine with the dependencies installed.

For a real end-to-end demonstration, additionally exercise registration, product discovery, Gemini analysis, purchase-order submission/approval, PayPal Sandbox buyer return, capture, and verified webhook delivery. See [development](docs/development.md), [testing](docs/testing.md) and [release verification](docs/release-verification.md). A frontend npm lockfile is not currently committed, so dependency resolution is not yet fully reproducible.

## Security and correctness: what's real, what's not

**Implemented:** Argon2id password hashing, short-lived JWT access tokens, user-owned record filters, strict approval status checks, server-derived PO prices/totals, product/offer snapshots, constrained model tool access, atomic daily AI-call quotas, bounded provider requests, PayPal order-and-capture verification, signed webhooks and duplicate-event handling, and user-visible audit records.

**Not production-certified:** true multi-person independent approval, durable edge/API request rate limiting, password reset/email verification, device/session revocation, concurrency-safe distributed payment reconciliation, browser E2E coverage, production monitoring/backup testing or live merchant receiving eligibility. The personal-workspace prototype allows self-approval. See [security posture and threat model](docs/security.md) for precise residual risks.

This is not a PCI-certified payment processor. The app does not capture card numbers, and it cannot represent PayPal Sandbox captures as real retailer payouts.

## Documentation and source layout

| Location | Contents |
| --- | --- |
| `frontend/` | React UI, views, routing, accessible controls, theme and favicon |
| `backend/app/api/` | Auth, procurement, approvals/order/payment and webhook HTTP routes |
| `backend/app/agents/` | Bounded Gemini/ADK runtime, evidence shaping and daily budgets |
| `backend/app/procurement/` | Deterministic requirements and product scoring |
| `backend/app/integrations/` | Channel3 and PayPal network clients |
| `backend/app/models/` | SQLAlchemy domain tables; Alembic migrations in `backend/alembic/` |
| `backend/tests/`, `frontend/src/**/*.test.jsx` | Unit/integration regression tests |
| `docs/architecture.md` | Domain architecture and trust boundaries |
| `docs/agent.md` | AI limits and safety engineering |
| `docs/security.md` | Implemented controls, threat model and remaining gaps |
| `docs/provider-setup.md` | Gemini, Channel3, PayPal Sandbox credentials |
| `docs/development.md` | Local startup and troubleshooting |
| `docs/release-verification.md` | Outstanding acceptance gates |

## Hackathon attribution and disclosure

**AI:** Gemini via Google ADK; catalogue discovery uses Channel3, and purchases/payments use deterministic FastAPI workflow controls and PayPal Orders v2 Sandbox. The recommendation is LLM-assisted; product prices, scores, stock evidence, payments and approvals are not fabricated by an LLM. Model costs are bounded but not guaranteed to be zero.

**Workflow:** Implement changes on `perez`, document meaningful commits, open a PR, merge into `main` and synchronize both branches. No GitHub Actions workflows.

**Copyright and license:** © 2026 PerezChris99. **All rights reserved. Authorized use only.** See [LICENSE](LICENSE), which grants narrowly scoped hackathon evaluator access but no general right to reuse, modify, sell or redistribute the project. **This is a proprietary license, not an OSI-approved open-source license.** If the hackathon requires an open-source license, the owner must resolve that conflict before submission.

### Public frontend deployment

The standard npm run build is a localhost-compatible Windows development check. For a real public deployment, set VITE_API_BASE_URL to https://YOUR-HTTPS-API-HOST/api/v1 or to /api/v1 behind a same-origin HTTPS reverse proxy. Then run npm run build:deploy from frontend/. That build gate refuses localhost/HTTP/malformed endpoints before generating public assets. Hosting services must explicitly choose build:deploy; normal npm run build remains a local check. The browser API layer also reports a clear misconfiguration instead of attempting to send a visitor's browser to localhost.

## Responsive layout and integration-state honesty

Phones and tablets below 961px use a six-destination fixed bottom dock (Overview, New, Orders, Approvals, Activity, Discover) with iPhone safe-area spacing and accessible link labels. Desktop screens retain a flat, no-pill sidebar. All six destinations are genuine routes; Activity and saved Product discovery no longer duplicate Purchase orders/New procurement. The status panel distinguishes **API reachable**, **database connected with required schema**, **credentials configured**, **partially configured**, and **not configured**. It reads real non-secret backend environment flags, refreshes on request and periodically, and never claims configured APIs have been authenticated with external providers.
