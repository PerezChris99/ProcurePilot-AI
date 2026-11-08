# ProcurePilot AI — master submission checklist S01–S36

**Updated 8 November 2026.** [Official rules](https://paypalaihackathon.devpost.com/rules)
· Deadline: **Thursday 12 Nov 2026, 23:00 EAT (12:00 noon PST)**
· Judges need functional access during the **1–15 Dec 2026** judging period.
· Repository: https://github.com/PerezChris99/ProcurePilot-AI
· Hosted application: https://procurepilotai.vercel.app

**Completion status:** source-level functionality is extensively implemented, and the owner has now confirmed a completed PayPal Sandbox payment visible in PayPal. **The artifact-level submission remains open:** fresh QA, public HTTP acceptance, independent webhook evidence, sanitized payment receipt, judge-access handoff, public video and Devpost submission must not be marked complete without their own proof. This checklist deliberately does not call the project 100% verified. See [secure judge access](JUDGE_ACCESS_PLAYBOOK.md) and [submission text](DEVPOST_FINAL_DRAFT.md).

**Release baseline, 8 November:** `main` and `perez` were synchronized at `5dff11f`, and production plus Preview Vercel deployments were READY for that same SHA. New submission-document edits on `perez` require a fresh diff review, PR merge and deployment confirmation; READY is not equivalent to an external 7/7 probe.

## A. Fundamentals and eligibility

- [x] **S01** — Project identity and buyer problem explained ([README](../README.md)).
- [x] **S02** — PayPal Sandbox Orders v2 / webhook code implemented; the owner now reports a successfully completed Sandbox payment also visible in PayPal. Capture details and live webhook delivery are separately tracked under S23/S24.
- [x] **S03** — Google ADK / Gemini source integration implemented; real hosted proof outstanding.
- [x] **S04** — GitHub repository publicly accessible.
- [x] **S05** — MIT `LICENSE` committed.
- [x] **S06** — GitHub repository API detects `license.spdx_id=MIT`.
- [ ] **S07** — Entrant personally verifies eligibility, originality, third-party rights and sponsor conflicts.
- [x] **S08** — Significant Oct–Nov changes documented with dated commits
      ([event changelog](HACKATHON_CHANGELOG.md)); Devpost field still pending.

## B. Release quality

- [ ] **S09** — Reconfirm 9/9 for the CURRENT `perez` commit. An earlier 9/9 result was maintainer-reported for `d6e61cd`; it is not a new test run after PayPal capture-response changes or final presentation edits.
- [x] **S10** — Judge README, flow diagrams, local preview and run instructions.
- [ ] **S11** — Latest candidate passes clean-room 9/9, source/diff/secret review.
- [ ] **S12** — Complete final source/document diff review, then PR from the existing `perez` branch into `main`; verify a merged result and no orphaned work. The owner authorized this final-readiness work.
- [x] **S13** — As of the last deployment lookup on 8 Nov, production and Preview Vercel reported READY on `5dff11f` and `main`/`perez` matched. Recheck the next production deployment after final documentation and UI changes.

## C. Hosted Vercel + Neon

- [x] **S14** — `procurepilotai.vercel.app` attached; frontend/deep links returned 200.
- [ ] **S15** — Production FastAPI build gate proves in-process `/api/v1/health` 200 and `/api/v1/ready` 200, and browser auth works. An independent PUBLIC HTTPS health 200 JSON check and runtime log review are still missing.
- [x] **S16** — **Production Neon schema and connection verified by the backend Vercel build gate**: correct production host/role, Alembic `0010_auth_throttles`, all 11 tables, and in-process FastAPI readiness 200. Staging Neon is separately migrated to 0010; the Vercel Preview passed real SQL-backed registration/login/JWT/procurement creation. This is not a 7/7 public HTTP result.
- [ ] **S17** — Latest production 7/7 *public HTTP* probe is still missing. The old 2/7 result predated the now-working Vercel/Neon release, so it is obsolete. Rerun `qa/live_demo_check.py` from a machine with network access; Preview may require Vercel authentication.
- [x] **S18** — **Real provider connectivity proven in Vercel Preview:** Channel3 returned priced products, the bounded automatic ADK model route responded, and a separate exact-primary **Gemini-only ADK** probe passed without fallback. This is read-only provider acceptance; the full browser purchasing journey is a separate gate.
- [ ] **S19** — **Partially achieved:** owner confirmed fresh hosted registration, login and procurement creation on 8 Nov. Still requires explicit expired-session testing, two-account data isolation, logout and device refresh acceptance.

## D. Real PayPal Sandbox and evidence

- [ ] **S20** — Buyer need → real offers → rules → stored fixed-price PO.
- [ ] **S21** — Human approval/rejection audited; denied unauthorized reviewer.
- [x] **S22** — Owner-confirmed PayPal Sandbox buyer approval and completed transaction visible in PayPal on 8 Nov, using the now-functioning buyer flow. The earlier Business-seller login blocker is resolved; archive a sanitized receipt for judges.
- [ ] **S23** — Owner reports successful Sandbox transaction, and Orders v2 capture-response handling is implemented. Independently compare the saved PO with the actual provider order/capture ID, currency, amount and displayed paid status before checking this evidence gate.
- [ ] **S24** — Signed webhook reaches public HTTPS; replays/mismatches rejected.
- [ ] **S25** — Decision Passport and readable PDF reflect real evidence truthfully.

## E. Judge access and safety

- [ ] **S26** — Judge follows [secure access guide](JUDGE_ACCESS_PLAYBOOK.md) unaided in a fresh clean browser, including a distinct dedicated Personal Sandbox buyer; keep test credentials out of the public repo.
- [ ] **S27** — 375/768/1440px, keyboard, legible type and payment control QA.
- [ ] **S28** — Expired JWT, empty/no stock, provider outage and PayPal cancel recovery.
- [ ] **S29** — Provider keys rotated where needed; budgets, secrets, assets and Sandbox-only endpoints reviewed.
- [ ] **S30** — Service, domain and free judge credentials remain available to Dec 15.

## F. Submission package and confirmation

- [ ] **S31** — Real browser screenshots of source, approval, capture, Passport.
- [ ] **S32** — Public English YouTube footage of real working app under 3 minutes; use the [2:45 production script](DEVPOST_FINAL_DRAFT.md) and verify the YouTube URL and public visibility.
- [x] **S33** — Accurate [Devpost text draft](DEVPOST_FINAL_DRAFT.md) prepared for review; actual insertion into Devpost is a separate S35 submission action.
- [ ] **S34** — Precise tools/platform and genuine sponsor-category disclosure.
- [ ] **S35** — Public repo, runnable demo access, video and required fields entered.
- [ ] **S36** — Submitted Devpost entry confirmed before Nov 12 cutoff (not draft).

## Provider and checkout diagnosis (8 Nov)

- [x] **AI source-level root cause** — Repaired literal `\\n` sequences in the Python lazy runtime import/assignment block that caused HTTP 500 on eligible-offer analyses.
- [x] **Separate backend action semantics** — `/discover` only fetches/ranks/saves Channel3, while `/analyze` requires saved Channel3 evidence (409 otherwise) and does not search again.
- [x] **UI evidence labeling** — Search is a prerequisite to AI; old AI assessments are cleared after refreshing products and model outages are not mistaken for a successful model response.
- [x] **Staging route acceptance** — Verified real FastAPI + Neon request processing, with stubbed third-party providers: pre-search 409, search success, saved-evidence analysis success, cached retry, no extra catalogue/model calls and zero retained test rows.
- [x] **Read-only actual provider smoke** — Real Preview Channel3 priced offers, bounded ADK model-route output and PayPal Sandbox OAuth all passed; no payment created.
- [x] **Live direct-Gemini validation** — Preview deployed READY with an actual ADK Gemini-only response; fallback explicitly disabled for the probe. No purchase/provider-write action.
- [ ] **Sandbox buyer/capture/webhook proof** — Personal buyer must approve checkout independently of Business merchant; capture and signed webhook replay still require verified evidence.
- [ ] **Actual judge-browser flow** — Capture and audit complete hosted search → model response → human approval → Sandbox capture, including current full test suite and mobile UX.

See [search/AI and PayPal diagnosis](SEARCH_AI_PAYPAL_TRIAGE_2026-11-08.md). **The main S01–S36 count is 11/36** based on the separate, actual primary Gemini + Channel3 provider probes; paid capture and the judge demo remain unverified.

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
