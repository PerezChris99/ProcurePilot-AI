# Live infrastructure acceptance — judge deployment

This is the **minimum** read-only check before giving judges a hosted URL.
It cannot prove AI output, real catalogue responses, a buyer's PayPal Sandbox
approval, an actual capture, or a delivered signed webhook.

After deploying the reviewed version of **Vercel Services** and applying
Neon PostgreSQL migrations through `0010_auth_throttles`, run the following
from the repository root. Redis is optional: the application falls back to
atomic Neon counters for public auth throttling.

```powershell
python .\qa\live_demo_check.py --frontend https://procurepilotai.vercel.app --api https://procurepilotai.vercel.app
```

Record the JSON in the ignored `qa/reports/hosted.json` file using PowerShell
`| Tee-Object -FilePath .\qa\reports\hosted.json`. The report makes no
payment or account modifications. Run `python qa/report_release.py` to
verify the combined offline, Neon and hosted evidence before a merge review.

On macOS/Linux replace `python` with `python3`.

The script makes seven **read-only GET/OPTIONS requests**. It verifies:
- Public React homepage returns HTML.
- Direct `/orders` navigation returns SPA HTML (no 404).
- `/api/v1/health` is live.
- `/api/v1/ready` can read the configured database and migrated tables.
- The API CORS policy allows the exact public frontend origin.
- Signed-out purchase orders return 401.
- Signed-out Decision Trust Lab returns 401.

**Never** provide credentials, tokens or payment IDs as CLI arguments. A failure
returns a nonzero exit code and must be addressed before sharing the live URL.
A PASS means only the described infrastructure and anonymous authorization
checks were satisfied at that moment.

### Mandatory live tests that this script cannot perform

Run the human-involved [integration acceptance](INTEGRATION_ACCEPTANCE.md)
with rotated private credentials and a real **Sandbox Personal test buyer**.
Verify a real Channel3 search, Google ADK analysis or honest fallback,
purchase creation, required human approval, exact Sandbox capture with matching
amount/currency, webhook signatures including duplicate delivery, and an
accurate Decision Passport. Record a redacted result without merchant secrets.

For self-serve reproducible policy verification, sign into the hosted app
and open **Decision Trust Lab** from the overview. It executes twelve controlled
synthetic inputs through the same deterministic purchase eligibility function
and does not make any provider or payment calls. It is not a substitute for
the above live acceptance.

**Status:** No successful public deployment or real provider-payment acceptance
is inferred merely from these scripts being present in GitHub.
