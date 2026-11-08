# ProcurePilot AI — final Devpost fields and demo script

**Draft prepared 8 November 2026.** All public product statements below describe actual implemented behavior. The entrant must upload the authentic video, provide private judge access, verify the latest deployment and submit on Devpost. This file is not a Devpost submission receipt.

## Project identity

**Project name:** ProcurePilot AI  
**Tagline:** Every Purchase Has a Reason.  
**Short description:** What happens when the cheapest product is the wrong product? ProcurePilot checks actual Channel3 offers against buyer requirements, uses Gemini to explain qualified evidence, requires human approval and preserves PayPal Sandbox proof in a Decision Passport.

**Public demo:** https://procurepilotai.vercel.app  
**Public source:** https://github.com/PerezChris99/ProcurePilot-AI  
**Judging guide:** https://github.com/PerezChris99/ProcurePilot-AI/blob/main/docs/JUDGES_START_HERE.md  
**Judge access details:** see [secure access playbook](JUDGE_ACCESS_PLAYBOOK.md); provide test buyer credentials in an authorized private testing channel, not the public project description.  
**YouTube video:** REQUIRED — fill with the real publicly visible YouTube URL after uploading. Must be under three minutes.

## Inspiration

**What happens when the cheapest product is the wrong product?** A purchasing team may find a tempting low price only to discover that the item violates a required size, attribute, stock or merchant constraint. Saving money on the wrong product is not a good purchasing decision. We built ProcurePilot AI so businesses can keep requirements, live offer evidence, human approval and Sandbox payment proof together—without treating an unexplained AI recommendation as permission to spend.

## What it does

ProcurePilot AI answers that question through one traceable purchasing workflow. A buyer specifies requirements, quantity, currency and budget. Channel3 retrieves real catalogue offers and merchant links. Deterministic server-side rules reject offers that fail mandatory attributes, observed stock, currency or budget restrictions—even when a rejected listing would appear cheaper. The reasons remain visible rather than being buried by an AI-generated recommendation.

Google Gemini, orchestrated through Google ADK, can then explain a bounded packet of saved offer evidence. It does not invent prices, decide eligibility, approve orders or execute payments. If the model is unavailable, the experience identifies the non-AI catalogue fallback rather than pretending a model replied.

The buyer selects a policy-eligible offer. ProcurePilot freezes the purchase-order total and source evidence, requires human approval, and creates a PayPal Orders v2 Sandbox checkout. A separate Personal Sandbox buyer authorizes it; the server validates the PayPal order and completed capture before recording the paid status. The Decision Passport brings together the chosen offer, rejected alternatives, approver, timestamps, payment identifiers and a downloadable PDF.

The result is **accountable AI-assisted commerce**, not unsupervised purchasing. A successful Sandbox capture moves virtual money between test accounts, not to a Channel3 retailer.

## How we built it

- **React 19 / JavaScript JSX / Vite:** responsive buyer workspace, catalogue comparison, order actions and audit views.
- **FastAPI / Python / SQLAlchemy / Alembic / PostgreSQL:** authenticated workflows, durable order evidence, database-backed status and validation.
- **Channel3 API:** real third-party product and offer discovery, price and stock observations, source URLs and requirement matching.
- **Google ADK with Gemini:** bounded explanations from saved evidence; deterministic eligibility and payment decisions stay outside the model.
- **PayPal REST Orders v2 Sandbox:** merchant API OAuth, idempotent order creation, separate test-buyer approval, explicit validated server capture and verified webhook handling.
- **Decision Passport:** inspectable selection rationale, rejection records, human decision and Sandbox payment trail in-app and as JSON/PDF.
- **Testing:** automated backend/frontend, policy guardrails and deployment-contract checks, plus a safe local offline preview.

## Challenges

Real product data can be incomplete. A 24-inch monitor should never pass a 27-inch mandatory screen specification merely because of its price. The AI provider may time out or exhaust quota, while a PayPal capture response can contain less purchase-unit metadata than the original approved order. These failure modes made deterministic policy checks, honest provider attribution, bounded model requests and carefully differentiated PayPal order/capture verification essential.

We also separated external network calls from long-running database transactions and designed a recoverable capture check to avoid treating a local response error as proof that PayPal did not take the test payment.

## Accomplishments

We built an end-to-end evidence-first purchasing prototype with real Channel3 retrieval, Google ADK/Gemini explanation, human-approved purchase orders, PayPal Sandbox checkout and an auditable Decision Passport. The owner reports completing a Sandbox transaction and independently seeing it in PayPal on 8 November. Automated regressions cover policy and payment boundary behavior; a separate current-commit full QA and public HTTPS check remain part of final submission acceptance.

Our key design choice: **AI explains. Code enforces. Humans approve. PayPal confirms.**

## What we learned

Reliable agents need constraints more than persuasive words. A good explanation shows which evidence makes a product eligible and what is unknown; it never silently relaxes buyer instructions. Human authorization and payment verification are distinct events. Auditable decisions require preserving the original evidence and the reasons rejected options were not selected.

## What's next

Organization-level approval policies, independent operational monitoring, inventory and retailer-fulfillment integration, robust session lifecycle management, expanded provider reliability, and deeper real-world procurement pilots. This hackathon prototype deliberately stops short of claiming merchant fulfillment or enterprise certification.

## Tools disclosure

**Primary:** PayPal Developer Platform (Orders v2 Sandbox), Gemini via Google ADK.  
**Sponsor technology actually used:** Channel3 API for product discovery and evidence.  
**Supporting tools:** React, Vite, FastAPI, PostgreSQL (Neon), SQLAlchemy, Alembic, Vercel, Playwright only if separately run and verified (do not claim it as completed testing from source alone).  
**Optional AI fallbacks:** LiteLLM/Groq/OpenRouter when configured; name the actual provider only when confirmed by the run.  
**Not used as sponsor integrations:** AG Grid, APIMatic, Bryntum, Render. Do not claim their awards or add decorative library references.

## Short pitch for project card

**What happens when the cheapest product is the wrong product?** ProcurePilot AI checks real Channel3 offers against the buyer's non-negotiable requirements, explains the qualified choices with Gemini via Google ADK, requires human approval, and verifies PayPal Sandbox capture. The Decision Passport records the rejected alternatives, selected evidence, human authorization and test payment proof. A rejected cheaper quote is not claimed as savings.

## Demonstration recording — “What happens when the cheapest product is the wrong product?”

**Canonical production plan:** [The 2:45 proof-first storyboard](DEMO_CHEAPEST_WRONG_PRODUCT.md). Film a real browser and real provider data, not a narrated mockup.

**00:00–00:13:** Ask the question; show the requirement. **00:13–01:05:** Show a real Channel3 offer and a policy rejection, with a genuine cheaper-versus-eligible price contrast **only if the actual saved quotes support it**. **01:05–01:28:** Show actual Gemini/ADK analysis, or accurately labelled rules-only fallback. **01:28–01:52:** Freeze and approve the qualified order. **01:52–02:23:** Record actual Personal-buyer PayPal Sandbox approval and explicit capture. **02:23–02:45:** Finish on the Decision Passport and tagline.

**Evidence rule:** Real provider offers must determine the product names, prices, currency and comparison. If the cheapest actual offer is not rejected, do not narrate it as though it were. Synthetic Trust Lab policy demonstrations are valid only when clearly labelled separate from the live commerce run.

**Value statement:** The product makes unsuitable offers visibly ineligible and preserves the purchasing justification. A cheaper *rejected* listing is not a saving, and Sandbox capture is not actual merchant fulfillment. The final video must be under 3:00, publicly visible on YouTube and free of exposed credentials or unlicensed third-party content.

## Differentiation and early impact evidence

ProcurePilot is deliberately not a price-sorting chatbot. Its contribution is the combination of **hard buyer mandates**, explain-only AI, human-approved fixed-price purchase orders and the historical Decision Passport. Existing shopping assistants or procurement suites may provide parts of this workflow; we do not claim to have invented product comparison, approval software or audit logging.

The current system does **not** submit the selected offer to a retailer for fulfillment. A real merchant-order integration would require an authorized seller channel, supported checkout or ordering API, and separate order confirmation, taxes, shipping, refunds, cancellation and failure reconciliation. The Sandbox demo proves the payment integration, not delivery.

Impact claims must be observable: a real rejected incompatible quote, a real approved eligible quote, the recorded approval actor, and the corresponding Sandbox capture. A controlled small usability test can compare time-to-decision, specification errors and the quality of the retained evidence against a manual process; report sample size and raw results if actually collected, not fabricated efficiency gains.

### Final material checklist

- [ ] Video captured from real browser and publicly uploaded to YouTube with runtime strictly under 03:00.
- [ ] Real screenshots: source results with rejection, model attribution, approval, payment confirmation, Passport.
- [ ] Hosted registration/login and purchase walkthrough rechecked after last release.
- [ ] Latest code QA and public HTTP report recorded, with failures stated plainly.
- [ ] Judge can obtain isolated Sandbox buyer details safely; test credentials functional through 15 Dec 2026.
- [ ] Source repository public with MIT license, and main deployment on correct commit.
- [ ] Devpost required fields completed and submitted, not merely saved as draft, by 12 Nov 2026 12:00 PST / 23:00 EAT.

Official rules: https://paypalaihackathon.devpost.com/rules
