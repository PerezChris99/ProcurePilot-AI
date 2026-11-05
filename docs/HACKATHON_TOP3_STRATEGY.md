# ProcurePilot AI — Top-Three Hackathon Strategy and Delivery Status

Research date: **2026-11-05**. Competition: **PayPal AI Hackathon / “Build What's Next with PayPal and AI”**. Objective: a credible shot at the **top three overall**, plus the most relevant sponsor category. Project: **ProcurePilot AI**. The owner subsequently authorized implementation. The source now includes substantial P1–P3 work; the separate external-provider, browser, operational and submission gates remain unverified. This document distinguishes implemented source from unfinished proof.

## 1. Competition ground truth

- **Deadline:** Thursday, November 12, 2026, **12:00 p.m. PST / 20:00 UTC / 23:00 EAT (Uganda)**. Aim to submit at least a day early; the deadline is not a target for the first functioning build.
- **Judging:** Stage 1 is a pass/fail check for theme viability and actual required API use. Stage 2 has **five equally weighted criteria**: (1) technical implementation, (2) design, (3) potential impact, (4) innovation/idea, (5) presentation. Technical implementation is the first tie breaker.
- **Mandatory:** meaningful PayPal developer-platform integration **and** meaningful AI; functional demo accessible to judges (public hosting or reproducible local build), a **public repo with a discoverable open-source license**, sufficient setup instructions, detailed explanation of AI tools, and a **public YouTube video under three minutes** showing real operation. Avoid unauthorized third-party trademarks/music.
- **Prize routes:** 1st overall $12,000; 2nd $8,000; 3rd $5,000; $5,000 honorable mentions including Best Use of PayPal + AI, Best Use of Agentic Commerce, Most Impactful, Most Creative and Best Demo Delivery; Channel3 sponsor prize $1,500. Only one overall or one honorable mention, plus at most one sponsor prize, may be awarded to the same submission.
- **Participant count:** 27,892 was reported by the entrant and the Devpost count changes over time. Participants are **not identical to eligible, completed submissions**, so do not calculate winning probability from registrations or assume a predictable cutoff.
- **Open-source licensing (resolved in source):** The owner-authorized MIT LICENSE now meets the repository's open-source license format requirement; verify that GitHub detects `MIT` on the public repository page and that the entire submission and all third-party assets comply. Copyright remains with the licensor. This does not prove judge eligibility by itself.
- **Judge access:** Make a working copy available without fees/restrictions through the judging period ending December 15. Prefer a hosted HTTPS demo plus exact fallback local instructions. Provide controlled demo credentials through the submission/testing instructions; never publish actual API secrets, Sandbox REST client secrets or personal test-buyer passwords in git.

Primary sources:
1. Official rules: https://paypalaihackathon.devpost.com/rules
2. Event/prizes/criteria: https://paypalaihackathon.devpost.com/
3. Dates: https://paypalaihackathon.devpost.com/details/dates
4. Channel3 sponsor: https://paypalaihackathon.devpost.com/details/channel3
5. PayPal announcement: https://developer.paypal.com/community/blog/PayPal_AI_Hackathon/
6. PayPal Sandbox guide: https://developer.paypal.com/sandbox-testing/overview/
7. Official PayPal Orders: https://developer.paypal.com/api/rest/integration/orders-api
8. Channel3 official API guidance: https://github.com/channel3-ai/skills/blob/main/skills/channel3-api/SKILL.md

## 2. Strategic thesis

**Category:** verifiable, human-controlled, AI-assisted procurement—not a generic chatbot or “AI buys anything” demo.

**One-sentence pitch:** “ProcurePilot turns a buying request into a defensible purchasing decision: live catalogue offers, documented AI comparison, deterministic budget and stock checks, human approval, and a verifiable PayPal Sandbox checkout—all in one audit trail.”

**Credibility rule:** PayPal Sandbox validates a payment **to the configured sandbox merchant**, **not a payment to the Channel3 retailer**. Neither the current product nor the pitch should imply automatic supplier settlement, real cash transfer, actual inventory reservation, live delivery tracking or verified shipping. Judges may penalize false claims more severely than a narrow but honest prototype.

**Where to differentiate:** Other publicly discoverable hackathon entries already demonstrate Channel3+PayPal shopping, split payments, mandates, policy guards or settlement ledgers. For examples, see https://devpost.com/software/cartsplit-ai-paypal-ai-hackathon-2026-demo and https://devpost.com/software/mandate-o2psny . These are public claims by entrants, not independently benchmarked judging outcomes. A budget guard **alone** is not enough novelty. The moat should be *auditable, explainable trade-offs in organizational procurement*, supported by an excellent end-to-end demo.

## 3. Competitive work and actual status (source vs. acceptance)

| Rank | Proposed change | Value to judges | Implementation risk | Priority |
| --- | --- | --- | --- | --- |
| P0 | Verify MIT license detection + demo availability + reproducible setup | Pass/fail eligibility and demo access | Low engineering, **high owner/legal importance** | Mandatory |
| P0 | Live integration acceptance of Gemini/ADK, Channel3 and PayPal Sandbox | Technical implementation and real demonstration | Depends on third-party keys, accounts and HTTPS | Mandatory |
| P1 | **Procurement Decision Passport**: requirements, ranked offers and rejection reasons, approval, amounts, real Sandbox transaction/capture IDs and a downloadable human-readable evidence view | Distinct evidence-based procurement narrative; technological implementation + impact | Medium | Best signature feature |
| P1 | **Counterfactual savings & risk evidence**: show rejected cheapest offer, price difference to cheapest *eligible* offer, verified policy failures and uncertainty; never invent a savings total | Credible buyer benefit; mathematical rigor | Medium | High |
| P1 | **Buyer mandate and policy gates** beyond a simple budget: allowed merchant/domain, in-stock, currency, specs, max total, expiry; deterministic pre-payment re-check | Real controlled agentic commerce, trust and compliance | Medium/high | High, but generic mandate alone isn't novel |
| P1 | **PayPal proof chain**: signed approval→order→buyer approval→capture→webhook status, UI labels for each state, amount/currency assertions, idempotent retry, proof of non-duplication | Makes PayPal central rather than a logo at the end | Medium/high | Must be reliable |
| P2 | **Explainable alternatives**: compare 3 realistic products; “why not this one?” evidence for stock/specs/price, with source IDs and truthfulness indicators | AI usefulness + design + trust | Low/medium | If time remains |
| P2 | **Scenario-based demo mode**: seeded non-claiming procurement requests, screenshots, deterministic fixture fallback when provider is temporarily down, clearly labeled “sample data” | Exceptional reliability, no blank dashboard during judging | Medium | High leverage |
| P2 | **Single audit export** (PDF/JSON) with source timestamps, human decision, and Sandbox proof | Memorable differentiator / easy judge inspection | Medium | After proof chain |
| P3 | Realtime vendor refresh and price-change warnings using Channel3 product retrieval/subscriptions with proper URL freshness | Useful practical innovation but more external dependency | Medium/high | Only after core stable |
| P3 | Separate requester/approver identities, role-scoped organizational workspace and audit review | True enterprise credibility | High | Stretch; avoid unfinished RBAC |
| P3 | AG Grid evidence table / product comparison, if it visibly improves clarity; sponsor eligibility otherwise should not drive dependency bloat | Optional sponsor category | Medium | Only if meaningful |
| Defer | Browser automation shopping, actual retailer purchasing, speculative escrow, multiparty autonomous spending, voice gimmicks | Distracts from demo; risky and misleading without real rails | Very high | Do not prioritize |

### P1. Procurement Decision Passport — suggested MVP shape

Capture a cohesive **read-only timeline** of the same purchase:
1. Request metadata: canonical text, quantity, budget, currency, optional mandatory specifications, creation timestamp.
2. Channel3 search and offer snapshot: actual product IDs, merchant, amount/currency, availability, URL retrieval timestamp, source label, eligibility decision.
3. Deterministic decision: eligible/ineligible with exact reasons (missing spec, unavailable stock, different currency, budget fail). AI does **not** set the definitive payment or risk gate.
4. Evidence-grounded AI narrative: recommendation, trade-off, product IDs cited, token usage and model, unavailable/uncertain fields explicitly marked.
5. Human action: author identity, approval/rejection, timestamp and amount. For the current personal-workspace demo, state clearly that the requester can approve their own order; don't describe this as independent organizational separation.
6. PayPal Sandbox: one server-side order, payer approval state, verified completed capture ID and amount/currency, signed webhook/audit event and idempotency result.
7. A shareable/exportable *fact sheet*, with “Sandbox demonstration, not retailer settlement” clearly visible. If adding digest, describe it accurately as **tamper-evidence for captured data**, not a cryptographic guarantee that external data was truthful.

### P1. Credible numerical proof

Do not claim “we save 30%” without underlying evidence. For an actual request, compute comparisons from verified, like-for-like prices and quantity using one currency; include timestamps, exclude out-of-stock/ineligible items, and indicate when delivery/tax is unknown. A useful screen explicitly explains why the apparently cheapest product was rejected and why a slightly dearer eligible product was approved. Present a **plausible quantitative example**, clearly marked a demonstration, not measured business-wide ROI.

### P1. PayPal centrality

Judges explicitly assess how **thoroughly** PayPal and AI are used, not just presence of a button. Show OAuth → create (idempotency key) → actual Sandbox buyer approval → server retrieval/validation → capture → webhook signature check → audit timeline. Race conditions and uncertain network responses must not double-charge a buyer or falsely mark an order paid. Use a single test Sandbox merchant + separate test personal buyer. Do not substitute a fake “payment succeeded” toast. Authorization/capture, invoicing, or other PayPal capabilities should only be expanded if they strengthen the focused procurement story and are reliably testable.

### P2. Impact and audience

Target **small purchasing teams, nonprofits and growing businesses** that currently compare multiple merchant tabs, need a clear approval reason, and must explain a purchase later. Choose a *specific* scenario such as buying office monitors for a small team, rather than calling it universal enterprise procurement. Identify current manual steps and demonstrate exactly which steps are removed or made auditable. Ask 2–3 actual procurement practitioners to review it if available; label their feedback honestly, never invent testimonials.

## 4. Judge scorecard (self-assessment, not official scoring)

Use five separate 0–5 ratings with recorded evidence for each. Don't give a criterion a high score without a reproducible proof:
- **Technical implementation (20%)**: real secured multi-service integration; successful and negative Sandbox paths; identity-scoped reads; no fake payments; deterministic constraints; webhook verification and idempotency.
- **Design (20%)**: clear hierarchy, quiet paper-white UI, sensible empty/loading/error states, keyboard accessibility, responsive layout, obvious next action, fast time to first win.
- **Impact (20%)**: specific user and problem, concrete defensible example, truthful value calculation, audit needs that ordinary shopping agents do not serve.
- **Innovation (20%)**: decision passport, eligibility/explanation chain and purchase proof are visibly unique; identify competitor overlap and explain differentiation.
- **Presentation (20%)**: frictionless, working end-to-end recording under 3 minutes, crisp narration, no stale logs, no hidden setup tricks, genuine sandbox evidence.

**Internal target:** five evidence-backed ratings of 4+/5, with technical/demo at 5/5. A high benchmark is an aspiration, not a guarantee of top-three placement.

## 5. A two-minute-forty-second demo story (proposal)

- **0:00–0:15 — Pain:** “A small team needs four suitable office monitors, within a strict budget; buying badly means explaining cost and risk later.”
- **0:15–0:35 — Define:** Enter the request, quantity, currency, mandatory attribute/budget; show single prominent action.
- **0:35–1:02 — Evidence:** Live Channel3 search, real offer prices, stock, eligible and ineligible reasons. Keep product IDs and merchant source visible.
- **1:02–1:25 — AI:** Let Gemini evaluate the real shortlist, explain one trade-off; visibly state uncertainty and show that AI doesn't approve payments.
- **1:25–1:50 — Human decision:** Select eligible offer, show exact total, approve deliberately, create one order.
- **1:50–2:13 — PayPal Sandbox:** Show *actual* payer approval and capture, payment amount matching the PO; no real merchant settlement claim.
- **2:13–2:30 — Proof:** Highlight signed/verified payment state, audit timeline, and (only if later implemented) the Decision Passport.
- **2:30–2:40 — Close:** Concise outcome and explicit differentiator; end with project name and demo URL.
- Upload to YouTube publicly, 2:40 target; never breach 3:00. Record real browser actions and ensure no passwords/API keys appear.

## 6. Seven-day execution discipline (proposals vs currently authorized testing)

### Nov 5–6: reliability first — AUTHORIZED NOW
- Verify local backend syntax/Pytest, frontend lint/Vitest/build, public API URLs, migrations and auth.
- Run **read-only live provider checks** (Gemini one benign ADK call with quota awareness; Channel3 query; PayPal Sandbox OAuth). The UI's “Configured” label is not evidence of provider access.
- Rehearse actual buyer approval/capture through the UI and signed HTTPS webhook. Check idempotency and negative cases; preserve redacted evidence.
- Make no real-money requests and never disclose provider secrets.

### Nov 7–8: competitive features — source already implemented; verification still required
- Implement **one** signature feature well: Decision Passport and its evidence-backed explanation.
- Tighten the PayPal proof chain, then truthful eligible-offer comparisons. Avoid multi-feature sprawl.

### Nov 9–10: show readiness
- Fix verified usability and failure-mode issues; complete a compelling minimal demo route.
- Prepare hosted judge access/clean demo account and documented offline fallback.
- Confirm public GitHub MIT license detection and Devpost requirements, including public source, video and third-party media rights.

### Nov 11: freeze and submit
- Run a full dry-run from fresh signup to signed webhook, 3 times.
- Record, edit and upload public YouTube demo; complete entry; confirm all links from a signed-out/incognito browser.
- Save submission confirmation before **Nov 12 at 23:00 EAT**.
- Keep services and test access available through judging.

## 7. What can disqualify or severely weaken this entry

1. The original proprietary license has been replaced by MIT; verify GitHub detects MIT and the judges can actually inspect and run the public project before entry.
2. A static “demo” or screens with no real working integrations. Judges can decline to run local setup.
3. PayPal Sandbox checkout that creates an order but cannot be captured successfully with a separate buyer.
4. Missing public YouTube video under three minutes or inaccessible repository/demo.
5. AI recommendations that invent product prices/stock, or marketing implying that PayPal Sandbox pays Channel3 retailers.
6. Missing PayPal webhook signature verification, replay safety or amount checks.
7. Broken Vite build and absent dependency lockfile, brittle judge setup, blank dashboard on provider timeout.
8. Competing against generic shopping bots on superficial animation or dozens of untested features.
9. Copyright/trademark mistakes in the video or branding.
10. Leaving the submission until the last minutes, or relying on an expiring trial during judging.

## 8. Explicit boundary

This is **research plus an implementation and acceptance record**. Decision Passport, optional buyer mandates, eligible-offer comparison, delegated approval, quote recheck, authenticated PDF/JSON export, and clearly labeled offline judge preview are now in source on `perez` pending integration verification and merge. **Not implemented:** AG Grid integration, real merchant settlement, production-grade multi-tenant governance, independent third-party evaluation, and a guaranteed top-three result. External Sandbox, Gemini and Channel3 tests are not yet certified.

Authorized now: inspect, test, add test coverage and safe provider smoke checks, repair concrete integration defects, document observed passing/failing evidence, and keep existing `perez` → PR → `main` workflow. No new branches; no GitHub Actions.

The team's goal is to improve the *credible odds* of a top-three result. Neither strategy nor participant counts can guarantee a prize.


## Implemented source milestone and acceptance limitations — November 5, 2026

- MIT open-source source license and third-party NOTICE now replace the proprietary restriction; GitHub detection after merge still needs checking.
- Buyer mandate fields, eligibility decisions, approved domains, price caps and expiry checks are enforced by server-side policy, not by an LLM.
- A frozen historical Decision Passport and authenticated JSON/PDF views expose source evidence, acceptable alternatives, the decision, approvals, payment IDs and any correlated signed webhook.
- Signed-in users can assign a distinct registered reviewer; the reviewer cannot capture payments. Default personal-workspace self-approval remains honestly labeled.
- Optional Channel3 product recheck flags changed/missing offers; a clearly labeled offline sample has checkout disabled.
- The PayPal client now fails closed if accidentally configured for the Live API host, preventing real-money operations during hackathon demonstrations.
- **Not yet 100% validated:** installed Python and npm test runs, migrations against a fresh PostgreSQL database, real Channel3 responses, actual Gemini invocation, Sandbox buyer authorization and capture, external signed webhook delivery, browser/mobile E2E, hosted demo access, public video upload and Devpost submission. Judge outcome is outside anyone's control.
