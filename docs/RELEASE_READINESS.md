# Controlled release and evidence — ProcurePilot AI

**Workflow:** implement on existing `perez` → verify offline → verify an isolated
preview with safe credentials → receive owner's explicit approval → one reviewed
merge to `main` → confirm production deployment SHA and recheck live services.

**No GitHub Actions. No extra Git branches. No automatic production promotion
without approval.** Do not trade away authentication, amount verification,
signed webhooks, or legitimate product evidence to make a check appear green.

## The three independently provable technical gates

| Gate | Proof | Status today |
| --- | --- | --- |
| Offline correctness | `qa/reports/summary.json`, nine passes | Maintainer reported 9/9 at `d6e61cd`; retest new candidate |
| Neon database | `qa/reports/neon.json`, TLS connection, schema 0010 and required tables | DB provisioned; SQL connection unverified because connected Neon plugin is pinned to nonexistent `owner` role |
| Hosted application | `qa/reports/hosted.json`, seven HTTP passes | Last reported 2/7, backend HTTP 500 |

### Step 1: pull and test the reviewed source

From repository root on Windows, using the existing Python virtualenv:

```powershell
git switch perez; git pull --ff-only origin perez
.\backend\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
.\test-all.bat
```

A passing build with mocked providers is **not** acceptance of a live model,
catalogue, buyer checkout, or HTTPS webhook.

### Step 2: initialize / verify Neon without revealing credentials

```powershell
.\backend\.venv\Scripts\python.exe .\qa\initialize_neon.py
```

Open [Neon Console](https://console.neon.tech/) → `procurepilot-ai` → Connect → `procurepilot` database → **Connection pooling OFF** → copy its **Direct** TLS connection string. Then run the initializer above. On Windows it reads the clipboard directly (no hidden paste prompt), clears the clipboard, and never prints the URL or writes it to a report. Alternatively pass `--input env` after privately setting `DATABASE_URL`. The script runs
`alembic upgrade head`, verifies `0010_auth_throttles`, and writes the
credential-free `qa/reports/neon.json` report.

**Do not reset tables or create demo users on the production DB just to pass
this check.** The old Neon plugin connection role `owner` does not exist;
this script verifies through a real, freshly supplied database connection.
A local Neon success does not prove that Vercel has the same correct URL.

### Step 3: safely test Vercel preview before merging

The Vercel project currently builds `perez` as a **preview** separate from
`main`. Test this preview through an authorized Vercel browser session
with a **separate staging database**. Production `DATABASE_URL` is scoped
to production and must not be copied into previews. If no staging database
and preview access are configured, **live preview acceptance remains blocked**.
Never disable protections or point a test account at production data to fake
a passing preview.

### Step 4: verify seven public gates after a controlled release

```powershell
python .\qa\live_demo_check.py --frontend https://procurepilotai.vercel.app --api https://procurepilotai.vercel.app | Tee-Object -FilePath .\qa\reports\hosted.json
```

For a protected Vercel `perez` Preview, open Settings → Deployment
Protection → **Protection Bypass for Automation** and create a temporary,
revocable token. Set `VERCEL_AUTOMATION_BYPASS_SECRET` privately in your
Windows PowerShell session. Then run the same seven checks with both
`--frontend` and `--api` pointing to
`https://procurepilotai-preview.vercel.app`. The script sends the secret
only to this exact preview host, never production or an arbitrary URL,
and refuses redirects to avoid credential leakage. Do not paste the
secret into GitHub, chat, logs or Devpost. Revoke it after preview QA.

For raw HTTP 500 diagnostics, use `python qa/hosted_readonly_check.py`.
The Vercel `backend/main.py` entrypoint now fails closed with HTTP 503 and
a **safe startup category** if an application import fails. Categories
`missing_runtime_dependency`, `runtime_import_failure`, and
`invalid_configuration` point to distinct operational causes; no raw
exception message is disclosed. If the host still returns
`FUNCTION_INVOCATION_FAILED` HTTP 500, inspect Vercel's Python runtime
and bundle logs. The diagnostic does **not** fix imports or authorize
account creation, provider calls, or payment handling.
Vercel's connected runtime-log reader previously returned HTTP 403; the
owner can view actual tracebacks under the deployment's Runtime Logs.

### Step 5: evaluate evidence (no Git writes)

```powershell
.\backend\.venv\Scripts\python.exe .\qa\report_release.py
```

If the current production build on `main` is still failing HTTP 500,
the 7/7 production report can only be obtained **after** its fix is
released. Before merge, use green local tests and an isolated, authorized
online preview as the release-review evidence; complete the production
7/7 gate **immediately after** the approved merge.

The tool's three-report PASS is a **post-release** evidence standard rather
than permission to merge untested source. It refuses to authorize review
unless all three reports pass on a clean
`perez` tree. It **does not** confirm provider payment, merge or deploy.

### Step 6: real-provider acceptance — human-assisted

- Real Channel3 products and one correctly excluded offer.
- One real Gemini/ADK analysis with accurate provider attribution.
- User-scoped buyer → saved PO → independent or authorized approval.
- Real PayPal **Sandbox** Business-seller checkout, separate Personal-buyer
  approval, explicit verified capture, matching currency/amount/order IDs.
- HTTPS signed webhook delivery, rejected forged event, duplicate replay,
  and a truthful Decision Passport/PDF.
- Fresh private browsing session, phone/tablet/desktop display, failure modes.

Detailed evidence: [Provider acceptance](INTEGRATION_ACCEPTANCE.md).
No real money, retail merchant settlement, or unlicensed content.

### Step 7: release only with explicit approval

The owner reviews `perez` changes, offline gate output, sanitized online
evidence, actual provider test and domain. Only after explicit approval:
merge the existing `perez` into `main` through a single PR, wait for
the production deployment, confirm the exact SHA, then rerun the live gates.
The GitHub integration builds `perez` previews automatically; avoid repeated
pushes. Preview and production databases must be isolated.

## Submission handoff

[Master submission checklist](SUBMISSION_READINESS.md) tracks S01–S36.
Prepare [Devpost copy and video storyboard](HACKATHON_SUBMISSION_KIT.md),
then capture real browser screenshots and a public YouTube video under 3:00.
Submit on Devpost before 12 November 2026, 23:00 EAT. Keep free judge
access through 15 December 2026.
