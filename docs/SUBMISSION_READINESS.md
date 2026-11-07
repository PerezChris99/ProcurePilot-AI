# ProcurePilot AI — master submission checklist S01–S36

**Updated 7 November 2026.** [Official rules](https://paypalaihackathon.devpost.com/rules)
· Deadline: **12 Nov 2026, 23:00 EAT**
· Free judging access through **15 Dec 2026**
· Repository: https://github.com/PerezChris99/ProcurePilot-AI
· Intended website: https://procurepilotai.vercel.app

**Verified count: 10/36**, including source implementations and maintainer-confirmed
offline tests—not live third-party certification. New candidate changes must
be retested. Do not check a box without a real artifact or trace. No
automatic Git merge or Devpost submission.

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

- [x] **S09** — Maintainer confirmed 9/9 offline gates on `perez` at `d6e61cd`;
      **rerun for latest source** before the release.
- [x] **S10** — Judge README, flow diagrams, local preview and run instructions.
- [ ] **S11** — Latest candidate passes clean-room 9/9, source/diff/secret review.
- [ ] **S12** — User approves after online tests, then one `perez`→`main` PR/merge.
- [ ] **S13** — Deployed **production** SHA matches approved, retested release.

## C. Hosted Vercel + Neon

- [x] **S14** — `procurepilotai.vercel.app` attached; frontend/deep links returned 200.
- [ ] **S15** — Production FastAPI `/api/v1/health` returns 200 JSON; logs clear.
- [ ] **S16** — Actual Neon `procurepilot` schema at 0010; Vercel DB connectivity,
      registration and login verified. Database exists, SQL verification blocked.
- [ ] **S17** — All seven hosted read-only checks PASS (last result 2/7).
- [ ] **S18** — Actual hosted Channel3 search and Gemini/ADK response.
- [ ] **S19** — Fresh-account browser sign-in, expired-session and per-user isolation.

## D. Real PayPal Sandbox and evidence

- [ ] **S20** — Buyer need → real offers → rules → stored fixed-price PO.
- [ ] **S21** — Human approval/rejection audited; denied unauthorized reviewer.
- [ ] **S22** — Distinct Business Sandbox seller + Personal buyer complete approval.
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
