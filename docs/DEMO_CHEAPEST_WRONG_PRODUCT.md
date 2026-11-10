# Demo walkthrough — when the cheapest product is wrong

**ProcurePilot AI · 1 minute 59 seconds** (creator-reported video length)  
[Watch on Devpost](https://devpost.com/software/procurepilot-ai) · [Try the application](https://procurepilotai.vercel.app)

## The question

**“What happens when the cheapest product is the wrong product?”**

A business needs two 27-inch monitors. A lower-priced 24-inch model, if returned by the live catalogue, **does not qualify**. ProcurePilot prioritizes buyer requirements over a tempting price and preserves the evidence behind the selected order.

## The story shown by the product

~~~mermaid
flowchart LR
    R["Business need"] --> S["Real product search"]
    S --> Q{"Meets requirements?"}
    Q -->|No| X["Reject + explain why"]
    Q -->|Yes| A["AI explains options"]
    A --> H["Human approves"]
    H --> P["PayPal Sandbox test"]
    P --> D["Decision Passport"]
~~~

| Stage | What to look for |
| --- | --- |
| **Request** | Specific item, quantity, currency, budget and mandatory requirements |
| **Product search** | Actual Channel3 offers; eligible and ineligible offers with reasons |
| **AI explanation** | Gemini/ADK analysis only when genuinely returned; otherwise clearly labelled rules-only assessment |
| **Approval** | Selected eligible offer and server-frozen order amount approved by a human |
| **PayPal** | Separate Personal Sandbox buyer approval; explicit validated capture |
| **Passport** | Source snapshot, rejection context, approver, audit trail and Sandbox payment proof |

## Why it is different

The **Decision Passport** does not merely show an item and a total: it records **what qualified, what was rejected, who authorized the order and how the test payment was confirmed**. It can be inspected and exported as JSON/PDF.

**Evidence rules:** Call an unsuitable listing *the cheapest* only if genuine, saved same-currency and same-quantity offers establish that price order. A cheaper ineligible listing is **not realized savings**. The optional **Decision Trust Lab** uses clearly labelled synthetic policy fixtures, not live Channel3 inventory.

**Scope:** PayPal **Sandbox** payments use virtual money; the system does not pay or place an order with the listed retailer. A browser return does not prove capture, and successful demonstration of a test payment does not prove live signed-webhook delivery.

## Explore

[Judge quick start](JUDGES_START_HERE.md) · [Private Sandbox buyer instructions](JUDGE_ACCESS_PLAYBOOK.md) · [Architecture](architecture.md) · [Source and tests](../README.md)
