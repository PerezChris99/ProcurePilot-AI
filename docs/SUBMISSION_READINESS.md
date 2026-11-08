# ProcurePilot AI — master submission checklist S01–S36

**Updated 8 November 2026.** [Official rules](https://paypalaihackathon.devpost.com/rules)
· Deadline: **Thursday 12 Nov 2026, 23:00 EAT (12:00 noon PST)**
· Judges need functional access during the **1–15 Dec 2026** judging period.
· Repository: https://github.com/PerezChris99/ProcurePilot-AI
· Hosted application: https://procurepilotai.vercel.app

**Verified completion: 10/36 submission gates.**
Checkboxes are binary: source-level implementation can satisfy a code gate,
but cannot replace a live PayPal or Gemini acceptance, a browser audit,
or the Devpost submission. Partial progress is explained below without checking
the remaining work off. Status incorporates owner-confirmed hosted account
creation/login/procurement creation on 8 Nov, production Vercel and Neon
build-gate evidence, and the latest GitHub source review.

**Current change candidate:** authentication latency optimization on existing
`perez` (batched DB throttle and reduced registration SQL roundtrips).
Performance improvements are **source-implemented but NOT yet certified faster
for actual public users**, pending a passing Preview regression build and
browser latency measurements. `main` remains the known working release
until separately reviewed.

## A. Fundamentals and eligibility

- [x] **S01** — Project identity and buyer problem explained ([README](../README.md)).
- [x] **S02** — PayPal Sandbox Orders v2 / webhook code implemented; **not** a live capture PASS.
- [x] **S03** — Google ADK / Gemini source integration implemented; real hosted proof outstanding.
- [x] **S04** — GitHub repository publicly accessible.
- [x] **S05** — MIT `LICENSE` committed.
- [x] **S06** — GitHub repository API detects `license.spdx_id=MIT`.
- [ ] **S07** — Entrant personally verifies eligibility, originality, third-party rights and sponsor conflicts.
- [x] **S08** — Significant Oct–Nov changes documented with dated commits
      ([event changelog](HACKATHON_CHANGELOG.md)); Devpost field still pending.

## B. Release quality

- [ ] **S09** — Reconfirm 9/9 for the CURRENT `perez` commit. Latest attached
      report: 8/9, with Trust Lab and public legal-page Vitest timeouts.
      Tests and worker scheduling were corrected, but not yet rerun locally.
- [x] **S10** — Judge README, flow diagrams, local preview and run instructions.
- [ ] **S11** — Latest candidate passes clean-room 9/9, source/diff/secret review.
- [ ] **S12** — User approves after online tests, then one `perez`→`main` PR/merge.
- [ ] **S13** — Production and Preview deployed `fa5f321` and `main`/`perez` were synchronized after PR #55. Current auth-speed candidate is not yet approved/retested for production; the release gate remains open.

## C. Hosted Vercel + Neon

- [x] **S14** — `procurepilotai.vercel.app` attached; frontend/deep links returned 200.
- [ ] **S15** — Production FastAPI build gate proves in-process `/api/v1/health` 200 and `/api/v1/ready` 200, and browser auth works. An independent PUBLIC HTTPS health 200 JSON check and runtime log review are still missing.
- [x] **S16** — **Production Neon schema and connection verified by the backend Vercel build gate**: correct production host/role, Alembic `0010_auth_throttles`, all 11 tables, and in-process FastAPI readiness 200. Staging Neon is separately migrated to 0010; the Vercel Preview passed real SQL-backed registration/login/JWT/procurement creation. This is not a 7/7 public HTTP result.
- [ ] **S17** — Latest production 7/7 *public HTTP* probe is still missing. The old 2/7 result predated the now-working Vercel/Neon release, so it is obsolete. Rerun `qa/live_demo_check.py` from a machine with network access; Preview may require Vercel authentication.
- [ ] **S18** — **Partial provider proof:** one-shot Vercel Preview real-provider gate passed a Channel3 search returning priced offers and a bounded ADK model route (could be a configured fallback); the exact primary-Gemini-only check and a full judge-browser interaction remain to be certified.
- [ ] **S19** — **Partially achieved:** owner confirmed fresh hosted registration, login and procurement creation on 8 Nov. Still requires explicit expired-session testing, two-account data isolation, logout and device refresh acceptance.

## D. Real PayPal Sandbox and evidence

- [ ] **S20** — Buyer need → real offers → rules → stored fixed-price PO.
- [ ] **S21** — Human approval/rejection audited; denied unauthorized reviewer.
- [ ] **S22** — **Blocked by Sandbox identity confusion:** merchant API OAuth passed the real Preview probe, but PayPal refuses the checkout because the browser is signing in as the same Business Sandbox seller. Buyer must log out there and approve with a distinct Personal Sandbox account; no real buyer approval recorded yet.
- [ ] **S23** — Explicit capture matches amount, currency, order and capture IDs.
- [ ] **S24** — Signed webhook reaches public HTTPS; replays/mismatches rejected.
- [ ] **S25** — Decision Passport and readable PDF reflect real evidence truthfully.

## E. Judge access and safety

- [ ] **S26** — Judge follows instructions unaided in fresh clean browser.
- [ ] **S27** — 375/768/1440px, keyboard, legible type and payment control QA.
- [ ] **S28** — Expired JWT, empty/no stock, provider outage and PayPal cancel recovery.
- [ ] **S29** — Provider keys rotated where needed; budgets, secrets, assets and Sandbox-only endpoints reviewed.
- [ ] **S30** — Service, domain and free judge credentials remain available to Dec 15.

## F. Submission package and confirmation

- [ ] **S31** — Real browser screenshots of source, approval, capture, Passport.
- [ ] **S32** — Public English YouTube footage of working app under 3 minutes.
- [ ] **S33** — Complete accurate Devpost description.
- [ ] **S34** — Precise tools/platform and genuine sponsor-category disclosure.
- [ ] **S35** — Public repo, runnable demo access, video and required fields entered.
- [ ] **S36** — Submitted Devpost entry confirmed before Nov 12 cutoff (not draft).

## Provider and checkout diagnosis (8 Nov)

- [x] **AI source-level root cause** — Repaired literal `\\n` sequences in the Python lazy runtime import/assignment block that caused HTTP 500 on eligible-offer analyses.
- [x] **Separate backend action semantics** — `/discover` only fetches/ranks/saves Channel3, while `/analyze` requires saved Channel3 evidence (409 otherwise) and does not search again.
- [x] **UI evidence labeling** — Search is a prerequisite to AI; old AI assessments are cleared after refreshing products and model outages are not mistaken for a successful model response.
- [x] **Staging route acceptance** — Verified real FastAPI + Neon request processing, with stubbed third-party providers: pre-search 409, search success, saved-evidence analysis success, cached retry, no extra catalogue/model calls and zero retained test rows.
- [x] **Read-only actual provider smoke** — Real Preview Channel3 priced offers, bounded ADK model-route output and PayPal Sandbox OAuth all passed; no payment created.
- [ ] **Live direct-Gemini validation** — Verify primary Gemini rather than relying on automatic fallback; stage one exact-provider smoke without a transaction.
- [ ] **Sandbox buyer/capture/webhook proof** — Personal buyer must approve checkout independently of Business merchant; capture and signed webhook replay still require verified evidence.
- [ ] **Actual judge-browser flow** — Capture and audit complete hosted search → model response → human approval → Sandbox capture, including current full test suite and mobile UX.

See [search/AI and PayPal diagnosis](SEARCH_AI_PAYPAL_TRIAGE_2026-11-08.md). **The main S01–S36 count stays 10/36** until all corresponding official evidence is supplied.

## G. Authentication performance (not counted in S01–S36)

- [x] **P01 source** — Profiled the registration/login path and identified two sequential remote PostgreSQL auth-throttle UPSERTs plus a post-commit registration SELECT.
- [x] **P02 source** — Implemented one atomic multi-bucket UPSERT and a pre-commit response snapshot; Argon2id and strict rate-limit checks retained.
- [x] **P03 targeted proof** — Standalone SQLAlchemy/SQLite execution demonstrated one UPSERT per auth attempt and retained both counters; automated regression tests committed.
- [x] **P04 Preview SQL acceptance** — Vercel Preview deployed optimized backend READY, with real staging Neon registration 201, login 200, JWT /me 200, procurement 201, health/readiness 200 and a SQLAlchemy event proving exactly one auth limiter INSERT for registration and one for login; independently verified zero leftover disposable users/orders.
- [ ] **P05 offline QA** — Run complete `test-all.bat` / 9/9 and targeted pytest from a fully installed local environment. The Vercel backend builder does **not** contain pytest; its isolated pytest gate was replaced with real staging integration checks.
- [ ] **P06 measurable speed** — Measure cold/warm sign-in and sign-up before vs after release, capturing p50/p95 browser timings, dashboard usability and stable auth-error behavior; do not exceed throttle limits.
- [ ] **P07 release** — Owner approves Preview; merge `perez`→`main`, verify production SHA and rerun public health/ready/login without touching PayPal state.

For technical details and exact test scope see [authentication performance report](AUTH_PERFORMANCE_2026-11-08.md).\n\n**Latency reality:** The code removes two round trips from the sign-up path
(one batched limiter write in place of two; one post-commit read eliminated)
and one round trip from the login limiter path. Total user-visible time also
depends on Argon2's deliberately secure CPU work, Neon latency, Vercel cold
starts and frontend bundle loading. No unsupported percentage speed-up claim.

## H. Prize-focused readiness (not counted in S01–S36)

- [ ] **W01** — Prove the entire legitimate PayPal Sandbox buyer approval, explicit capture and signed webhook flow; retain amount/currency/idempotency evidence.
- [ ] **W02** — Prove real Channel3 offers and one AI response with accurate provider attribution, constrained by buyer's deterministic policy.
- [ ] **W03** — Capture one concrete, truthful impact example and one meaningful ineligible-offer rejection.
- [ ] **W04** — Rehearse a judge-led 3-minute walkthrough with accessible text, no secret leakage, and no fabricated PayPal checkout.
- [ ] **W05** — Produce a polished public YouTube demo **under 3 minutes**, screenshots, final technical documentation and Devpost description.
- [ ] **W06** — Independent judge-style run, final QA, Devpost submit confirmation and free demo access through judging.

See [winning execution plan](WINNING_EXECUTION_PLAN_2026-11-08.md).

## Next evidence commands

From the project root on Windows:

```powershell
.\test-all.bat
.\backend\.venv\Scripts\python.exe .\qa\initialize_neon.py
python .\qa\live_demo_check.py --frontend https://procurepilotai.vercel.app --api https://procurepilotai.vercel.app | Tee-Object -FilePath .\qa\reports\hosted.json
.\backend\.venv\Scripts\python.exe .\qa\report_release.py
```

**Warning:** Running the Neon initializer applies `alembic upgrade head`
to the **selected** actual database, with the copied private Direct connection URL.
Do not pass a production URL to a disposable test. The hosted probe is
GET/OPTIONS only; it never tests payments. Read the
[release playbook](RELEASE_READINESS.md) before execution.
