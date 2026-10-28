# SettleIQ — Documentation Index

SettleIQ is an **independent** payment settlement reconciliation and discrepancy investigation engine, built as a demonstrated engineering artifact for employment evidence. It is not governed by any other repository, and it makes no claim about competitors, no market-gap claim, and no commercial-viability claim.

## Canonical documents

**Specifications** (`docs/specifications/`) — all PROPOSED; **no implementation exists**:

| # | Document | Domain of authority |
|---|---|---|
| — | `SETTLEIQ-MASTER-SPEC.md` | Sole authority for scope, frame, and requirements |
| 01 | `01_OBJECTIVES_AND_BOUNDARIES.md` | Objectives, independence, boundaries, success criteria |
| 02 | `02_PROBLEM_AND_USE_CASES.md` | Problem statement, actors, use cases, scope |
| 03 | `03_EVIDENCE_AND_RESEARCH_REGISTER.md` | Research record; verified / not verified / contradicted claims |
| 04 | `04_REQUIREMENTS_AND_NON_GOALS.md` | Consolidated requirement register and binding non-goals |
| 05 | `05_ARCHITECTURE.md` | Components, boundaries, deployment view |
| 06 | `06_DATA_MODEL_AND_PERSISTENCE.md` | Canonical types, schema, migrations, transaction boundaries |
| 07 | `07_RECONCILIATION_ENGINE_SPEC.md` | Decomposition, matching, confidence, fail-closed, determinism |
| 08 | `08_DISCREPANCY_AND_AUDIT_SPEC.md` | Typed taxonomy, investigation workflow, hash-chained audit |
| 09 | `09_API_AND_INTEGRATION_SPEC.md` | REST/OpenAPI, frozen `SourceAdapter` interface, idempotency |
| 10 | `10_DASHBOARD_SPEC.md` | Five functional views |
| 11 | `11_TESTING_AND_PERFORMANCE_SPEC.md` | Seven test classes, Decimal gates, tamper suite, benchmark gate |
| 12 | `12_DECISIONS_AND_OPEN_QUESTIONS.md` | The five engineering questions, ADRs, open questions |
| 13 | `13_ROADMAP_AND_ACCEPTANCE.md` | Milestones, dependency graph, release gates |
| 14 | `14_EMPLOYMENT_EVIDENCE.md` | Skills-to-artifact mapping; what the project does **not** teach |
| 15 | `15_RISKS_AND_NON_GOALS.md` | Risk register with verifiable mitigations; non-goals |
| 16 | `16_DECISION_REGISTER_AND_RESOLUTIONS.md` | Architecture decision baseline; resolution of all eight outstanding engineering questions |
| 17 | `17_TRACEABILITY_MATRIX_AND_CONSISTENCY.md` | Requirements-to-verification traceability; eight-class consistency findings |
| 18 | `18_M1_IMPLEMENTATION_PLAN.md` | M1 file-level scope and acceptance criteria — **a plan, not an authorization** |

**Research record** (`docs/research/`):

| Document | Status |
|---|---|
| `02_verification_log.md` | Active — append-only discipline; primary source for verification status |

**Where this index and a specification differ, the master specification governs. Where any document and the verification log differ, the verification log governs.**

## Reading order

1. `01_OBJECTIVES_AND_BOUNDARIES.md` — what the project is for and what it is not.
2. `12_DECISIONS_AND_OPEN_QUESTIONS.md` — the five engineering questions, each **RECOMMENDED, awaiting ratification**. Nothing is ratified.
3. `03_EVIDENCE_AND_RESEARCH_REGISTER.md` — which research claims were verified, which were not, and which were contradicted.
4. `15_RISKS_AND_NON_GOALS.md` — the explicit boundaries.
5. `SETTLEIQ-MASTER-SPEC.md` — the requirement source.
6. The rest, in numeric order.

## Standing rules for contributors and agents

* **A claim is not a fact until it appears in the verification log with a primary source.** Mark it `NOT VERIFIED` otherwise. Do not fill gaps with plausible text.
* **Intent and implementation are never presented in the same register.** A specification states intent; a test result states implementation.
* **Digests and hashes are computed by the system and verified on read.** A hand-written or patterned digest is treated as fabricated evidence.
* **No monetary value is ever a binary float.**
* **No ambient clock, sequence, or random value participates in any output or digest preimage.**
* **No requirement is cited from another repository as authority.** SettleIQ is independent (master REQ-IND-01…04).
* **Do not add a competitive-claim, pricing, market-gap, or go-to-market document.** Those frames are prohibited by SETTLEIQ-REQ-001.
* **Report the absence of a capability rather than describing it.**

## Authorization status

The five engineering questions are **OWNER-PROPOSED, awaiting explicit ratification** (`16` Part A). Ratification order matters: **Q5 (target role) before Q2 (language architecture)**, because Q2's conditional C++17 gate depends on it.

The OWNER has stated a baseline — Stripe-only · Python core · PostgreSQL · five views · financial systems/ledgering. **This is recorded as a proposal, not a ratification**, because approval was not explicitly given.

Eight outstanding engineering questions are **resolved by recommendation** in `16` Part B. Five genuinely open items remain (OQ-09…OQ-12 plus two OWNER judgements).

**No implementation is authorized. No code exists. Nothing is built. No test has run. No benchmark has been measured.**
