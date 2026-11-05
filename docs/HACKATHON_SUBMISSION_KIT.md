# ProcurePilot AI — PayPal AI Hackathon submission kit

**Prepared:** 2026-11-05 · **Deadline:** 2026-11-12 12:00 PST / 23:00 EAT.
**Status:** submission materials are drafts. Replace fields marked `[VERIFY]` only after checking them. The video, hosted URL, live Sandbox evidence and formal Devpost submission must be completed by the entrant.

## Project name
**ProcurePilot AI — Every Purchase Has a Reason**

## One-line pitch
**Accountable AI-assisted purchasing:** real product evidence, deterministic buyer policies, human approvals, and traceable PayPal Sandbox outcomes in one decision record.

## Devpost project description — ready to adapt

### Inspiration
A business purchase is rarely just a checkout. Someone must explain why the selected product satisfies the request, why other offers were rejected, whether the amount meets policy, who approved it, and what actually happened at payment. Email threads and shopping tabs do not produce that record.

### What it does
ProcurePilot AI turns a business purchasing request into an accountable decision trail. A buyer defines what they need and optional hard constraints. Channel3 supplies actual catalogue product and retailer offer data. ProcurePilot checks price, currency, stock, specification evidence and spending limits in deterministic Python. Gemini, running through Google ADK, explains the shortlist without being given approval or payment authority. A human then authorizes an eligible purchase order. PayPal Orders v2 Sandbox demonstrates the payer-approval and capture lifecycle.

The **Decision Passport** ties the saved request, eligible and rejected offers, source timestamp, AI reasoning, signed-in human approval, PayPal Sandbox order/capture metadata and audit history into an inspectable JSON/PDF export. Comparisons are based on eligible offers in the same currency—not invented savings. External delivery, tax and supplier settlement remain explicitly unverified.

### How we built it
Frontend: React, Vite and accessible responsive UI. Backend: FastAPI, SQLAlchemy, Alembic and PostgreSQL/SQLite for local development. Integrations: Channel3 REST API for catalogue results, Gemini through Google ADK for bounded explanation, PayPal Orders v2 Sandbox for payment authorization/capture and authenticated signature-verified webhooks. Protection includes server-scoped records, deterministic buyer mandates, request quotas, password hashing, limited-source evidence packets, idempotent payment request identifiers, amount/currency verification and audit events.

### Key implementation decisions
- **The model explains; code decides.** Gemini cannot initiate, approve or capture payments.
- **Policies are executable.** Mandatory attributes, merchant domains, amount/budget limits and expiry block noncompliant offers.
- **A buyer actually approves.** An optional designated registered reviewer can separately approve/reject without payment privileges.
- **The evidence is frozen.** A Decision Passport captures the original selected offer and comparisons; optional Channel3 quote rechecks do not silently rewrite an approved amount.
- **PayPal is central.** The Sandbox workflow uses OAuth, server-side order creation, buyer approval, capture verification and audited webhook handling. The app refuses live PayPal API operations in the hackathon build.
- **Demo honesty.** Clearly labeled offline samples cannot become payable orders; live Channel3, Gemini and Sandbox proof must be demonstrated separately.

### Challenges and lessons
Combining untrusted catalogue listings, generative explanation and financial actions requires separating **suggestions** from **authority**. Missing stock, nonmatching merchant domains, stale quotes, invalid amounts and webhook retries should produce safe, understandable outcomes—not plausible-looking purchases. We designed the demo to retain meaningful evidence even when AI or catalogue calls fail.

### Accomplishments
The repository contains an end-to-end purchase workflow, owner-scoped requests/orders, human decision records, signed-webhook handling, source-grounded comparisons, a Decision Passport and exports. **Do not claim these passed live integration tests until the acceptance checklist is completed.**

### What comes next
Independent, organization-managed approvals and accounting integrations; continuous merchant price monitoring; improved exact-once reconciliation and reconciliation-after-timeout; verified supplier settlement through a separately authorized commerce provider; production operations and user research. These are roadmap items, not shipped features.

### Intended users and impact
Small purchasing teams, nonprofits and growing businesses that need to show **why** a purchase was approved. In the demonstration, two office monitors must satisfy an explicit specification, stock, price and budget. The cheapest product may be the wrong product. ProcurePilot explains that difference instead of merely displaying a shopping cart.

### Links
- Source (MIT): https://github.com/PerezChris99/ProcurePilot-AI
- Demo: **[VERIFY — provide live judge-accessible HTTPS URL or complete local setup steps]**
- Public YouTube video (under 3 minutes): **[VERIFY — upload and link]**
- Integrations: https://github.com/PerezChris99/ProcurePilot-AI/blob/main/docs/INTEGRATION_ACCEPTANCE.md
- MIT notice: https://github.com/PerezChris99/ProcurePilot-AI/blob/main/LICENSE

## Three-minute video storyboard — target 2:40

| Time | Screen/action | Suggested narration | Proof to capture |
| --- | --- | --- | --- |
| 00:00–00:14 | Paper-white landing / one clear problem statement | “Buying for a team is a decision, not just a payment. Can we prove why we chose an offer?” | Clean site and real workflow entry |
| 00:14–00:32 | Create request: two 27-inch monitors, budget and required size | “We define the need and a machine-checkable mandate before looking at products.” | Exact specs, quantity, total budget |
| 00:32–00:54 | Real Channel3 results and comparison | “Channel3 supplies offers. We reject the cheaper option when the required specification or availability is not evidenced.” | Real IDs and matching prices; eligibility reasons |
| 00:54–01:15 | Actual Gemini/ADK analysis | “Gemini explains the evidence. It cannot approve an order or transfer money.” | Real response, transparent source, no invented status |
| 01:15–01:39 | Create PO, review and human approval | “The selected offer and amount are frozen. A person explicitly approves the purchase.” | Exact price math, approval actor |
| 01:39–02:08 | PayPal Sandbox checkout and verified capture | “PayPal handles payer approval and Sandbox capture. Our server validates the order and final amount.” | **Real separate Sandbox buyer**, returned capture ID |
| 02:08–02:28 | Decision Passport / audit chain | “One passport connects requirement, alternatives, AI evidence, approval and the Sandbox payment proof.” | Exportable JSON/PDF and source timestamps |
| 02:28–02:40 | Closing and honest disclosure | “ProcurePilot makes the purchase explainable. Sandbox payments do not settle the original retailer.” | Name, source/demo URL |

**Rule:** The final recording must show the actual working browser, not wireframes or a mocked payment completion. Never display passwords, private API keys, a real buyer identity or a production PayPal transaction. Do not use another company's logos or copyrighted music in promotional materials without permission.

## The four memorable proof moments

1. **Rejected cheaper option:** Use real Channel3 offers with a genuine reason for rejection (or clearly labeled offline examples only for the non-payable preview). Explain the blocked policy.
2. **No AI payment authority:** Show the bounded Gemini assessment and the still-required human approval action.
3. **Exact Sandbox transaction:** Show that the approved total, PayPal order amount and completed capture amount match, and repeated capture does not cause a second payment.
4. **Decision Passport:** Show evidence timestamp, selected/alternate offer prices, who decided, payment status and audit event chain. Avoid saying that a SHA-256 checksum is independent notarization.

## Final acceptance checklist — must be observed, not inferred

- [ ] GitHub detects the repository's MIT license and source is publicly readable.
- [ ] Frontend production build, Node tests/lint, Python tests, Alembic migration from scratch and upgrade from existing DB pass.
- [ ] Channel3 API returns real current products and a valid comparable priced offer; invalid/empty states fail gracefully.
- [ ] Gemini ADK returns genuine grounded analysis on the real saved offer list, and repeats are cached.
- [ ] Assigned reviewer (if used) is distinct from requester; reviewer cannot create/capture payment.
- [ ] User can generate an accurate JSON and readable PDF Decision Passport; another user cannot retrieve it.
- [ ] PayPal Sandbox merchant OAuth, separate personal-buyer approval, server-verified capture and exact amount/currency all pass.
- [ ] Valid signed HTTPS webhook, duplicate event, missing signature and amount mismatch are safely handled.
- [ ] Real PayPal Live API host is refused by the hackathon backend.
- [ ] At 320, 375, 768, 960, 1024 and 1440px layouts remain legible and all actions usable; 200% zoom and reduced-motion pass.
- [ ] Judge can access a hosted HTTPS demo or reliably run documented steps; keep it accessible through Dec 15.
- [ ] Public YouTube video is under 3 minutes, shows a real functional run and is linked from the Devpost entry.
- [ ] Submission text lists actual AI tooling, real changes during the hackathon and truthful limitations.
- [ ] Screenshots, offer data and imagery comply with third-party licensing and provider terms.
- [ ] Devpost submission confirmed **before 23:00 EAT on Nov 12**.

## Judges' five equal criteria — evidence map

| Criterion | What to point judges to | Remaining proof |
| --- | --- | --- |
| Technical implementation | FastAPI safeguards, real Channel3+ADK+PayPal code, idempotency, signature checks, migrations, tests | Live payment/webhook and full test logs |
| Product design | Calm paper-like landing/dashboard, explainable offer cards, human decisions, mobile icons | Browser/phone walkthrough |
| Impact | Specific small-team monitors scenario, eligibility reasons, audit trail | Credible buyer feedback, not invented ROI |
| Innovation | Frozen Decision Passport integrating a source/decision/payment proof chain | Competitive differentiation in video |
| Presentation | One coherent story with exact evidence and honest Sandbox caveat | Actual public 2:40 video and accessible demo |

## Unfinished external duties

The repository cannot generate real OAuth credentials, a successful PayPal buyer approval, a publicly hosted deployment, an uploaded YouTube video or a Devpost submission merely by merging source. Those are separate, required acceptance stages. There is no honest way to guarantee a top-three placement.
