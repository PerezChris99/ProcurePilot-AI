# ProcurePilot AI — final Devpost fields and demo script

**Draft prepared 8 November 2026.** All public product statements below describe actual implemented behavior. The entrant must upload the authentic video, provide private judge access, verify the latest deployment and submit on Devpost. This file is not a Devpost submission receipt.

## Project identity

**Project name:** ProcurePilot AI  
**Tagline:** Every Purchase Has a Reason.  
**Short description:** An accountable procurement assistant that turns live product evidence, AI analysis, human approval and PayPal Sandbox capture into one auditable Decision Passport.

**Public demo:** https://procurepilotai.vercel.app  
**Public source:** https://github.com/PerezChris99/ProcurePilot-AI  
**Judging guide:** https://github.com/PerezChris99/ProcurePilot-AI/blob/main/docs/JUDGES_START_HERE.md  
**Judge access details:** see [secure access playbook](JUDGE_ACCESS_PLAYBOOK.md); provide test buyer credentials in an authorized private testing channel, not the public project description.  
**YouTube video:** REQUIRED — fill with the real publicly visible YouTube URL after uploading. Must be under three minutes.

## Inspiration

Buying a product is straightforward. Explaining why it was the right purchase is harder. Teams lose specification details, choose cheap but unsuitable offers, approve spending without context, and later struggle to match the decision to the payment. We wanted an AI-assisted purchasing experience that does not ask anyone to trust an unexplained recommendation.

## What it does

ProcurePilot AI turns a purchasing need into a traceable decision. A buyer sets a specification, quantity, currency and budget. Channel3 retrieves real catalogue offers and merchant links. Deterministic server-side rules check whether each offer actually meets the request, including required attributes, observed stock, currency and budget. Ineligible offers retain explicit reasons for rejection.

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

Real product data can be incomplete. A 24-inch monitor should never pass a 27-inch mandatory screen specification because it is cheap. The AI provider may time out or exhaust quota, while a PayPal capture response can contain less purchase-unit metadata than the original approved order. These failure modes made deterministic policy checks, honest provider attribution, bounded model requests and carefully differentiated PayPal order/capture verification essential.

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

ProcurePilot AI makes every purchase explainable. It sources real offers through Channel3, rejects products that violate the buyer's requirements, uses Gemini via Google ADK to explain the eligible options, requires a human to authorize the purchase, and verifies PayPal Sandbox capture. Every choice ends with a Decision Passport: what was considered, why it qualified, who approved and how payment was confirmed.

## Demonstration recording — 2:45 target

Film the actual hosted browser at readable 1080p or higher. Keep the mouse steady, show evidence rather than menus, and use voice narration with subtitles. Cut waiting time, never fabricate transactions or use synthetic offline results as live evidence. Blur buyer email, login password, authorization tokens and other personal data. Avoid copyrighted music and third-party branding beyond necessary factual product-interface capture.

| Window | Screen proof | Voiceover |
| --- | --- | --- |
| 0:00–0:15 | Landing page; one clear product sentence | "Buying is easy. Defending a purchasing decision is harder. ProcurePilot preserves the reason behind every order." |
| 0:15–0:38 | New procurement with concrete specifications, quantity and budget | "We begin with the actual requirement, not a generic AI prompt." |
| 0:38–1:06 | Real Channel3 results; show source and a rejected unsuitable alternative | "Live offers meet a strict server policy. A cheaper but incorrect product is not a better purchase." |
| 1:06–1:29 | Real model response labelled Gemini/ADK if received | "AI explains the saved evidence. It cannot change eligibility or spend money." |
| 1:29–1:53 | Create frozen-price purchase order and approve | "A human authorizes the decision against the original amount and conditions." |
| 1:53–2:25 | Genuine PayPal Sandbox page, separate Personal buyer approval, app return and capture | "PayPal confirms the test buyer's approval. The backend verifies the completed capture and exact amount." |
| 2:25–2:42 | Paid status, audit, Decision Passport/PDF | "The final record links product evidence, human decision and PayPal's test transaction." |
| 2:42–2:45 | Simple closing title | "Every purchase has a reason." |

**Visual rule:** Spend the most time on the things a judge cannot infer from a screenshot: a rejected wrong specification, the real PayPal approval/capture and the completed Passport. Avoid tech-logo slides and feature-list walls. Screen text must be legible at normal playback size.

### Final material checklist

- [ ] Video captured from real browser and publicly uploaded to YouTube with runtime strictly under 03:00.
- [ ] Real screenshots: source results with rejection, model attribution, approval, payment confirmation, Passport.
- [ ] Hosted registration/login and purchase walkthrough rechecked after last release.
- [ ] Latest code QA and public HTTP report recorded, with failures stated plainly.
- [ ] Judge can obtain isolated Sandbox buyer details safely; test credentials functional through 15 Dec 2026.
- [ ] Source repository public with MIT license, and main deployment on correct commit.
- [ ] Devpost required fields completed and submitted, not merely saved as draft, by 12 Nov 2026 12:00 PST / 23:00 EAT.

Official rules: https://paypalaihackathon.devpost.com/rules
