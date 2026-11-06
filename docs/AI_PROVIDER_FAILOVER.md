# ProcurePilot AI — Google ADK + LiteLLM failover

## Purpose and boundaries

The procurement analyst uses **Google ADK** for every model call, including
backup providers. Normal route: native `gemini-3.5-flash-lite`; optional
route 2: `groq/openai/gpt-oss-20b`; optional route 3:
`openrouter/google/gemma-4-26b-a4b-it:free`. This is the LiteLLM provider prefix plus the OpenRouter model ID
`google/gemma-4-26b-a4b-it:free`. The previously configured free GPT-OSS
endpoint returned HTTP 404 on November 6, 2026; do not replace it with the
paid GPT-OSS slug. The `openrouter/free` convenience router has different
routing semantics and is not used as the default here. Both model choices can be changed to an enabled model
within the respective provider using the `AI_*_MODEL` settings.

No API secret is needed to keep the current Gemini-only behavior. LiteLLM
is an installed Python adapter, **not** a hosted proxy or subscription.

## Local configuration (do not commit real keys)

Use official consoles to issue credentials:
- Google AI Studio: https://aistudio.google.com/app/apikey
- Groq: https://console.groq.com/keys
- OpenRouter: https://openrouter.ai/keys

Set in **repository-root** `.env`:

```dotenv
GOOGLE_API_KEY=<your-existing-Google-key>
AI_MODEL=gemini-3.5-flash-lite
AI_FALLBACK_ENABLED=true
GROQ_API_KEY=<your-Groq-key>
AI_GROQ_MODEL=groq/openai/gpt-oss-20b
OPENROUTER_API_KEY=<your-OpenRouter-key>
AI_OPENROUTER_MODEL=openrouter/google/gemma-4-26b-a4b-it:free
AI_TIMEOUT_SECONDS=60
AI_DAILY_USER_RUNS=12
AI_DAILY_GLOBAL_RUNS=100
```

If your private root `.env` still contains `AI_OPENROUTER_MODEL=openrouter/openai/gpt-oss-20b:free`, update that value explicitly. Environment variables override the repository default. Run `Get-ChildItem Env:AI_OPENROUTER_MODEL` in your launch terminal to detect an inherited override.

If you have no backup key, leave the corresponding value empty. An absent
backup key does not cause a live API call. Set `AI_FALLBACK_ENABLED=false`
to force primary-only mode. Process environment variables override `.env`;
remove stale Windows `AI_MODEL` overrides before starting the server.
Restart the backend after modifying private configuration.

## Installation

From the project root in VS Code PowerShell:

```powershell
.\qa\setup.bat
.\test-all.bat
```

The backend requirements pin `litellm==1.84.0`, which satisfies the official
ADK minimum (`>=1.84`). Compromised 1.82.7/1.82.8 are intentionally
excluded. Inspect installed packages after updating dependencies; always
keep confidential keys out of command output.

The Windows smoke wrapper sets `PYTHONUTF8=1` before Python launch to avoid
a documented LiteLLM Windows encoding problem. For a VS Code backend launch,
set `PYTHONUTF8=1` in the launching environment before starting Python.

## Exact-provider and automatic smoke probes

```powershell
# These are read-only ADK model assessments: each consumes real provider quota.
.\smoke-providers.bat gemini 45 gemini
.\smoke-providers.bat gemini 45 groq
.\smoke-providers.bat gemini 45 openrouter

# Checks Channel3, automatic ADK routing and PayPal Sandbox OAuth.
.\smoke-providers.bat all 75
```

The JSON check named `gemini` reflects the existing CLI identifier;
inspect its `provider` and `model` fields for the provider that actually
answered. Explicit-provider probes never switch providers. Automatic routing
may consume up to **three model attempts** if every configured route fails in
turn. The Google SDK or LiteLLM may also internally retry HTTP requests.
Do not run provider smoke repeatedly on the free tier.

## Reliability and spending guarantees

- Every model attempt is executed through ADK with zero action tools and
  `RunConfig(max_llm_calls=1)`.
- **Only** transient 503/unavailable, timeout, transport and 429/quota responses
  can trigger a different provider. Invalid keys, denied permissions, invalid
  models and malformed evidence are not silently bypassed.
- The total ADK analysis window remains bounded by `AI_TIMEOUT_SECONDS`
  (10–90 seconds; default 60). The primary model can get a shorter slot to
  preserve enough time for a backup if one is configured.
- In the authenticated API, each model attempt reserves its own user/global
  SQL daily AI allowance. If quota runs out before backup, no backup call is
  issued. Repeated cached assessments incur no new model call.
- The recorded AI response includes the selected provider, configured route
  model and provider-supplied usage counters where available.
- If every enabled provider fails, return an honest 503 and retain the saved
  Channel3 price/stock/policy evidence. Never invent a successful AI answer.

The fallback provider receives **only the bounded, allowlisted evidence
packet**: request excerpt, product IDs, shortened titles, rankings, eligible
offer prices and policy decisions. No OAuth/PayPal secrets, approval
credentials or payment authority are sent. The procurement text and allowed
product evidence do reach the chosen model host, so review privacy/data use
policies for each external provider.

## Channel3 and PayPal integrity

Channel3 search and on-demand product lookup may retry once after a transient
transport error or HTTP 502–504. They never retry on invalid credentials,
rate limiting (429) or invalid response JSON. Response size limits and
deterministic policy checks remain intact.

PayPal Sandbox OAuth acquisition may retry once on transient transport/502–504.
**PayPal create-order, capture, and webhook verification requests are not
automatically replayed.** In uncertain payment states, inspect the persisted
order and PayPal Sandbox merchant activity before taking another user action.
This patch does not implement end-to-end exactly-once financial reconciliation.
The existing Sandbox-only enforcement and signed webhook checks remain.

## November 6 local test findings

The entrant's latest local offline QA showed **8 of 9 gates green**:
all **208 backend tests** (86% overall coverage), all **57 frontend tests**,
ESLint, deploy contracts, production build, syntax and built-asset checks passed.
Both SQLite migrations verified schema/revision correctly but Windows
temporary-folder cleanup failed with `WinError 32` because the verifier used
`with sqlite3.connect(...) as connection`, which is a transaction manager,
**not** a connection closer. The verifier now wraps its connection in
`contextlib.closing`. Two regression tests cover successful and failing
verification cleanup. These changes require a local rerun before QA is green.

The **OpenRouter** free Gemma route was accepted but returned HTTP **429 from
an upstream shared Google AI Studio provider pool**. This is a shared-rate
limit, not an invalid API key or missing model. Never silently substitute a
paid model or hammer the shared pool. Native Gemini and Groq had already
passed exact real-model smoke checks; automatic routing can use either. When
free OpenRouter is saturated, wait for capacity to return or temporarily
disable its private key until the free capacity is usable. An OpenRouter
configuration badge indicates key presence only, not guaranteed service
availability.

A later combined provider check showed Channel3 unavailable while Gemini and
PayPal Sandbox OAuth passed. The earlier Channel3 smoke response reported
only `Channel3Unavailable`, hiding whether the cause was HTTP 429, 503,
connection trouble or invalid catalogue JSON. The smoke runner now emits only
safe `category`, allowlisted `http_status`, and fixed `hint` fields to help
separate transient provider failure from configuration problems. It never
includes raw response bodies or credentials and does not retry on HTTP 429.

Local test sequence after syncing with `main`:

```powershell
git pull --ff-only origin main
.\test-all.bat
Get-Content .\qa\reports\summary.md
.\smoke-providers.bat channel3
.\smoke-providers.bat all 75
```

The final two commands make real provider requests; do not repeat them rapidly
on free quotas. If migration cleanup still fails, inspect any remaining
SQLite connection ownership or Windows antivirus/process file locks rather
than weakening the migration assertions. Full PayPal buyer/capture/webhook
tests remain separately required.

## Required acceptance before release

1. Run `test-all.bat` (Python tests including ADK/LiteLLM construction, JS
   tests, syntax, migrations and strict production build).
2. Test all three exact AI routes against real key-bearing accounts; reject
   unconfigured/missing keys without sending private values anywhere.
3. Temporarily force a Gemini 503 in a mocked local test and verify a single
   Groq fallback, proper quota reservation, correct answer provenance and
   preserved catalogue; do **not** simulate a real API success in the demo.
4. Walk through an actual saved catalogue request, AI explanation, purchase
   order, human approval and PayPal Sandbox personal-buyer capture.
5. Independently verify PayPal signed HTTPS webhooks, duplicate detection,
   amount/currency equality and database recovery on a public HTTPS backend.

Neither three provider green connectivity probes nor passing mocked tests
guarantees uptime, provider free-tier quotas, supplier inventory, external
merchant settlement, production security, or PayPal transaction correctness.

## Sources

- Google ADK LiteLLM adapter: https://adk.dev/agents/models/litellm/
- LiteLLM security note: https://docs.litellm.ai/blog/security-update-march-2026
- Groq model selection: https://console.groq.com/docs/models
- OpenRouter free model list: https://openrouter.ai/collections/free-models
- OpenRouter currently listed free Gemma endpoint (verify availability before relying on it):
  https://openrouter.ai/google/gemma-4-26b-a4b-it%3Afree
