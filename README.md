# ProcurePilot AI

**From a purchasing request to an informed, approved purchase.**

ProcurePilot AI is an evidence-first procurement application that combines real catalogue discovery, deterministic product/price checks, a carefully bounded Gemini analyst, human-controlled approvals, and a PayPal Sandbox payment demonstration.

**Project status:** Functional prototype under active hardening. The Sandbox does not pay retailers, and a passing local build is not evidence of production readiness, unrestricted provider access, or high-load capacity.

## Installation and local development

**Local development requires Python 3.12+, Node.js 22.12+ (or 20.19+), npm and Git.** Mac/Linux first-run mode uses a local SQLite file so a PostgreSQL service is **not required just to open the app**. A real Channel3 search, Gemini analysis or PayPal Sandbox checkout requires the corresponding private provider credentials in the root `.env`; the app never invents provider results.

| Platform | Start | Verify |
| --- | --- | --- |
| Windows / VS Code | `.\\start.bat` | `.\\verify.bat` |
| macOS / Linux | `./start.sh` | `./verify.sh` |

### macOS

Install [Homebrew](https://brew.sh/) if needed, then open Terminal:

~~~bash
brew install git python@3.12 node
git clone https://github.com/PerezChris99/ProcurePilot-AI.git
cd ProcurePilot-AI
./start.sh
~~~

First launch creates local `.env` and `frontend/.env`, installs dependencies, applies database migrations, **builds React before starting**, then launches the backend and frontend in the current terminal. The command preserves any existing `.env`. Keep Terminal open; **Ctrl+C** stops both servers.

### Linux (Ubuntu / Debian)

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

### Windows and VS Code

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

**Start here:** `http://127.0.0.1:5173/` is now the public landing page; click **Get started** to register or **Sign in**. After authentication, the Overview is at `/dashboard`. The existing `/orders` PayPal Sandbox return URL is unchanged. Anyone can read About, How it works, Privacy, Terms, Security, Accessibility, Responsible use and Contact before signing in.

### Optional PostgreSQL and external providers

On macOS/Linux, `./start.sh --postgres` starts from the PostgreSQL template **only when no `.env` exists**. For an existing `.env`, change `DATABASE_URL` yourself; the script never overwrites it. Development SQLite is useful for exploring the UI and local flows; **production requires PostgreSQL**. In Windows, configure PostgreSQL before `.\start.bat`.

Supply `GOOGLE_API_KEY`, `CHANNEL3_API_KEY`, `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET` and an optional `PAYPAL_WEBHOOK_ID` to unlock those real provider workflows. The authenticated System status panel reports exactly which credential categories are set and which are missing. A configured key **does not** prove a provider API call works; live transactions and signed HTTPS webhooks must be demonstrated separately.

---

## Why ProcurePilot exists

A business purchase is more than a product-search query. Teams must express requirements, compare trustworthy offer evidence, stay within budget, document decisions, request human sign-off and reconcile a payment. Generic chatbots may invent stock or prices and cannot substitute for purchase controls.

ProcurePilot separates responsibilities: **the model explains, deterministic code decides what is orderable, people approve, and PayPal Sandbox demonstrates a verified payment lifecycle.** This makes a sophisticated workflow usable from a small set of clear screens.

## Five-minute product walkthrough

1. **Visit the public landing page, then register or sign in.** A short real-photo slideshow introduces procurement challenges and the workflow; your authenticated overview is now at `/dashboard`.
2. **New procurement.** Enter an unambiguous requirement, e.g. "Two 27-inch office monitors with IPS displays", quantity 2, currency USD and a reasonable budget. Product availability depends on the live catalogue.
3. **Ask AI to analyze** or **Search products**. Asking AI first automatically performs one Channel3 discovery if none has been saved, ranks the returned products in backend code, and sends a short shortlist to Gemini. Repeating an unchanged assessment uses its saved response without a new model call.
4. **Inspect the offers.** Only verified-in-stock, matching-currency, HTTPS offers within budget can become a purchase order. Review the retailer link, select **Create PO**, then **Submit for approval**.
5. **Approvals.** Open the dedicated Approvals screen, inspect the frozen item and price, and approve or reject. The personal-workspace demo permits the requester to approve their own order; this is explicitly **not independent segregation of duties**.
6. **Purchase orders → PayPal Sandbox.** Create a Sandbox checkout, sign in at PayPal using the **Sandbox Personal buyer**, approve in the same tab, return to ProcurePilot, and confirm capture. The backend checks the PayPal order and completed capture before marking it paid.
7. **Review the audit trail.** The order timeline and user-scoped dashboard show the actual events. A separate public HTTPS webhook can reconcile signed PayPal notifications.

**Required for the full Sandbox flow:** a Sandbox **Business merchant** REST application and credentials, a Sandbox **Personal buyer**, and the appropriate order/currency. A PayPal Sandbox payment does **not** pay a Channel3 retailer.

### Screen map

| Screen | Function |
| --- | --- |
| Public home | Concise hero, actual procurement photography, transparent technology integration strip, problem/solution, workflow, FAQs and CTA |
| About and legal pages | Public About, How it works, Privacy, Terms, Security, Accessibility, Responsible use and Contact |
| Overview | Personalized greeting, persisted order/approval statistics, recent audit events, a live date/time/timezone clock, activity counts and dynamic integration configuration (configured vs missing, not provider connectivity) |
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

## Environment configuration

~~~dotenv
GOOGLE_API_KEY=
AI_MODEL=gemini-3.8-flash
CHANNEL3_API_KEY=
CHANNEL3_BASE_URL=https://api.trychannel3.com/v1
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
PAYPAL_WEBHOOK_ID=

# Required for public authentication / shared rate limits
RATE_LIMIT_REDIS_URL=rediss://USER:PASSWORD@REDIS_HOST:6380/0

# Bound the number and duration of PostgreSQL connections per worker
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=5
DB_POOL_TIMEOUT_SECONDS=10
DB_CONNECT_TIMEOUT_SECONDS=5
DB_STATEMENT_TIMEOUT_MS=15000
DB_LOCK_TIMEOUT_MS=3000
DB_IDLE_TRANSACTION_TIMEOUT_MS=15000
MAX_REQUEST_BODY_BYTES=1048576
~~~

See [Scaling, operations and capacity planning](docs/scaling.md) for Redis, database pool sizing, least-privilege DB roles, load tests and production operations. See the [full provider setup guide](docs/provider-setup.md) for merchant vs buyer Sandbox accounts and webhook registration. `PAYPAL_WEBHOOK_ID` requires a webhook registered against a **public HTTPS** endpoint; localhost cannot accept PayPal's remote webhook deliveries. Keep all keys in the backend/root environment, never a `VITE_*` frontend setting or a commit.

### Verification

~~~powershell
.\verify.bat
~~~

This runs backend Pytest, frontend ESLint, Vitest and a Vite production build. It stops at the first failure. **Source-authored tests do not count as passing tests** until this command completes on a machine with the dependencies installed.

For a real end-to-end demonstration, additionally exercise registration, product discovery, Gemini analysis, purchase-order submission/approval, PayPal Sandbox buyer return, capture, and verified webhook delivery. See [development](docs/development.md), [testing](docs/testing.md) and [release verification](docs/release-verification.md). A frontend npm lockfile is not currently committed, so dependency resolution is not yet fully reproducible.

## Security and correctness: what's real, what's not

**Implemented:** Argon2id password hashing, short-lived JWT access tokens, user-owned record filters, strict approval status checks, server-derived PO prices/totals, product/offer snapshots, constrained model tool access, atomic daily AI-call quotas, bounded provider requests, PayPal order-and-capture verification, signed webhooks and duplicate-event handling, and user-visible audit records.

**Not production-certified:** true multi-person independent approval, durable distributed rate limits for API routes beyond authentication, password reset/email verification, device/session revocation, concurrency-safe distributed payment reconciliation, browser E2E coverage, production monitoring/backup testing or live merchant receiving eligibility. The personal-workspace prototype allows self-approval. See [security posture and threat model](docs/security.md) for precise residual risks.

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
| `docs/INTEGRATION_ACCEPTANCE.md` | Six gate Gemini, Channel3, PayPal, webhook and local-build acceptance; read-only provider smoke instructions |
| `docs/HACKATHON_TOP3_STRATEGY.md` | Researched official criteria, hard license blocker and ranked top-three feature proposals (deferred until 'suggest execute') |
| `docs/scaling.md` | Capacity planning, database operations, load testing, incident recovery and security boundaries |

## Technology, licensing and disclosure

**AI:** Gemini via Google ADK; catalogue discovery uses Channel3, and purchases/payments use deterministic FastAPI workflow controls and PayPal Orders v2 Sandbox. The recommendation is LLM-assisted; product prices, scores, stock evidence, payments and approvals are not fabricated by an LLM. Model costs are bounded but not guaranteed to be zero.

**Workflow:** Implement changes on `perez`, document meaningful commits, open a PR, merge into `main` and synchronize both branches. No GitHub Actions workflows.

**Hackathon eligibility:** The public repository contains an OSI-approved [MIT License](LICENSE) (SPDX `MIT`). The original author retains copyright while allowing use, modification and redistribution under its standard notice condition. See [NOTICE](NOTICE) for attribution and third-party asset boundaries.

**Copyright and license:** © 2026 PerezChris99. Licensed under the [MIT License](LICENSE). Copyright is retained by the author; software reuse, redistribution and commercial use are permitted subject to MIT notice requirements. Product and third-party names do not confer trademark or endorsement rights.

## Public frontend deployment

The standard npm run build is a localhost-compatible Windows development check. For a real public deployment, set VITE_API_BASE_URL to https://YOUR-HTTPS-API-HOST/api/v1 or to /api/v1 behind a same-origin HTTPS reverse proxy. Then run npm run build:deploy from frontend/. That build gate refuses localhost/HTTP/malformed endpoints before generating public assets. Hosting services must explicitly choose build:deploy; normal npm run build remains a local check. The browser API layer also reports a clear misconfiguration instead of attempting to send a visitor's browser to localhost.

## Readability, contrast and brand accessibility

ProcurePilot uses **Whitesmoke** `#F5F5F7` for calm backgrounds, **Sky Blue** `#38BDF8` for digital accents, and restrained **Warm Yellow** `#FFD66B` for its closing call to action and meaningful caution states. **Midnight Navy** `#0B1B3D` anchors text and dark surfaces. Decorative yellow underlines, section bars, and metric-card edges are intentionally avoided.

Public, account and workspace interfaces now use a browser-scalable 16px root, larger text (typically 14–18px for secondary copy and controls, with 16px inputs and body text), stronger contrast and more generous line-height. The universal six-link mobile navigation keeps a short label and high-contrast active marker, even at narrow phone widths. Users can zoom the page using normal browser controls without relying on downloaded fonts. The design preserves reduced-motion preferences and visible keyboard focus. See [Accessibility and visual design](docs/accessibility.md) for checks and current limitations.

## Responsive layout and integration-state honesty

A single iPhone-style bottom navigation dock now appears on **all mobile-sized screens below 961px**, including the public landing page, About/legal pages, sign-in/registration and the authenticated workspace. Public pages expose Home, Why, How, FAQ, About and Account (or Workspace when signed in); inside the app it retains the complete six-destination sidebar set: Overview, New, Orders, Approvals, Activity and Discover. The dock uses iPhone safe-area spacing, clear active states, accessible link labels and no colored active pills. Desktop screens retain a clean site header or a flat workspace sidebar. All six destinations are genuine routes; Activity and saved Product discovery no longer duplicate Purchase orders/New procurement. The status panel distinguishes **API reachable**, **database connected with required schema**, **credentials configured**, **partially configured**, and **not configured**. It reads real non-secret backend environment flags, refreshes on request and periodically, and never claims configured APIs have been authenticated with external providers.

## Public landing, photo sources and deployment routing

The public root `/` now introduces the problem and product in a compact editorial layout. A controlled three-frame **real photography** carousel (warehouse sourcing, team purchasing decisions, office workflow) has previous/next and pause controls, motion-reduction handling, descriptive image text and a light fogged-glass tint. Photography is served over HTTPS by Unsplash, governed by the [Unsplash License](https://unsplash.com/license); the site uses these images as illustrative editorial photos, not customer proof. The social-proof strip names the actual technology stack, **not customers, partners or endorsements**. The slideshow needs internet access to load its remote images.

The authenticated Overview moved to `/dashboard`. Other purchasing routes and PayPal's `/orders` return route are preserved. Public About, How it works, Privacy, Terms, Security, Accessibility, Responsible use and Contact are available from the footer without a login. These prototype legal notices should receive owner/counsel review before a commercial launch.

For static hosting, `frontend/vercel.json` provides Vercel's SPA rewrite when the project root is `frontend/`, and `frontend/public/_redirects` provides Netlify's SPA fallback for direct legal and workspace URLs. Configure the public frontend's HTTPS backend address as `VITE_API_BASE_URL` and use `npm run build:deploy`. A simple successful `npm run build` alone does not prove a deployed domain, API connection or provider access.

## Performance and security boundaries

The protected Overview also shows a ticking local device time, date, IANA time zone and UTC offset. The backend now enforces finite and range-checked money, a 1 MiB HTTP request body limit, size-limited external catalogue responses, human approval and server-verified PayPal Sandbox evidence. Public authentication uses **shared Redis rate limiting** and fails closed if that service is unavailable. Secrets are never returned by the integration-status endpoint, and production API responses include defensive headers. Database access uses bounded PostgreSQL connection pools, SQL/lock timeouts, composite user-scoped indexes, unique PayPal capture/order IDs, keyset pagination for saved procurement lists and bounded audit summaries; complete order audit data remain available through the individual order endpoint.

**Capacity is not a fixed user-count guarantee.** Running 100,000 or 1,000,000 accounts reliably depends on concurrent load, provider quotas, query plans, data volumes, infrastructure, backups, autoscaling and security monitoring. Use the [scaling and capacity guide](docs/scaling.md) and demonstrate throughput and p95/p99 latency through real load and failure testing before advertising those levels. Separating signed-in user accounts from simultaneous active sessions is essential.

### Public visual language

The public site follows a refined, original fintech design rather than imitating another company's interface: clear hierarchy, confident typography, restrained blue accents, real editorial procurement photography with a translucent mist, and subtle accessible motion. The same responsive navigation behavior is shared across public, account and private routes. The photography is illustrative, not a customer endorsement. Motion follows system reduced-motion preferences, and the hero slideshow retains manual next/previous/pause controls.

## Full-width public layout and concise workspace

The landing page has returned to a **calm, centered 1180px maximum-width editorial layout** with a classic text-left and photograph-right split hero. The rectangular photo carousel remains 510px tall on desktop, with accessible slideshow controls and a readable photo caption. The headline and CTAs live on the paper-white surface beside the image, not on top of it. At mobile/tablet widths, content stacks with comfortable spacing. A light paper palette, reduced font weights and restrained blue/navy accents replace the former full-width, high-contrast treatment. A subtle bounded desktop-only parallax effect and native smooth anchor scrolling remain, both respecting reduced-motion settings.

The signed-in Overview prioritizes the greeting, **New procurement** action, live saved counts, recent events and actual integration status. Four metrics now share a single rectangular, neutral summary surface with fine dividers, not colored card borders or decorative rounded tiles. The extra promotional hero, duplicate explanatory sentences, and unnecessary site copy were removed; provider and PayPal Sandbox limitations are still accurately disclosed. Visual regression and runtime acceptance guidance is in [docs/testing.md](docs/testing.md).
