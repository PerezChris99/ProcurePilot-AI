# Demonstration: What happens when the cheapest product is the wrong product?

**ProcurePilot AI · Every Purchase Has a Reason**  
**Format:** one real browser journey, approximately 2:45, with an actual PayPal Sandbox capture.  
**Purpose:** A reference walkthrough of the actual application flow. Example prices and catalogue availability must come from genuine saved provider data; this document does not itself certify a recorded video.

## The question

**What happens when the cheapest product is the wrong product?**

For a small business buying equipment, a low price is worthless if the product does not meet the requirement. ProcurePilot checks buyer specifications against observed Channel3 catalogue evidence, rejects unsuitable offers, uses Gemini via Google ADK to explain the qualified evidence, requires human approval, and records a PayPal Sandbox test capture in a Decision Passport.

The aim is not to show every page. Show **one decision a viewer can understand in ten seconds**.

## Preflight: choose only an authentic example

1. In a fresh, authorized account, request a product with an objectively testable hard requirement (example: **two 27-inch office monitors**, USD, a stated total budget, 27-inch display mandatory). If catalogue data does not expose a usable size attribute, choose another real product with a reliably present required attribute.
2. Search Channel3. Capture provider identifiers, source URLs, observed price, currency, quantity, availability, discovery timestamp, and precise server-side rejection reason.
3. **Only say “the cheapest is wrong” if the saved results contain a genuinely lower-priced, same-currency, same-quantity rejected offer and a more expensive eligible alternative.** Verify the exact amounts and eligibility before recording. Do not invent a 24-inch listing, quote or comparative price.
4. Select the eligible item. Record a real model response **only if actually returned by Gemini/ADK** with visible attribution; otherwise narrate the labelled rules-only fallback. Do not use an offline sample as live provider proof.
5. Submit and approve the purchase order. Complete a fresh authorized Personal PayPal Sandbox buyer approval, explicit capture and matching paid order status. Make sure the test capture is not accidentally repeated.
6. Open the real Decision Passport. Check that its `price_comparison.cheapest_rejected_total`, `cheapest_rejected_offer.blocked_by` and `eligible_vs_rejected_price_gap` refer to the saved same-currency evidence, and that payment proof matches the order. **This gap is not “savings”; the rejected offer was ineligible.**
7. Use screenshots and video that show genuine readable app state. Redact test passwords, personal emails and sensitive identifiers. Do not display secrets in DevTools.

**Fallback if no genuine cheaper rejected offer appears:** Keep the question as a *hypothetical problem* in the opening, but say on camera: “Here is an unsuitable listing that the rules block,” without claiming it was the cheapest. If useful, cut to **Decision Trust Lab — labelled synthetic scenarios** to demonstrate hard requirements, then return to the genuinely captured purchase for PayPal and Passport. Never combine synthetic prices with live provider or payment data.

## 2:45 recording plan (sub-three-minute hard limit)

| Time | Visual proof | Suggested narration |
| --- | --- | --- |
| 00:00–00:13 | One-line question over real application, no long opening animation | **“What happens when the cheapest product is the wrong product? For a business, the wrong purchase is never a bargain.”** |
| 00:13–00:35 | Enter a specific request, quantity, currency, budget, mandatory attribute | “ProcurePilot starts with the buyer's actual requirements. Let's ask for two monitors that must meet a specific display size and budget.” |
| 00:35–01:05 | Actual Channel3 cards: price and blocked reason visibly distinguish qualified from unqualified | “These are actual catalogue offers. This listing fails the requirement. Even a lower price cannot override a mandatory specification.” **Only use ‘lower’ if verified.** |
| 01:05–01:28 | Real attributed Gemini/ADK result, or explicitly marked non-AI fallback | “Gemini explains the saved evidence. It doesn't invent inventory, change the eligibility rules or authorize spending.” |
| 01:28–01:52 | Select an eligible saved offer, freeze PO total, human approval | “The chosen offer becomes a fixed-price purchase order. A human checks and approves it before checkout.” |
| 01:52–02:23 | Real PayPal Sandbox checkout, distinct Personal test buyer, approval, explicit server capture | “The buyer approves in PayPal Sandbox. ProcurePilot verifies the test order, amount, currency and completed capture; the browser redirect alone is not proof of payment.” |
| 02:23–02:40 | Paid order, recorded approval, rejection context, Passport JSON/PDF | “Now we can answer not only what was bought in the test flow, but why it qualified, who approved it and how the Sandbox payment was confirmed.” |
| 02:40–02:45 | One quiet end card with product name/tagline | **“ProcurePilot AI. Every purchase has a reason.”** |

Use the exact real item names, prices and rejected policy explanation visible in the recording; narration above is illustrative. Edit only out loading delays and sensitive login keystrokes. Do not fake an AI response or a PayPal confirmation. Show the official PayPal Sandbox page only as needed to evidence the authorized test transaction, and respect the hackathon's third-party content/trademark rules. Do not use copyrighted music.

## Six screenshots that tell the same story

1. Buyer request showing mandatory specification and budget.
2. Actual Channel3 rejected offer *with exact reason*, plus eligible alternative (and price ordering only when established).
3. Genuine Gemini/ADK explanation and provider attribution, or an accurately labelled rules-only fallback.
4. Human-approved PO with the same frozen amount and currency.
5. Paid Sandbox order with verified provider evidence, protecting private identities.
6. Decision Passport with the selected offer, rejected alternative, time, authority and payment proof.

## Outcome claims: show evidence, not invented savings

A source snapshot showing a cheaper rejected product demonstrates a **prevented policy violation in this workflow**, not measured real-world cost savings. A PayPal Sandbox capture proves a **test payment**, not supplier fulfillment or settlement.

For a small and truthful usability comparison, recruit willing testers who are not the developer. Give them the **same stated purchasing requirement** once with a normal manual catalogue workflow and once with ProcurePilot, varying which task is done first to reduce learning bias. Record consent, test scenario, start/finish timestamps, required-specification errors, successful audit-record retrieval, whether assistance was needed, and provider downtime. Report raw observations, sample size and limitations; do not claim productivity gains, fraud reduction or live customer savings from a synthetic benchmark.

The strongest outcome to substantiate quickly is: **“The purchasing rules correctly rejected a real unsuitable offer while preserving a complete explanation and Sandbox proof for the eligible one.”**

## What this demo intentionally does NOT claim

- AI autonomously purchases or approves products.
- The chosen Channel3 retailer received an order or payment.
- All online offers and attributes are accurate after the original discovery timestamp.
- A rejected cheap listing represents realized savings.
- The system guarantees elimination of incorrect purchases or fraud.
- Signed webhook delivery happened, absent a verified provider event.
- An independent customer pilot has been completed, absent actual participants and records.

## Supporting material

- [Public Devpost project](https://devpost.com/software/procurepilot-ai)
- [Judge steps and separate Sandbox buyer login](JUDGE_ACCESS_PLAYBOOK.md)
- [Architecture and Decision Passport flow](architecture.md)
- [Source and setup](../README.md)
- [Official rules](https://paypalaihackathon.devpost.com/rules)
