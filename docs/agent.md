# AI token economics and engineering safeguards

ProcurePilot uses **deterministic orchestration with a bounded Google ADK/Gemini evidence analyst**, not an unrestricted swarm of costly autonomous agents. Ranking, price, budget and order actions are exclusively backend responsibilities.

## Roles

| Part | Role | Model calls |
| --- | --- | --- |
| Channel3 | Live provider product discovery | Zero |
| Python scorer | Requirements, stock, budget, ranking | Zero |
| Evidence builder | Clip/allowlist up to four saved candidates | Zero |
| Daily budget service | Reserve calls in atomic SQL transaction | Zero |
| ADK analysis_agent | Explain verified saved evidence in plain language | One maximum |
| Purchase-order and payment routes | Snapshot, approve, checkout and capture | Zero |

A legacy tool-capable root_agent remains in the code for future controlled research, capped at three calls; the normal public /analyze endpoint uses the **tool-free** analysis_agent. This is intentional and prevents duplicate catalogue queries.

## Single-analysis pipeline

~~~mermaid
flowchart LR
 A[Procurement request] --> B{Saved analysis?}
 B -->|Yes| C[Cached answer - zero tokens]
 B -->|No| D{Saved Channel3 results?}
 D -->|No| E[One catalogue search + deterministic rank]
 D -->|Yes| F[Reuse saved results]
 E --> F
 F --> G{Any evidence?}
 G -->|No| H[Catalogue-only response - zero tokens]
 G -->|Yes| I[Compact allowlisted JSON]
 I --> J{Global and user budget?}
 J -->|Exhausted| K[HTTP 429 - no LLM call]
 J -->|Allowed| L[Atomic reservation]
 L --> M[One capped ADK Gemini call]
 M --> N[Saved text and provider usage]
~~~

1. An initial **Ask AI** click performs one catalogue search if needed; no prerequisite clicks.
2. The backend preserves ranked results, only sends compact evidence to Gemini and avoids raw seller descriptions and arbitrary URLs.
3. The ADK RunConfig limit is **max_llm_calls=1**, low temperature, output-token limit and wall timeout.
4. Available usage metadata (input, output, total, cached input tokens) is saved with the request; if absent, totals are not invented.
5. Repeated analysis uses the saved text without model cost until the user deliberately refreshes discovery.
6. Errors leave verified Channel3 results usable and do not generate fake AI answers.
7. Quota exhaustion has an explicit 429 and Retry-After; incomplete/uncertain provider requests consume reserved allowance to avoid accidental excess spending.

## Backend settings

| Variable | Default | Limit / meaning |
| --- | --- | --- |
| GOOGLE_API_KEY | Empty | Required for real Gemini analysis |
| AI_MODEL | gemini-3.8-flash in .env.example | Model choice, backend only |
| AI_MAX_OUTPUT_TOKENS | 900 | Validated 256 to 2048 |
| AI_TIMEOUT_SECONDS | 35 | Validated 10 to 90 |
| AI_DAILY_USER_RUNS | 12 | Calls per user per UTC day |
| AI_DAILY_GLOBAL_RUNS | 100 | Calls across users per UTC day |
| AI_EVIDENCE_CANDIDATES | 4 | Validated 1 to 8 |

These are **call-count and output limits**, not exact USD/UGX billing guarantees. Provider rates change and input sizes vary; consult Gemini billing/usage metrics. ADK runtime documentation: https://adk.dev/runtime/runconfig/ . Agent config reference: https://adk.dev/api-reference/python/google-adk.html .

## Guardrails and limitations

- Agent cannot approve, change or pay for an order, read credentials, fetch arbitrary URLs or run shell commands.
- Supplier text is untrusted. Short JSON evidence, no full product descriptions or tracking links, and static instructions reduce the scope for prompt injection.
- Delivery, merchant checkout, payment status and missing product facts are declared **unverified** rather than invented.
- No unbounded agent loops, delegation trees or automatic retries.
- Guardrails are defense in depth, not formal proof of factual accuracy. A human sees the original retailer offer and must approve.
- Not yet implemented: dedicated red-team prompt-injection evaluation suite, hallucination benchmark, billing reconciliation or provider-specific monetary budget enforcement.

## Acceptance checklist

Run backend Pytest for evidence shaping, caching, quotas and max-call constraints; run frontend tests. Separately make an authenticated real Gemini analysis with valid credentials, inspect provider usage, repeat it to verify caching, test exhausted quota, and test failure states. A mocked ADK runner or an existing API key alone is not proof of real provider availability.
