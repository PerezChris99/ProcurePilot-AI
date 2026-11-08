# Judging evidence map — ProcurePilot AI

Updated: 8 November 2026. This is an evidence index for evaluators, not a claim of certification or a prize forecast.

**One sentence:** A purchasing assistant that uses real catalogue evidence, keeps AI within explain-only boundaries, requires human authorization and records a verified PayPal Sandbox payment in an auditable Decision Passport.

## Five equally weighted judging criteria

| Criterion | Demonstration evidence | Source to inspect | Limitation not to hide |
| --- | --- | --- | --- |
| Technological implementation | Real Channel3 retrieval, eligibility rejection, actual ADK model attribution, order approval, correct PayPal capture ID/amount, replay-safe webhook handling | backend/app/integrations/channel3/client.py; backend/app/agents/runtime.py; backend/app/procurement/policy.py; backend/app/api/purchase_orders.py; backend/app/api/paypal_webhooks.py | No proof of live signed webhook delivery is available from owner transaction visibility alone. |
| Design | Focused start-to-finish purchasing workflow, explicit status/feedback, readable evidence and downloadable Passport | frontend/src/pages/ProcurementPage.jsx; frontend/src/pages/DiscoveryPage.jsx; frontend/src/pages/OrdersPage.jsx; frontend/src/components/ui/DecisionPassport.jsx | Do not describe synthetic policy fixtures as real shopping results. |
| Potential impact | Correct requirements prevent unsuitable purchases; recorded authority and price help a small purchasing team explain its choices | backend/app/procurement/specifications.py; backend/app/procurement/passport.py; docs/JUDGES_START_HERE.md | No pilot customers, quantified savings, reduced fraud metric or formal business outcome have been established. |
| Innovation | Explain-only AI + deterministic purchasing policy + human approval + provider-confirmed Sandbox transaction in one evidence trail | README.md; docs/architecture.md; docs/security.md | This is not an autonomous payment agent, deployed retailer purchasing integration or a live-money marketplace. |
| Presentation | A real case: clear specification → rejected bad match → grounded AI → human approval → PayPal Sandbox capture → Passport | docs/DEVPOST_FINAL_DRAFT.md; docs/JUDGE_ACCESS_PLAYBOOK.md | A video is not completed until an actual public YouTube link exists and its footage is verified. |

## PayPal and AI: critical sequence

1. The model explains catalogue evidence; deterministic Python policy decides whether an offer is eligible.
2. The selected source offer and server-calculated amount are frozen in a purchase order.
3. A permitted human reviewer explicitly authorizes the order.
4. Backend obtains PayPal Sandbox merchant OAuth and creates an Orders v2 test order. A distinct Personal Sandbox test buyer approves in a PayPal-hosted checkout.
5. An explicit server request inspects order identity and approved amount, captures or reconciles a completed capture without unnecessary duplicate POST, and validates capture ID, amount and currency before saving paid status.
6. Signed PayPal webhooks are validated and deduplicated in application code. Live event delivery requires separate evidence; do not call it independently proven without a provider log/receipt.
7. Decision Passport records selected and rejected evidence plus approval and payment history.

**Owner-reported live milestone:** on 8 November the entrant reported successful Sandbox checkout and viewing the completed transaction in PayPal. This is credible owner testimony, not an independently captured transaction ID, signed webhook receipt or 7/7 public acceptance report.

## Channel3: critical sequence

A real query produces product identifiers, offers, retailer links and available observed attributes. The backend rejects ineligible offers, including wrong or unknown mandatory specifications, stock, currency or budget problems; the model sees a short evidence set rather than an invented catalogue. The genuine provider response, timestamped offer and meaningful downstream purchasing use make Channel3 an integrated product capability—not a logo or incidental call.

## Claims that must be avoided

- "We automatically buy goods from retailers" — retailer fulfillment is not implemented.
- "Our AI decides spending" — human approval and deterministic rules retain authority.
- "We prevent all fraud" or "100% secure" — no security guarantee or independent audit exists.
- "We saved customers 30%" — no real customer outcome measurement is documented.
- "PayPal webhooks have been delivered" — only say so once an authentic signed delivery has been recorded.
- "Live money was transferred" — the working payment flow uses PayPal Sandbox virtual money.
- "All tests pass today" — current SHA must have a recorded current-suite run before making that claim.
- "Fully agentic autonomous checkout" — this is bounded, human-in-the-loop agentic commerce.

## Actual source and award eligibility

The project meaningfully integrates PayPal Developer Platform and Gemini via Google ADK. The third-party commerce sponsor integration present in source is Channel3. The official PayPal AI Hackathon also offers grand prizes and honorable mentions; those are determined by judges on five equal criteria. The rules allow one grand prize **or** one honorable mention, plus up to one sponsor prize. Do not claim an AG Grid, APIMatic, Bryntum or Render sponsor award without real use.

See official rules: https://paypalaihackathon.devpost.com/rules

## Proof that the entrant still has to capture

- A recent end-to-end run from a fresh judge-style browser session.
- Output from the current-commit nine-gate local QA runner, and seven-gate public read-only HTTPS checker.
- Dated sanitized images or screen recording of genuine live Channel3, Gemini attribution, human approval, paid Sandbox transaction and matching Passport.
- Live signature-verified PayPal webhook delivery/replay evidence, if that claim is used.
- Public YouTube recording under three minutes and a completed Devpost submission receipt.
- A private, functional test buyer account for judges through 15 December 2026.

The simplest compelling proof is one real purchase order with a clear **wrong-product rejection** and a **confirmed Sandbox capture** ending in a readable Passport.
