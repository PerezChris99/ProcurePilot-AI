# AI token economics and engineering safeguards

ProcurePilot uses **deterministic orchestration with a bounded Google ADK/Gemini evidence analyst**, not an unrestricted swarm of costly autonomous agents. Ranking, price, budget and order actions are exclusively backend responsibilities.

## Roles

| Part | Role | Model calls |
| --- | --- | --- |
| Channel3 | Live provider product discovery | Zero |
| Python scorer | Requirements, stock, budget, ranking | Zero |
| Evidence builder | Include policy-eligible price evidence in a 3600-character packet; reduce candidate count when needed | Zero |
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
 F --> G{Any eligible in-stock offer?}
 G -->|No| H[Policy-based catalogue-only response - zero model tokens]
 G -->|Yes| I[Policy-filtered compact JSON]
 I --> J{Global and user budget?}
 J -->|Exhausted| K[HTTP 429 - no LLM call]
 J -->|Allowed| L[Atomic reservation]
 L --> M[One capped ADK Gemini call]
 M --> N[Saved text and provider usage]
~~~

1. An initial **Ask AI** click performs one catalogue search if needed; no prerequisite clicks.
2. The backend preserves ranked results, only sends compact evidence to Gemini and avoids raw seller descriptions and arbitrary URLs.
3. The ADK RunConfig limit is **max_llm_calls=1**, low Gemini 3.x thinking effort, output-token ceiling and wall timeout; no unsupported temperature setting.
4. Provider-reported input, output, thinking, total and cached-input tokens are stored when supplied; unknown counters remain missing, never guessed. Saved `ai_prompt_characters` is a separate non-billing input-size measurement.
5. Repeated successful analysis or catalogue-only rejection uses the saved explanation without another model call until discovery is refreshed.
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
| AI_EVIDENCE_CANDIDATES | 4 | Validated 1 to 8; fewer may be selected when the prompt is near its character ceiling |
| AI_MAX_PROMPT_CHARS | 3600 | Validated 1500 to 8000; caps model evidence characters, not exact billed input tokens |

These are **call-count, prompt-size and output limits**, not exact USD/UGX billing guarantees. Provider rates change and input sizes vary; consult Gemini billing/usage metrics. ADK runtime documentation: https://adk.dev/runtime/runconfig/ . Agent config reference: https://adk.dev/api-reference/python/google-adk.html .

## Efficiency audit — release freeze

**Existing proven-by-code controls:** one tool-free ADK model request at most,
atomic per-user and global UTC-day call reservations, in-database cached
analysis, low Gemini 3.x thinking effort, short saved-evidence packet, no
second Channel3 search if a saved snapshot is present, and hard provider
timeouts. Prices, eligibility, stock and budget checks use deterministic code
with no model tokens.

**Changes for this release:** An all-blocked, out-of-stock or empty catalogue
now returns a truthful catalogue-only explanation with **zero Gemini calls**;
this includes repeat requests. Product evidence is filtered to the
buyer-policy-approved offer URLs, not merely the cheapest listing. The short
evidence packet has a strict 3600-character default maximum, trimmed
adaptively to valid JSON, with a 600-character request excerpt, shorter
titles and concise rejection reasons. If an eligible item appears beyond the
first shortlist positions it is pulled into the prompt. Target explanations
are at most **130 words**, without lowering the generation ceiling so far that
low-effort Gemini thinking might consume all output allowance. Provider
reasoning tokens are included when usage metadata reports them.

**Avoid needless complexity:** explicit Gemini context caching adds lifecycle
and minimum-input thresholds, and a short single-call packet is unlikely to
reach the 4096-token implicit cache threshold. Successful analysis is already
cached durably by ProcurePilot. Do not add a second model just to summarize
or compress the first one.

**Offline measurement (no API calls or secrets):**

```powershell
.\backend\.venv\Scripts\python.exe .\backend\scripts\agent_economy_audit.py
```

Run from the project root. It prints actual prompt characters, candidate
count and call-limit controls. **It cannot produce the number of billable
tokens or cost of a live call.** Only a successful ADK response and the
provider usage/billing dashboard can establish those. After the live
integration works, inspect the saved request's `analysis_json.ai_usage` for
`input_tokens`, `output_tokens`, `thinking_tokens`, `cached_input_tokens`
and `total_tokens`; check `analysis_json.ai_prompt_characters` separately.

**Residual risks:** Concurrent identical requests across API workers can
still race before the cache is written, consuming more than one reserved
attempt; the daily SQL quota limits damage but is not a distributed
single-flight lock. Failed/uncertain requests deliberately count toward
quotas. No fixed monetary budget can be guaranteed without observing actual
provider pricing and billing. A local 9-gate QA pass before this change does
not certify the updated code; rerun `test-all.bat`.

