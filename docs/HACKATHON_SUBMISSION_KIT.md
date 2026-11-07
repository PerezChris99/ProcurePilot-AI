# ProcurePilot AI — Devpost submission and demo production kit

**Competition:** [PayPal AI Hackathon](https://paypalaihackathon.devpost.com/) ·
[Official rules](https://paypalaihackathon.devpost.com/rules) ·
**Submission cutoff:** November 12, 2026, **12:00 PST / 23:00 EAT**.

**Updated:** November 7, 2026. **State:** copy-ready draft; real hosted acceptance and payment proof outstanding.
The entrant must verify the hosted URL, live transaction evidence, video and
submission before replacing any `[REQUIRES VERIFICATION]` field. Never
invent a provider response, demonstration result, payment capture, sponsor use,
user testimonial or savings percentage.

## 1. Submission identity

- **Project name:** ProcurePilot AI
- **Tagline:** *Every Purchase Has a Reason.*
- **Category:** Accountable AI-assisted purchasing; evidence-first agentic
  commerce with mandatory human authorization.
- **One-sentence pitch:** ProcurePilot turns a buyer's request into a
  defensible purchasing decision by combining real Channel3 offer evidence,
  policy-checked AI comparison, human approval and verified PayPal Sandbox
  payment records in a single Decision Passport.
- **Code:** https://github.com/PerezChris99/ProcurePilot-AI
- **License:** https://github.com/PerezChris99/ProcurePilot-AI/blob/main/LICENSE
  (GitHub detects MIT).
- **Hosted application:** https://procurepilotai.vercel.app — public frontend verified; live API and database acceptance NOT YET VERIFIED (last reported 2/7).
- **Public YouTube demo:** `[REQUIRES VERIFICATION — actual public video URL]`
- **Judge access:** `[REQUIRES VERIFICATION — clear signup/test account route]`
- **Offline source walkthrough:** [Judges start here](JUDGES_START_HERE.md)
- **Repository execution and QA:** [README](../README.md), [QA](../qa/README.md)

## 2. Copy-ready Devpost description

### Inspiration

Teams often finish a purchase without a defensible record of **why** it was
made. Buyers may compare prices across tabs, lose the original specification,
approve something slightly wrong, or be unable to reconstruct who agreed to
the cost. A purchasing assistant should help people make accountable choices
instead of treating the first cheap result as the answer.

### What it does

ProcurePilot AI turns an ordinary purchasing request into a transparent,
auditable decision. A buyer specifies the item, quantity, currency, budget and
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
2026**, at commit `d6e61cd`; any subsequent candidate changes must be retested. Live hosted payments, public webhook delivery and judge access still
require separate confirmation and should not be claimed as complete until
actually recorded.

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

**Target runtime: 2:40–2:50. Hard requirement: less than 3 minutes.**
YouTube video must be publicly accessible and show actual browser behavior.
Film the strongest pre-rehearsed **real** Sandbox journey. Edit only to
remove waiting time; do not fake a payment, AI response, user testimonial or
source. No unlicensed music or unrelated copyrighted logos. Frame browser
safely so passwords, tokens and account secrets are never visible.

| Time | On screen | Narration intent / proof |
| --- | --- | --- |
| 0:00–0:13 | Calm landing page and one purchasing pain statement | "Buying is easy. Proving why a business should buy is harder." |
| 0:13–0:33 | Enter explicit item, quantity, currency and budget | Show a focused real buyer workflow |
| 0:33–1:03 | Live Channel3 results; one eligible and one rejected offer | Show real product source, amount, missing size/stock rule, not invented listings |
| 1:03–1:27 | Ask AI; show provider attribution and an evidence-based comparison | Explain that ADK model output informs but cannot approve |
| 1:27–1:51 | Create exact PO, frozen amount, submit and authorized human approval | Make control separation obvious |
| 1:51–2:19 | Create checkout; real PayPal Sandbox buyer login/approval and return | Show genuine Sandbox domain, not a simulated green check |
| 2:19–2:37 | Explicit capture, completed status and payment IDs | Show amount/currency validation, no retail settlement claim |
| 2:37–2:45 | Decision Passport, PDF export, final tagline | "Every purchase has a reason—and now it has a record." |

**Presenter rule:** articulate one claim per clip; keep product names, amounts,
source badges and screen-size text large enough to read at 1080p. Zoom in
rather than speeding up the footage. Show at least one visible rejection and
one actual PayPal approval/capture. If the live run cannot be captured,
**do not edit together mock results and call them live**. Resolve the blocker
or explicitly disclose the limits of the recorded demo.

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

**Current hosting direction:** Vercel Services for React and FastAPI at
https://procurepilotai.vercel.app; Neon PostgreSQL 17 is provisioned and its
secret DATABASE_URL is configured. The hosting API and Neon migration are
**not yet certified** (last 7-check probe was 2/7). This project is **not
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
- [ ] Run PayPal **Sandbox Personal buyer** approval and explicit capture; match
      IDs, currency, amount and UI state.
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
