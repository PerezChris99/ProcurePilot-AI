# ProcurePilot AI — Devpost submission and demo production kit

**Competition:** [PayPal AI Hackathon](https://paypalaihackathon.devpost.com/) ·
[Official rules](https://paypalaihackathon.devpost.com/rules) ·
**Submission cutoff:** November 12, 2026, **12:00 PST / 23:00 EAT**.

**Updated:** November 8, 2026. **State:** copy-ready submission narrative; owner has confirmed a real PayPal Sandbox transaction visible in PayPal, while fresh external QA, signed-webhook evidence, judge access details, public video and Devpost submission still require independent completion.
The entrant must verify the hosted URL, archive sanitized transaction evidence, publish the authentic video and submit the final project before replacing any `[REQUIRES VERIFICATION]` field. Never
invent a provider response, demonstration result, payment capture, sponsor use,
user testimonial or savings percentage.

## 1. Submission identity

- **Project name:** ProcurePilot AI
- **Tagline:** *Every Purchase Has a Reason.*
- **Category:** Accountable AI-assisted purchasing; evidence-first agentic
  commerce with mandatory human authorization.
- **One-sentence pitch:** What happens when the cheapest product is the wrong
  product? ProcurePilot checks real Channel3 offers against requirements,
  uses Gemini/ADK to explain eligible evidence, requires human approval and
  preserves PayPal Sandbox payment proof in one Decision Passport.
- **Code:** https://github.com/PerezChris99/ProcurePilot-AI
- **License:** https://github.com/PerezChris99/ProcurePilot-AI/blob/main/LICENSE
  (GitHub detects MIT).
- **Hosted application:** https://procurepilotai.vercel.app — owner-confirmed hosted workflow and PayPal Sandbox transaction; the earlier 2/7 report predates the repaired release. Current 7/7 external probe is still pending.
- **Public YouTube demo:** `[REQUIRES VERIFICATION — actual public video URL]`
- **Judge access:** `[REQUIRES VERIFICATION — clear signup/test account route]`
- **Judge testing instructions:** [Secure evaluation and buyer access](JUDGE_ACCESS_PLAYBOOK.md)
- **Short ready-to-paste text:** [Final Devpost draft](DEVPOST_FINAL_DRAFT.md)
- **Canonical filming plan:** [The wrong-product purchasing demonstration](DEMO_CHEAPEST_WRONG_PRODUCT.md)
- **Evidence map:** [Judging evidence](JUDGING_EVIDENCE_MATRIX.md)
- **Offline source walkthrough:** [Judges start here](JUDGES_START_HERE.md)
- **Repository execution and QA:** [README](../README.md), [QA](../qa/README.md)

## 2. Copy-ready Devpost description

### Inspiration

**What happens when the cheapest product is the wrong product?** Buying teams
can mistake an apparently good price for a good purchasing decision even when
the product fails a mandatory specification. ProcurePilot was built to preserve
what the buyer required, which actual offers qualified, why alternatives were
rejected, who approved the choice, and what PayPal Sandbox payment was recorded.

### What it does

ProcurePilot AI treats that question as an evidence-based purchasing decision,
not a generic AI product recommendation. A buyer specifies the item, quantity, currency, budget and
optional mandatory attributes or merchant restrictions. Channel3 supplies
actual products and retailer offers. Deterministic Python policy checks
availability, screen size where explicitly requested, supported attributes,
source evidence, currency and spending limits.

Google ADK passes only a small, bounded shortlist to Gemini for an
evidence-grounded explanation. Optional Groq and OpenRouter fallbacks are
used for transient provider errors; all model attempts respect shared daily
quotas. If every route is unavailable, the app says clearly that it is
showing **rule-based catalogue evidence**, not an AI-generated answer.

The buyer chooses a qualified retailer offer. The backend freezes a purchase
order's amount and the alternatives considered. An authorized human approves
the decision. PayPal REST Orders v2 **Sandbox** then demonstrates checkout:
the buyer approves using a separate Sandbox Personal account, and the server
verifies the exact order and completed capture before marking the payment
complete. Signed webhook handling and audit records provide independent
payment-status evidence.

The **Decision Passport** packages the evidence trail: request, product IDs,
observed offer prices and timestamps, eligible/rejected alternatives, human
decision, Sandbox payment IDs and a downloadable PDF.

### How we built it

React 19, JavaScript/JSX, Vite and responsive component design form the
frontend. FastAPI, SQLAlchemy, Alembic and PostgreSQL form the API and durable
state; SQLite supports isolated local previews. Channel3 is the actual
catalogue source. Gemini through **Google ADK** performs bounded explanation
with a tool-free normal analyst. LiteLLM routes optional backup model calls.
PayPal OAuth and Orders v2 Sandbox handle test order creation, buyer approval,
explicit capture and signed webhook verification.

The separation is intentional: AI can summarize and explain, but cannot
create a purchase order, authorize a payment, or alter a captured amount.
Verified stock, price, currency, budget and merchant eligibility are
determined by server rules, not a language model.

### Challenges

The hardest problem was not producing AI prose; it was keeping the evidence
honest through unexpected failure. Real provider calls can return temporary
503 or shared-pool 429 errors, catalogue results can omit critical
specifications, and payment operations must never assume that a browser
redirect proves a completed transaction.

We responded with short, quota-accounted model attempts and transparent
non-AI fallback; explicit rejection of wrong-sized and unverified products;
server-frozen purchase totals; idempotent Sandbox request identifiers;
verification of PayPal amounts and completed captures; and database
transaction boundaries that do not remain idle during slow external I/O.

### Accomplishments

The working source includes policy-checked catalogue discovery, a grounded
ADK analyst with bounded fallback, authenticated buyer/approver workflows,
Sandbox checkout/capture integrations, signed webhook handling, an auditable
Decision Passport with PDF export and a nine-gate offline QA runner.
The maintainer reported **9/9 offline gates passing on November 7,
2026**, at commit `d6e61cd`; subsequent changes require a fresh suite. On November 8 the owner reported a successful live **Sandbox** buyer transaction visible in PayPal. This confirms the owner's observed result, not independent capture-ID reconciliation or signed webhook delivery. Judge access, current 9/9 QA, the public 7/7 HTTPS check and an authentic video are still outstanding evidence gates.

### What we learned

A trustworthy purchasing assistant must show not just its recommendation,
but the evidence that supports and disqualifies alternatives. A useful AI
failure mode is a clear, policy-derived explanation—not a fabricated source
or payment success message. Putting human approval and remote transaction
proof at separate boundaries makes the system accountable.

### What's next

After the prototype, the next work is organization-wide role governance,
session revocation, stronger distributed payment reconciliation, retailer
fulfillment integrations, tested disaster recovery, broader catalogue
specification extraction, and observed production performance. These are
not claims about the current hackathon build.

## 3. Video: 2:45 evidence-first storyboard

**Central question:** **“What happens when the cheapest product is the wrong product?”** The [complete filming script, timing and proof requirements](DEMO_CHEAPEST_WRONG_PRODUCT.md) is the canonical storyboard. Keep the full recording below three minutes; YouTube must be public and the video must show a real functioning application.

Demonstrate one understandable business request, an actual Channel3 offer that fails a hard requirement, a qualified alternative, genuine attributed Gemini/ADK analysis when it succeeds, human approval, real PayPal Sandbox buyer authorization and capture, and the final Decision Passport. Start with the problem, not a technical architecture slide.

**Critical accuracy guard:** State that the wrong item was *cheaper* only if actual saved same-currency, same-quantity quotes prove that price ordering. If no such pair is present, show the rejected offer honestly and keep the opening question as a hypothetical. Clearly label any synthetic Trust Lab cutaway; never present it as an actual Channel3 quote, AI response or payment.

Edit away network waiting but never invent provider outcomes, transaction IDs or savings. Keep type readable at ordinary 1080p playback size. Redact test buyer credentials and private details; respect third-party content and trademark permissions.

## 4. Recommended screenshots (actual capture only)

1. **Landing:** brand, tagline and primary action without placeholder cards.
2. **Catalogue:** real Channel3 source and one clearly rejected alternative.
3. **Decision:** explainable top offers, ineligibility reason and model badge.
4. **Approval:** human reviewer decision and frozen PO amount.
5. **PayPal proof:** Sandbox order/capture confirmation with identifiers redacted
   where sensitive, status readable.
6. **Passport:** one-page summary, comparison and audit/PDF.

No generated UI screenshots or counterfeit PayPal confirmations. If desired,
make a separate *clearly labelled* architecture diagram from source for
technical explanation; never substitute it for actual working footage.

## 5. Explicit technology and sponsor disclosure

**Actually integrated in source:**
- PayPal REST Orders v2 **Sandbox**: merchant OAuth, create test order, real
  buyer approval, explicit verified capture, signed webhook processing.
- Google **ADK/Gemini**: grounded analysis only, with output/time/call limits.
- LiteLLM routes to Groq/OpenRouter when configured; actual provider names
  must reflect the provider which returned the displayed response.
- **Channel3**: actual product/offer retrieval and timestamped policy evidence.
- FastAPI/Python, React/JSX/Vite, SQLAlchemy/Alembic/PostgreSQL, PDF exports.

**Current hosting:** Vercel Services for React and FastAPI at
https://procurepilotai.vercel.app; Neon PostgreSQL 17 schema checks have run, and production/Preview Vercel deployments were READY on commit `5dff11f` on 8 November. The owner reports a completed real Sandbox payment. A **new public 7-check HTTP probe and delivered signed-webhook proof are still required** for those distinct claims. The historical 2/7 result predates the repaired release and is obsolete. This project is **not
hosted on Render** and does not claim eligibility for Render's sponsor prize.
Neon-backed auth rate limits are available without a separate Redis account.

Do not claim AG Grid, APIMatic, Bryntum or any other sponsor tool that is
not demonstrably integrated and tested. Channel3 sponsor usage must be
supported by a real provider walkthrough.

**Prize limit:** the official rules permit **one Grand Prize plus one Sponsor
Prize OR one Honorable Mention plus one Sponsor Prize**. Multiple honorable
mentions and multiple sponsor prizes cannot be stacked. The first objective
is a compelling Grand Prize submission; the already meaningful Channel3
integration is the most defensible sponsor entry today.

## 6. Submission checklist

- [ ] Eligibility/ownership and third-party content rights personally verified.
- [x] Public GitHub repo with recognized MIT license.
- [x] Complete source, documentation and offline QA scripts committed.
- [x] Maintainer reported 9/9 offline QA gates green on 2026-11-07 at `d6e61cd` (new changes require rerun).
- [ ] Rotate provider credentials exposed outside secure secret managers.
- [ ] Add **verified live HTTPS demo URL**, or fully reproducible external
      provider test access; do not insert a placeholder as a real URL.
- [ ] Run real Channel3 + Google ADK provider smoke and full UI journey.
- [ ] Archive the owner-confirmed **Sandbox Personal buyer** transaction evidence and compare exact saved capture ID, currency, amount and UI state. The owner reports seeing the completed test transaction in PayPal on 8 November; do not mislabel it as an untested checkout blocker.
- [ ] Test one signed HTTPS PayPal webhook (including duplicate delivery).
- [ ] Confirm mobile/desktop usability, no console errors, CORS and resilience.
- [ ] Capture screenshots and publish an authentic YouTube video **under 3:00**.
- [ ] Complete Devpost project name, description, tools used, GitHub link,
      functional demo access and video URL, and select only eligible sponsor
      categories.
- [ ] Submit before **November 12 at 23:00 EAT**; keep access free through
      **December 15**, and retain judging proof/credentials privately.
- [ ] Confirm the submission shows a **submitted** state, not just a draft.

The 9/9 offline result does not certify a public deployment, provider
availability, security audit, webhook delivery, authorized assets or
Devpost submission.

Official references:
- https://paypalaihackathon.devpost.com/
- https://paypalaihackathon.devpost.com/rules
- https://developer.paypal.com/community/blog/PayPal_AI_Hackathon/
