# Significant hackathon-period work

This file documents substantive, verifiable development **during the
October 1–November 12, 2026 submission period**. Each example links to a
real repository commit. It is intended for a concise Devpost summary, not
a claim that every integration has passed live acceptance.

| Evidence | Actual work and distinctive contribution |
| --- | --- |
| [Trust Lab — 6 Nov](https://github.com/PerezChris99/ProcurePilot-AI/commit/85d84dd9) | Added an executable, synthetic scenario lab using real procurement predicates without provider transactions. |
| [Neon-backed auth throttling — 7 Nov](https://github.com/PerezChris99/ProcurePilot-AI/commit/d07a2ab244c2fc6a363694434eeb5f8b7e26ed8e) | Shared PostgreSQL login limits with atomic counters and an Alembic schema revision. |
| [Vercel + Neon foundation — 7 Nov](https://github.com/PerezChris99/ProcurePilot-AI/commit/0cf69e219602ac70957afd32dd1876d6028c6458) | Single-domain React/FastAPI routing, deploy entrypoint and secret-handling guide. |
| [Expired-session recovery — 7 Nov](https://github.com/PerezChris99/ProcurePilot-AI/commit/e7d331d551efb20daf8566743af3a2125e88e5a4) | Correct authentication recovery and PayPal-safe return URL continuity. |
| [Judge-focused README — 7 Nov](https://github.com/PerezChris99/ProcurePilot-AI/commit/fcff63feaa5a01f0f43fccade5b79bff365da32a) | Explainable decision, human authority and Sandbox proof with three Mermaid diagrams. |
| [Offline QA hotfix — 7 Nov](https://github.com/PerezChris99/ProcurePilot-AI/commit/d6e61cda6b8b149489a21ae93c702c39c33c21e3) | Updated migration/dep routing tests and pinned compatible FastAPI version for offline verification. |

**Devpost summary:** ProcurePilot evolved into an evidence-first purchasing
system: live catalogue integration in code, deterministic supplier eligibility
and mandate checks, bounded explanatory ADK/Gemini assistance, human-controlled
PO approval, PayPal Sandbox Orders v2 and verification, audit trails and
Decision Passport export. These features were built or significantly refined
during the event. An offline QA PASS is different from a hosted end-to-end
capture, which requires separate acceptance evidence.

See [architecture](architecture.md), [security](security.md) and
[provider gates](INTEGRATION_ACCEPTANCE.md).
