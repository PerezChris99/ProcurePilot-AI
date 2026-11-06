# ProcurePilot AI — Prize-focused technical and submission audit

**Review date:** November 6, 2026 · **Basis:** `main` source and official
[Devpost event](https://paypalaihackathon.devpost.com/) /
[rules](https://paypalaihackathon.devpost.com/rules).
**Audit boundary:** repository/read-through plus the maintainer's statement
that the nine offline QA gates passed. This is **not** a fresh execution of
every Python/React test, a penetration test, a Render session, or a live
PayPal/Channel3/Gemini acceptance run.

## Executive assessment

The project has a credible technical core for a strong submission: meaningful
Channel3 data retrieval, Google ADK evidence comparison, hard buyer-policy
gates, protected approval, actual PayPal Sandbox Orders v2 endpoints,
independent capture/webhook verification, and a distinctive **Decision
Passport**. It is substantially beyond a static prototype.

**But winning is not a test outcome.** A flawless mocked suite can lose to a
well-filmed, accessible, live working demo. The biggest remaining risks are
missing public judge access, unverified end-to-end PayPal Sandbox buyer
journey and webhook, provider rate-limit variability, missing YouTube video,
uncertain asset permissions and a not-yet-submitted Devpost entry.

## Official rules: pass/fail compliance

| Requirement | Source evidence | Status |
| --- | --- | --- |
| Meaningfully integrates PayPal **Sandbox** and AI | `backend/app/integrations/paypal/client.py`, `backend/app/agents/runtime.py`, `backend/app/api/purchase_orders.py` | **Implemented in source; live acceptance outstanding** |
| Functional, consistently runnable demo | Existing Windows/macOS/Linux launchers; new isolated `judge-preview.py` | **Offline run supported; complete third-party judge access outstanding** |
| Text description and named AI tools | `README.md`, `docs/HACKATHON_SUBMISSION_KIT.md` | **Draft ready; must copy/verify on Devpost** |
| Public code + visible OSI-compatible license | Public repo, detected `MIT` license | **Verified via GitHub metadata** |
| Demo video on public YouTube, under 3 minutes | Recording/storyboard instructions only | **Not produced/verified** |
| Judge/testing access through Dec 15, 2026 | Render runbook, no confirmed hosted URL or private judge credentials | **Not verified — critical** |
| Accuracy/IP/rights/eligibility | No fabricated settlement claims in source; `NOTICE`, licence | **Entrant must verify country/legal eligibility and third-party image/mark/music rights** |
| Substantial work during hackathon period | Git history and recent dated PRs | **Evidence exists; explain changes in submission** |
| Complete submitted Devpost entry | Cannot be verified from repository | **Not verified** |

### Prize portfolio and constraints

Official rules: **maximum one Grand Prize + one Sponsor Prize, or one
Honorable Mention + one Sponsor Prize**. Therefore competing in many
categories does **not** mean collecting many awards.

| Category | Award | Fit today | Strategy |
| --- | ---: | --- | --- |
| **1st Overall** | **$12,000 cash** | Ambitious, credible if live demo is excellent | **Primary target** across all five equal criteria |
| 2nd / 3rd Overall | $8,000 / $5,000 cash | Alternate overall outcomes | Same submission quality |
| Best Use of PayPal + AI | $5,000 cash | Strong only after proving genuine end-to-end Sandbox and meaningful AI decision context | Honorable alternative |
| Best Use of Agentic Commerce | $5,000 cash | Partial: ADK analyst assists but does **not** autonomously transact | Describe *human-controlled* agentic assistance, never invented autonomy |
| Best Demo Delivery | $5,000 cash | Strong potential **after** a polished, real 2:45 video | Storyboard + mobile/desktop legibility |
| Most Impactful / Most Creative | $5,000 cash each | Demonstrable pain point and Decision Passport, but **no verified external impact study** | Evidence-backed use case, not invented ROI |
| **Best Use of Channel3** | **$1,500 cash** | Best defensible sponsor fit in current code | Show real source/rejections, recheck, proven provenance |
| Best Use of Render | $1,000/$750/$500 **in credits** | **Only after a working Render deployment** | Supportive, not proof of hosted infrastructure today |
| Best Use of AG Grid | Up to $5,000 cash | **Not eligible today**: AG Grid is not integrated | Add only if it adds demonstrable comparison value **after** live flow is stable |
| APIMatic / Bryntum | $1,000 + partner extras where offered | **Not integrated today** | Do not claim eligibility |

Maximum obvious cash combination with *current* sponsor integration,
assuming the awards are won, is **1st Overall ($12,000) + Channel3
($1,500) = $13,500**. AG Grid 1st offers a potentially larger permitted
combination ($17,000), but it would require genuine integration and winning
that sponsor prize; adding it purely to tick a box is a risky distraction.

## Five equally weighted judging criteria: evidence-driven attack plan

| Judge axis | Current advantage | Unresolved weakness | Best next action |
| --- | --- | --- | --- |
| **Technological implementation** | Real PayPal OAuth/create/capture/webhook code, ADK, fallback, SQL policy, stored evidence, explicit safe failures | No confirmed live buyer/capture/webhook under public HTTPS; race/recovery edge cases remain | Record a reproducible Sandbox E2E with actual IDs and verified amount |
| **Design** | Paper-white brand, legible fonts, accessible responsive pages, per-action loading, activity and Decision Passport | Physical mobile/browser UX not independently validated; empty/error states need demonstration | Rehearse at 375/768/1440px with keyboard and reduced motion |
| **Potential impact** | Small-team/nonprofit purchasing use case, explainable rejection, owner/approver record, PDF audit | No real user case study, time-saved baseline or verified savings figure | One buyer scenario + honest numerical counterfactual from real eligible offers |
| **Innovation** | **Decision Passport** fuses product policy, AI explanation, human authorization and payment proof | Many rivals also use agents, budgets and shopping; differentiation must be visible | Make alternative rejection and payment provenance the signature reveal |
| **Presentation** | Coherent end-to-end narrative and storyboard ready | Public 2:45 video, screenshot set, hosted link and Devpost submission unverified | Produce **one continuous credible story**; ensure first 15 seconds establish problem |

Avoid claiming 100% production security, LLM correctness, delivery guarantees,
actual retailer checkout or proven financial savings. Sound engineering
boundaries tend to outperform invented polish under technical questioning.

## Technical audit: verified source and honest limitations

**Implemented source review**
- Authenticated, user-scoped buyer records; Argon2id/JWT; Redis-backed public
  login/registration throttling with fail-closed behavior when unconfigured.
- Channel3 search/offer retrieval, pagination, normalized product evidence,
  recent-snapshot requirement, exact offer HTTPS/currency/stock/price policy.
- Explicit requested monitor diagonal mismatch prevention; invalidation of
  outdated policy/AI snapshots.
- Small untrusted-evidence packets, bounded ADK response, up to two
  provider backups, global/user daily SQL quota, no AI purchase tools.
- Human-owned/default approval and distinct optional registered delegated
  approver; no organization-wide RBAC or verified external buyer identity.
- PayPal Sandbox-only guard, signed webhook API, exact payment amount and
  currency checks, stable request IDs, replay-safe state paths and audit events.
- Frozen Decision Passport, PDF export, dashboard, public legal/info pages,
  responsive UI contract tests and nine-gate offline QA system.
- Public repository with GitHub-recognized MIT license.

**Not proven by this audit**
- Real PayPal buyer approval and capture across Render frontend/API;
  real signed/duplicated webhook delivered from PayPal.
- Stable live Channel3 offer availability at the time a judge starts testing,
  successful Gemini and fallbacks under rate-limits or no quota.
- PostgreSQL migrations/restore in actual deployed environment, all CORS
  origins, Redis connectivity, hosted SPA rewrites or security headers.
- Live cross-device browser E2E, keyboard screen-reader acceptance,
  site performance and load/failure injection; the existing suite is offline.
- Distributed payment reconciliation for ambiguous network outcomes,
  refunds/disputes, enterprise authorization or actual retail settlement.
- A public YouTube demo, private judge test access or submitted Devpost form.

## P0: must finish before submission (strict priority)

1. **Rotate exposed service credentials** using Google, Groq, OpenRouter,
   Channel3 and PayPal provider consoles. Re-enter rotated secrets in hosting;
   do not republish them or place personal test passwords in source.
2. **Deploy a judge-accessible HTTPS frontend + backend** with actual
   PostgreSQL, auth rate-limit Key Value, exact CORS origin and Alembic
   migrations. Follow [Render runbook](RENDER_DEPLOYMENT.md); do not pick
   a Workflow instead of Web/Static services.
3. **Rehearse and record live integrations** using a test user and distinct
   Sandbox Business merchant / Personal buyer: verified Channel3 search,
   actual Gemini/ADK output or disclosed fallback, create eligible PO, human
   approval, PayPal checkout, return, explicit capture, paid state and Passport.
4. **Verify HTTPS webhook signature handling** and duplicate delivery. Check
   pending/denied/mismatch cases without replaying any real payment.
5. **Publish a public 2:40–2:50 YouTube video**, capture 4–6 authentic
   screenshots, and use the copy-ready [submission kit](HACKATHON_SUBMISSION_KIT.md).
6. **Submit Devpost before Nov 12 23:00 EAT**. Verify the entry is submitted,
   not a draft. Keep the demo free, working and accessible through Dec 15.
7. **Inspect intellectual property**, external image licensing, use of any
   logos/music, and entrant legal eligibility. These are legal/account tasks,
   not matters that passing unit tests can prove.

## P1: strongly valuable before video capture

- Run a complete hosted browser acceptance on Windows, Android-sized viewport,
  mobile navigation, 375/768/1440 widths, keyboard/reduced-motion support.
- Demonstrate the **negative case**: request 72-inch monitors; 24-inch
  products and monitor stands must not be ordered due to cheap prices.
- Show one transparent **counterfactual**: cheapest *eligible* total vs
  selected total in the same currency, explicitly excluding shipping/tax.
- Demonstrate model fallback safely without falsely claiming a generated
  answer from an unavailable provider. Retain the provider label and usage.
- Confirm the deployed health + DB readiness endpoints, permanent database,
  mobile route refresh, payment return, private test user and password hygiene.
- If available, obtain qualitative feedback from 1–2 actual purchasers and
  attribute it only with their permission; otherwise omit testimonials.

## P2: do not trade a working demo for optional extras

- Genuine AG Grid comparison *only* if it improves judge clarity and can
  pass full QA and mobile acceptance before the video freeze.
- Render Workflow *only* for clearly idempotent, nonpayment background
  research; avoid worker auto-retries for payments.
- Major new roles, actual retailer ordering, bank/merchant live settlement,
  subscriptions, browser purchase agents and untested autonomous tasks are
  out of scope for this six-day shipping window.

## Schedule — November 6–12 (Uganda time)

| When | Deliverable / exit criterion |
| --- | --- |
| Nov 6–7 | Rotate secrets; establish stable HTTPS Render demo, DB and auth; validate fresh signup and product discovery |
| Nov 7–8 | Run real Gemini, Channel3 and Sandbox test buyer approval/capture + webhook; document proof and repair blockers |
| Nov 9 | Complete device/browser accessibility rehearsal and record actual screenshots; freeze demo scenario |
| Nov 10 | Record 2:45 demo video; review for secret leakage, legibility and honest payment attribution |
| **Nov 11** | Final QA/regression pass, release freeze, public video, working demo, Devpost submit **one day early** |
| Nov 12 23:00 EAT | **Absolute submission cutoff**; contingency only, not intended first submission |
| Dec 1–15 | Keep hosted demo free, stable, accounts available, monitor and preserve authorized audit logs |
| Around Dec 21 | Official anticipated winners announcement |

## Final gate that cannot be bypassed by documentation

Before marking this project *hackathon-submission-ready*, the owner must
supply or independently verify all of: a live hosted/reproducible full
integration URL, permitted test access, a real PayPal Sandbox capture and
webhook proof, successful browser/phone test, a real public YouTube link,
and Devpost's final **submitted** confirmation.

A 9/9 green offline QA report is excellent evidence of engineering
discipline—**it is not proof of any of those external requirements**.
