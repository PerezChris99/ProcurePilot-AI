# ProcurePilot AI — first-place execution plan (8–12 November 2026)

**Competition:** [PayPal AI Hackathon](https://paypalaihackathon.devpost.com/) ·
**Deadline:** Thursday **12 November 2026, 23:00 EAT** (12:00 noon PST) ·
**Target:** 1st overall ($12,000); 2nd ($8,000) / 3rd ($5,000) alternatives;
best sponsor fit **Channel3** ($1,500) ·
**Primary project identity:** *Every purchase has a reason.*

> This is a **competition strategy**, not a promise of prize placement or
> verified live provider results. The judges, eligibility, and prize allocation
> are controlled by the organizers. The official rules limit each project to
> **one Grand Prize + one Sponsor Prize, OR one Honorable Mention + one Sponsor Prize**;
> you cannot win all grand/honorable categories simultaneously. Do not state
> eligibility for sponsor prizes without genuinely integrated technology.

## 1. The differentiator judges must understand immediately

**ProcurePilot is not another AI shopping chatbot.** It turns a business
purchasing need into a defensible, policy-compliant transaction with its
evidence frozen in a **Decision Passport**.

Show the trust boundary explicitly:

- **Channel3 provides real product/offer data**, with source/provenance and stock/price uncertainty handled honestly.
- **Deterministic policy** rejects offers that violate specifications, currency, budget or availability; it, not AI prose, decides eligibility.
- **Gemini through Google ADK** compares permitted evidence. It does **not** authorize a purchase and must be attributed accurately.
- **A human authorizes** the frozen purchase order under recorded buyer rules.
- **PayPal Sandbox** provides real *test* buyer approval, deliberate capture and signed-webhook/payment evidence. This is not real retailer settlement.
- **Decision Passport** makes source, AI reasoning, policy, approval and payment traceable afterwards.

**One-sentence pitch:** "ProcurePilot turns AI-assisted purchasing into an auditable decision: verified offers, enforced rules, human approval, PayPal Sandbox payment evidence, and a portable Decision Passport."

## 2. Attack all five equally weighted criteria (20% each)

| Judging criterion | Judge-facing proof to show, not merely claim | Release blocker |
| --- | --- | --- |
| **Technological implementation** | One live request → Channel3 offer evidence → bounded ADK/Gemini explanation → guarded PO → approver decision → PayPal Sandbox create/approval/capture → webhook/Passport | Without real capture and signed webhook, a payment screenshot or mock is insufficient |
| **Design** | Fast readable signup, organized dashboard, high-contrast reason badges, one clear primary action per screen, mobile flow at 375/768/1440px | No clipped data, excessive text, confusing loading states or generic widgets |
| **Potential impact** | One specific buyer persona with a concrete business need; explain why cheapest is not always compliant, and what evidence saves review time | Do not invent ROI, savings percentages or users/interviews |
| **Innovation** | Explicitly reject a cheaper invalid quote, preserve the lowest eligible quote and freeze a Decision Passport linking all approvals/payment evidence | Distinguish it from a generic AI product finder |
| **Presentation** | Under-three-minute authentic single story showing all core systems actually working with readable evidence | Video missing, overly fast narration, mocked providers or concealed failures |

Prizes are **not** scored independently per feature. A technically impressive
but hard-to-follow video can lose on the equally weighted Presentation axis.

## 3. Award portfolio within official rules

1. **Primary:** 1st overall; backups 2nd and 3rd (same entry and same five criteria).
2. **Honorable alternatives:** Best Use of PayPal + AI (prove real provider calls), Best Use of Agentic Commerce (truthfully human-controlled), Best Demo Delivery (highest priority narrative), Most Impactful (concrete buyer problem), Most Creative (Decision Passport).
3. **Sponsor:** Best Use of Channel3 — only after proving actual Channel3 provider results and source-linked rejected/eligible offers.

Do not add AG Grid or Render just to claim a new category in the final days.
If one of those tools substantially improves the **working** story, assess its
integration and new test surface first. PayPal+AI, Channel3 and the existing
Decision Passport are stronger than five unproven sponsors.

Maximum allowed combination using existing sponsor integration, if awarded:
**$13,500 (1st Overall $12,000 + Channel3 $1,500)**. This is a theoretical
award combination, not an expected result.

## 4. Four-day execution and freeze

| Date, EAT | Priority and completion definition |
| --- | --- |
| **Sun 8 Nov** | Land auth latency improvements on Preview without weakening Argon2, verify real signup/login and page responsiveness, refresh evidence checklist, confirm 7/7 hosted health probe |
| **Mon 9 Nov** | Real Channel3 and Gemini evidence, then full PayPal Business seller / Personal buyer Sandbox create–approve–capture flow, verify signed webhook + duplicate handling; capture sanitized log/screenshots |
| **Tue 10 Nov** | Complete judge browser rehearsal and impact example, record 2:40–2:50 authentic video with clean audio, review on phone/full HD, fix only demo-blocking issues |
| **Wed 11 Nov** | Freeze code, run final clean-room 9/9 + hosted 7/7 and PayPal evidence checks, publish public YouTube, finalize Devpost fields, submit **one day early** and verify "Submitted" status |
| **Thu 12 Nov** | Contingency only. Hard deadline **23:00 EAT**; never rely on last-minute uploads or provider quota availability |

Priority is **P0: correctness and demo evidence**, **P1: responsive UX and
clear narration**, **P2: nonessential extras**. Stop optional feature work
after Monday unless it blocks the truthful demo.

## 5. Under-3-minute demo storyboard (target 2:45)

| Timestamp | What is actually visible | Why it matters |
| --- | --- | --- |
| **0:00–0:12** | Real product dashboard and buyer pain: "A cheaper quote isn't always a safe purchase." | Impact and hook |
| **0:12–0:30** | Create specific need, quantity, currency, budget and hard policy. No sensitive account creation shown. | Real buyer context |
| **0:30–0:58** | Channel3 real products; one cheap noncompliant offer visibly rejected; one eligible product | Honest source and deterministic enforcement |
| **0:58–1:17** | Real bounded Gemini analysis, clearly attributed to provider and source evidence | Meaningful AI, not placeholder prose |
| **1:17–1:43** | Fixed-price purchase order, submission, human approval in a separate authorized account | Human control, auditability |
| **1:43–2:14** | Actual PayPal Sandbox buyer approval and return; show sandbox hostname and hide buyer identifiers | Functional test payment journey |
| **2:14–2:34** | Explicit capture with amount/currency/ID consistency and state transition | Payments engineering, no phantom "paid" state |
| **2:34–2:45** | Export Decision Passport, show policy, source, approver, provider evidence; final tagline | Memorable differentiation |

**Recording rules:** Use 1080p or 1440p and visible type, deliberate cursor,
neutral audio without unlicensed music, clean browser tabs, no exposed keys,
session tokens, email identities or payment credentials. Rehearse one uncut
working path before editing; cut only real recorded material, not staged fake
green checks. Do not imply PayPal Sandbox pays a real Channel3 merchant.

**If PayPal Sandbox cannot complete:** do not fabricate capture proof. Show the
exact tested functionality and state remaining work honestly. However, this
weakens the technological implementation criterion; prioritize resolving it.

## 6. Deliverables and judge access

- **GitHub:** public open-source repo (MIT), clear setup for Windows/macOS/Linux, environment template without secrets, architectural diagrams, security/limitations, test commands, precise PayPal Sandbox explanation, troubleshooting.
- **Devpost:** final plain-English problem, what it does, full workflow, real technical stack with tools/versions, challenges overcome (Neon/Vercel auth), innovations, limitations, future roadmap and correct sponsor declarations.
- **Working demo:** public HTTPS app accessible without invitation; provide **private disposable judge credentials only through appropriate secure private channel** if needed, never committed to README.
- **Evidence folder:** real 375/768/1440 screenshots, readable Channel3 results/one rejection, Gemini response/provider attribution, approval, PayPal verified capture, actual webhook handling and Passport PDF. Redact PII.
- **YouTube:** public video **strictly under 3 minutes**, link included in Devpost, copyright/third-party trademark rules respected.
- **Submission:** all fields completed, public repo/license linked, correct URLs, final "Submitted" status verified, not just draft; keep judge access working through **15 Dec 2026**.

## 7. Truthful progress as of 8 Nov

**Verified:** real hosted signup/login/procurement creation reported by owner;
production Vercel/Neon ready gate and staged isolated SQL auth flow; source
implementation for Channel3, ADK, PayPal, approvals, policy and Passport;
public MIT-licensed source.

**Not verified yet:** end-to-end real hosted Channel3/Gemini outputs,
PayPal Sandbox Personal buyer approval + explicit capture, signed public webhook
replay, public 7/7 read-only probe, clean-room current 9/9 test suite,
external judge usability, polished YouTube footage, Devpost final submission.

See [master checklist](SUBMISSION_READINESS.md). Update status ONLY from
actual proof, using 3 states: passed / partial / missing. Do not promote code
presence to completed third-party acceptance.

## Official references

- https://paypalaihackathon.devpost.com/
- https://paypalaihackathon.devpost.com/rules
- https://paypalaihackathon.devpost.com/details/dates
- https://developer.paypal.com/community/blog/PayPal_AI_Hackathon/
