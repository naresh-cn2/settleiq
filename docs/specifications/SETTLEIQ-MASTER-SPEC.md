# SETTLEIQ MASTER SPECIFICATION

**Document ID:** SETTLEIQ-MASTER-SPEC-001
**Title:** SettleIQ Master Specification — Payment Settlement Reconciliation & Discrepancy Investigation Engine
**Version:** 1.1.0
**Status:** PROPOSED — specification only; no implementation claimed
**Domain:** Master
**Governing document:** None. This document is the sole authority for SettleIQ's scope and requirements.
**Date:** 2026-10-27, revised 2026-10-28 (v1.1.0 — project independence correction)
**Canonical path:** `docs/specifications/SETTLEIQ-MASTER-SPEC.md`
**Owner:** Bukya Naresh (CN2)

---

## Document Control

### Purpose

This document defines the governing frame, scope, requirements, and acceptance conditions for SettleIQ. It is the single source of requirements against which all subordinate SettleIQ documents (architecture, data model, engine, API, test, deployment) are authored and classified.

This is a **specification-only document**. It describes intended scope and requirements, not implemented software. Nothing in this document constitutes an implementation, a tested component, or evidence that SettleIQ satisfies its objectives.

### Project Independence — OWNER-DEFINED

**SETTLEIQ-REQ-IND-01 (OWNER-DEFINED):** SettleIQ is an independent project. It owns its own product definition, architecture, technical decisions, specifications, implementation, tests, benchmarks, and engineering documentation.

**SETTLEIQ-REQ-IND-02 (OWNER-DEFINED):** SettleIQ shall not inherit architecture, requirements, roadmaps, or implementation tasks from PROJECT-TOP1, STRATA-ENGINE, Forex-platform, crypto-platform, or any other repository. Those projects are separately owned and separately governed. SettleIQ's presence on a personal roadmap is progress tracking only and confers no engineering authority.

**SETTLEIQ-REQ-IND-03 (OWNER-DEFINED):** SettleIQ shall not import implementation from another repository as a shortcut. Prior work may be consulted as reference material, but every line SettleIQ runs must be SettleIQ's own, with its own tests and its own evidence. Where a pattern is borrowed, the justification must be a requirements-based technical reason recorded in `12_DECISIONS_AND_OPEN_QUESTIONS.md`, never "it exists elsewhere."

**SETTLEIQ-REQ-IND-04 (OWNER-DEFINED):** No external governance document shall be cited as authority for a SettleIQ requirement. Principles adopted from elsewhere must be restated here as SettleIQ's own requirements, owned and testable within this repository.

### Purpose Classification — OWNER-DEFINED

SettleIQ exists to produce **verifiable employment evidence**. Its audience is a hiring manager evaluating candidates for financial-systems, ledgering, or backend engineering roles. This frame was selected by the OWNER on 2026-10-27 after research established that the alternative frame — commercial product differentiation — was not supportable on available evidence. An employment-first frame does not cap technical ambition: SettleIQ may still lead to client work or a commercial product later, and no requirement here prohibits that. What is prohibited is making product decisions on an unproven market gap.

**SETTLEIQ-REQ-000 (OWNER-DEFINED):** SettleIQ shall not be positioned, marketed, documented, or described as a commercially competitive product, a superior alternative to named competitors, or a fill for a proven market gap. Every artifact this project produces must be defensible as engineering evidence rather than as commercial positioning.

### Requirement Classification Convention

Requirements are classified as:

* **OWNER-DEFINED** — established by the OWNER. These may only change by explicit OWNER decision.
* **PROPOSED** — recommended by this specification. Not binding until ratified by the OWNER.
* **IMPLEMENTED / VALIDATED** — reserved for statements backed by executed tests with recorded output. **No requirement in this document carries these states.** Nothing is implemented.

### Relationship to Verified Research

This specification rests on a primary-source verification log (`docs/research/02_verification_log.md`) in which claims carried forward from subordinate research agents were re-checked against original sources. 16 claims were verified verbatim, several were found unverified, and one prior conclusion was contradicted by its own source. The classification states below reflect that log, not the original agent reports. Research is preserved as evidence; it is **not** a source of engineering requirements.

---

## 1. Governing Frame

### 1.1 What SettleIQ Is

A payment settlement reconciliation and discrepancy investigation engine that ingests processor transaction data and bank settlement data, decomposes payout-level records into charge-level components using exact-decimal arithmetic, reconciles across both sides, classifies unmatched differences into typed discrepancies with auditable provenance, and reports its own automation performance using an explicitly defined measurement methodology.

### 1.2 Why This Frame and Not a Commercial One

Research completed 2026-10-27 (primary-source verified) established the following, each traceable to a cited source:

| Finding | Evidence class |
|---|---|
| Processor vendors document that payout decomposition is the merchant's responsibility (Stripe manual/instant payouts; Braintree states its own summary tools "should not be used for reconciliation purposes"; Adyen pays net-of-costs requiring gross-to-net bridging) | A |
| Auditability, explainability, human-approval gating, and confidence scoring are **documented capabilities** of funded competitors — Numeric, Ramp Stack (launched 2026-06-03), Xero JAX | A |
| Published per-seat pricing is standard in the spend-management tier (Ramp $0/$15; Brex $0/$12; BILL $49/$65/$89 per user/month) | A/B |
| Xero will not expose unreconciled bank statement lines via public API for **regulatory** reasons (consumer-data-rights treatment of raw banking data) | A |
| No vendor publishes a measurement methodology for its headline auto-match rate; Numeric's own blog advises buyers to weigh "controls, explainability, and data quality over headline match-rate claims" | A |

The first and last rows describe a real engineering problem and a real missing practice. The middle rows establish that the differentiators this project might otherwise have claimed are **occupied**. SettleIQ therefore competes on nothing and asserts no market position. It demonstrates capability.

**Verification status of this table — important, and deliberately unflattering:** the rows in this table were established during the M1 research pass with cited source URLs, but they were **not re-fetched and re-confirmed during the M2b primary-source verification pass**. They are therefore *research-pass verified*, not *independently re-verified here*. The claims that WERE re-fetched and confirmed verbatim are recorded in `docs/research/02_verification_log.md` (§1, V1–V26) and in `03_EVIDENCE_AND_RESEARCH_REGISTER.md`. Three claims carried in the original research were checked and found absent, and one prior conclusion was contradicted by its own source; those are recorded as NOT VERIFIED and CONTRADICTED respectively. Where this table and the verification log differ, **the verification log governs**.

### 1.3 What SettleIQ Is Not

**SETTLEIQ-REQ-001 (OWNER-DEFINED):** The following non-claims are binding. Any artifact that violates one is defective and must be corrected before it counts as deliverable evidence.

1. Not a claim that any named competitor lacks auditability, explainability, or charge-level capability. Verified sources show these capabilities are documented by Numeric, Ramp, and Xero.
2. Not a claim of a market gap, market size, or underserved segment. The research that would support such a claim was not obtained.
3. Not a claim of product-market fit, commercial viability, or willingness to pay. No buyer contact exists.
4. Not a claim of superior matching accuracy against any named product.
5. Not a competitive analysis, a pricing recommendation, or a go-to-market plan.
6. Not connected to live money movement, live customer financial data, or any real payment instrument.

---

## 2. Requirements

### 2.1 Frame and Purpose — OWNER-DEFINED

**SETTLEIQ-REQ-002:** SettleIQ shall be buildable and demonstrable entirely on **synthetic, generator-produced data**. No real processor credentials, no real bank feeds, no real customer data.

**SETTLEIQ-REQ-003:** Every deliverable shall be verifiable by a third party with no access to the author. `clone → install → one command → tests, benchmarks, and a worked discrepancy investigation execute and produce recorded output`.

**SETTLEIQ-REQ-004:** SettleIQ shall distinguish, in every artifact, **intended capability from implemented capability**. A specification states intent; a test result states implementation. The two shall never be presented in the same register.

### 2.2 Reconciliation Correctness — OWNER-DEFINED

**SETTLEIQ-REQ-005:** All monetary amounts shall use `decimal.Decimal` with explicit context and explicit rounding mode. Floating-point arithmetic shall not be used for any amount, fee, balance, or rounding computation. Any use of binary floating point on monetary values is a defect.

**SETTLEIQ-REQ-006:** Reconciliation shall operate at **charge level, not payout level**. A payout is reconciled by decomposing it into constituent charges, fees, refunds, and adjustments and matching each constituent, not by comparing payout totals.

**SETTLEIQ-REQ-007:** Every match decision shall carry a **provenance record**: which fields supported the match, which rule or determinator produced it, the confidence classification, and the determinism guarantee (deterministic / ambiguous / human-required).

**SETTLEIQ-REQ-008:** Unmatched differences shall be classified into **named typed discrepancies**, never into a generic "mismatch". The taxonomy shall be explicit, exhaustive, and tested.

**SETTLEIQ-REQ-009:** The engine shall be **fail-closed**. Where evidence is insufficient to determine a match, the engine reports an unresolvable break. It shall never guess, approximate, or silently absorb a difference.

### 2.3 Audit Integrity — OWNER-DEFINED

**SETTLEIQ-REQ-010:** The discrepancy record store shall be append-only.

**SETTLEIQ-REQ-011:** Audit journal entries shall be **hash-chained**, where each entry's digest is computed over the previous entry's digest and the current entry's canonical serialization. Digests shall be **computed by the system and verified on read**. A hand-written, patterned, or placeholder digest is a critical defect and is treated as fabricated evidence.

**SETTLEIQ-REQ-012:** Given identical inputs and identical rule version, the engine shall produce byte-identical outputs. Determinism shall be tested, not asserted.

### 2.4 Measurement Practice — OWNER-DEFINED (the centerpiece)

**SETTLEIQ-REQ-013:** SettleIQ shall publish its own auto-match rate **with an explicit, documented measurement methodology**: the denominator definition (what counts as an eligible record), the population (which records were in scope), the observation window, and the treatment of AI-assisted or human-confirmed matches.

**Determinism interaction (OWNER-DEFINED, resolving a conflict):** the observation window shall be a **declared input** to the run, recorded in the run's input digest and rule version — never a wall-clock range sampled from ambient time. A rate computed over an ambient time window is not reproducible and would break REQ-012. The window is therefore *specified by the operator, hashed with the inputs, and reproducible*, and the methodology states that explicitly. Any report that shows a window without showing how it was declared is defective.

**SETTLEIQ-REQ-014:** The rate shall be computed and reported by the system from recorded instrumented counts. It shall not be stated in prose anywhere in the repository.

**Rationale (PROPOSED, evidence-backed):** No competitor examined publishes such a methodology, and Numeric's own documentation advises buyers to weigh controls and explainability "over headline match-rate claims" (Class A, verified). SettleIQ does not claim competitors lack this practice — it **demonstrates the practice on itself**, on data a third party can inspect. This converts the verified research finding into a demonstrable property without making any competitive assertion.

### 2.5 Quality and Finish — OWNER-DEFINED

**SETTLEIQ-REQ-015:** SettleIQ shall not be a disposable slice. Every component shall be modular, tested, documented, and runnable in Docker, with a documented evolutionary path. This is stated as SettleIQ's own requirement, owned and enforced within this repository.

**SETTLEIQ-REQ-016:** No completion claim shall be made without executed test output. A component described in prose as working, without a recorded passing test, is a defect. "Checkbox theater" is a named SettleIQ risk.

---

## 3. Component Architecture — PROPOSED

Not binding. Subject to ratification and to the architecture specification.

| Component | Responsibility | Classification |
|---|---|---|
| Settlement Data Model | Canonical typed representations of charge, payout, fee, refund, adjustment, bank deposit, and discrepancy; Decimal money | PROPOSED |
| Source Adapters | Per-processor normalization into the canonical model behind a stable interface; Stripe-shaped and Adyen-shaped generators initially | PROPOSED |
| Settlement Decomposer | Payout → constituent decomposition; gross-to-net bridging; FX and fee attribution | PROPOSED |
| Matching Engine | Deterministic rule-based matching across charge/payout/bank; confidence classification; ambiguous-case routing | PROPOSED |
| Discrepancy Engine | Typed break classification, ageing, root-cause attribution, resolution workflow | PROPOSED |
| Audit Journal | Append-only hash-chained record store with computed-and-verified digests | PROPOSED |
| Metrics & Reporting | Instrumented counts, methodology-defined rate computation, reproducible reports | PROPOSED |
| API | REST + OpenAPI over the above; read-only references for investigation | PROPOSED |

**Reuse posture (OWNER-DEFINED, see SETTLEIQ-REQ-IND-03):** Cases where patterns from other software might inform SettleIQ are illustrative only and carry no engineering authority. Every component is SettleIQ's own implementation with its own tests. The append-only hash-chained store, the typed discrepancy taxonomy, and the exact-decimal arithmetic core are all built here, tested here, and evidenced here. No test coverage, benchmark result, or correctness property from another repository is ever cited as SettleIQ's evidence.

---

## 4. The Demonstration Contract

The artifact's value is that a stranger can verify it. The contract, in order:

1. `docker compose up` starts the engine with seeded synthetic data.
2. A single command runs the full test suite (unit, property-based Decimal invariants, determinism, fault injection) and emits recorded output.
3. A worked discrepancy investigation runs end to end against a dataset with **known, injected defects**: a phantom charge, an amount break, a fee misattribution, a mid-payout refund, and an FX rounding carryover. The engine must classify each correctly, and the expected classification is asserted, not narrated.
4. The metrics report computes the auto-match rate with its stated denominator from instrumented counts, and the same figure reproduces across runs.
5. **Conditional, not mandatory:** if and only if a compute-bound workload has been identified and measured, a benchmark compares a Python baseline against a C++17 implementation and reports ns/op, allocations, correctness equivalence, and the honest limits of the comparison. If no such workload exists, no benchmark is produced and none is claimed. The four gating conditions are recorded in `12_DECISIONS_AND_OPEN_QUESTIONS.md` §Q2.

**SETTLEIQ-REQ-017 (OWNER-DEFINED):** The demonstration shall fail loudly. A test that cannot run, a benchmark that cannot reproduce, or an investigation that cannot classify an injected defect is reported as such. Documentation shall never describe capability that the demonstration does not execute.

---

## 5. Milestones — evidence-based acceptance

Each milestone is closed only by executed output recorded in the repository. No milestone is closed by prose.

| # | Milestone | Acceptance evidence | Target role evidence |
|---|---|---|---|
| M1 | Canonical data model + Decimal invariants, property-tested | Property test suite output; invariant violations fail the build | Ledgering, Quant Dev |
| M2 | Source adapters + **Stripe-shaped** generators with injected defects (Stripe-only per Q1; the frozen `SourceAdapter` interface is the deliverable, not the adapter count) | Golden-file tests; defect generator tests | Data Infra, Backend |
| M3 | Settlement decomposer + charge-level reconciliation | Worked decomposition test with exact expected totals | Financial Systems |
| M4 | Matching engine + typed discrepancy taxonomy | Injected-defect classification suite, all classes asserted | Financial Systems, Backend |
| M5 | Append-only hash-chained audit journal, digests computed and verified | Tamper-injection test proves verification detects modification; determinism test proves byte-identical output | Backend, Financial Systems |
| M6 | Metrics with published methodology | Reproducible report across runs; denominator documented in code | All |
| M7 | REST + OpenAPI + investigation dashboard | Contract tests; running UI against live engine | Backend |
| M8 | **Conditional.** Python-vs-C++17 benchmark, only if the four Q2 gating conditions are satisfied | Benchmark output; stated caveats; correctness-equivalence proof. **If the conditions are not satisfied, this milestone is deleted, not deferred, and its absence is stated rather than hidden** | Quant Dev, HFT |
| M9 | Docker + single-command reproduction | Clean-clone reproduction by a third party | All |

**Explicitly excluded from milestones:** buyer interviews, pricing experiments, GTM artifacts, and any competitive-claim document. These belong to a different frame and that frame was closed on 2026-10-27.

---

## 6. Risk Register

| ID | Risk | Severity | Control |
|---|---|---|---|
| SR-01 | Capability claimed in prose but not executed in tests — the exact defect found across three prior repositories | Critical | REQ-004; milestone closure requires recorded output |
| SR-02 | Computed hashes replaced by fabricated / patterned values | Critical | REQ-011; tamper-injection test must detect modification |
| SR-03 | Float money entering via a dependency or JSON boundary | High | Property tests on Decimal; CI gate rejects float on monetary paths |
| SR-04 | Scope expanding back into commercial positioning | High | REQ-001 binding; this document is the guard |
| SR-05 | Abandonment mid-build: a large unfinished codebase with no demonstrable evidence | High | Milestones are small and independently closing; each produces recordable evidence before the next begins |
| SR-06 | Multi-source research restated as fact without verification | Medium | Verification log discipline (`docs/research/`) applies to all claims |
| SR-07 | Xero-style regulatory constraint blocks a planned integration | Medium | Bank/processor-direct connections; GL-mediated integration is not assumed available |

---

## 7. External Tracking and Independence Note

SettleIQ may be listed on a personal roadmap for progress tracking. That relationship is administrative and one-directional:

* The roadmap records that SettleIQ exists and roughly what phase it is in.
* The roadmap confers no engineering authority over SettleIQ.
* This repository's specifications are the sole authority for SettleIQ's scope, architecture, and requirements.
* Progress reported externally must match the repository's own milestone state. If the repository says nothing is implemented, external reporting must say the same.

Reporting SettleIQ against an external goal is permitted and useful. Subordinating SettleIQ's engineering to that goal is prohibited by SETTLEIQ-REQ-IND-01 and IND-02.

---

## 8. Subordinate Document Hierarchy — specification system of record

Each subordinate document is authoritative in its own domain and traces its requirements back to this specification. **Nothing below is implemented.**

| # | Document | Domain of authority | Master requirements it elaborates |
|---|---|---|---|
| 01 | `01_OBJECTIVES_AND_BOUNDARIES.md` | Objectives, scope boundaries, independence, success criteria | REQ-IND-01…04, REQ-000, REQ-001 |
| 02 | `02_PROBLEM_AND_USE_CASES.md` | Problem statement, actors, use cases, in-scope / out-of-scope | REQ-002, REQ-006 |
| 03 | `03_EVIDENCE_AND_RESEARCH_REGISTER.md` | Research record, evidence classes, verified vs. unverified claims | REQ-001, verification discipline |
| 04 | `04_REQUIREMENTS_AND_NON_GOALS.md` | Full requirement register, priorities, non-goals | REQ-000…016 |
| 05 | `05_ARCHITECTURE.md` | Components, boundaries, interfaces, deployment view | REQ-004, REQ-015 |
| 06 | `06_DATA_MODEL_AND_PERSISTENCE.md` | Canonical types, Decimal rules, schema, migrations, transaction boundaries | REQ-005, REQ-006 |
| 07 | `07_RECONCILIATION_ENGINE_SPEC.md` | Decomposition, matching rules, determinism, confidence classes, fail-closed behaviour | REQ-005…009, REQ-012 |
| 08 | `08_DISCREPANCY_AND_AUDIT_SPEC.md` | Typed taxonomy, ageing, provenance, hash-chained journal, tamper detection | REQ-007…011 |
| 09 | `09_API_AND_INTEGRATION_SPEC.md` | REST/OpenAPI contracts, source-adapter interfaces | REQ-003 |
| 10 | `10_DASHBOARD_SPEC.md` | Minimum complete investigation interface, functional requirements | REQ-003 |
| 11 | `11_TESTING_AND_PERFORMANCE_SPEC.md` | Test taxonomy, property tests, correctness gates, benchmark methodology | REQ-004, REQ-012, REQ-016 |
| 12 | `12_DECISIONS_AND_OPEN_QUESTIONS.md` | The five engineering decisions with recommendations, ADRs, unresolved items | — |
| 13 | `13_ROADMAP_AND_ACCEPTANCE.md` | Milestones, dependency graph, acceptance gates, release criteria | REQ-015, REQ-016 |
| 14 | `14_EMPLOYMENT_EVIDENCE.md` | Skills-to-artifact mapping, interview readiness, role emphasis | REQ-000 |
| 15 | `15_RISKS_AND_NON_GOALS.md` | Risk register, explicit non-goals | REQ-001, REQ-016 |
| 16 | `16_DECISION_REGISTER_AND_RESOLUTIONS.md` | Architecture decision baseline (Part A) and resolution of all outstanding engineering questions (Part B) | REQ-001, REQ-005, REQ-009, REQ-012 |
| 17 | `17_TRACEABILITY_MATRIX_AND_CONSISTENCY.md` | Requirements-to-verification traceability; eight-class consistency findings | All |
| 18 | `18_M1_IMPLEMENTATION_PLAN.md` | M1 file-level scope and acceptance criteria. **A plan, not an authorization** | REQ-003, 005, 006, 009, 012, 016 |

This specification does not authorize implementation. It authorizes the next specification step, contingent on OWNER ratification of `12_DECISIONS_AND_OPEN_QUESTIONS.md`.

---

## 9. Open Questions — resolved by recommendation in `12_DECISIONS_AND_OPEN_QUESTIONS.md`

Five engineering questions require OWNER ratification before implementation. Evidence-based recommendations are recorded in `12_DECISIONS_AND_OPEN_QUESTIONS.md`, with rationale, alternatives considered, and the cost of each choice. **They are recommendations, not approvals.** No question is marked resolved until the OWNER ratifies it.

| # | Question | Recommendation status |
|---|---|---|
| Q1 | Processor scope: Stripe-only vs. Stripe + Adyen | RECOMMENDED, awaiting ratification |
| Q2 | Language architecture: Python core plus optional C++17 benchmark | RECOMMENDED, awaiting ratification |
| Q3 | Persistence: PostgreSQL vs. alternatives, and reproducibility | RECOMMENDED, awaiting ratification |
| Q4 | Dashboard scope: minimum complete investigation interface | RECOMMENDED, awaiting ratification |
| Q5 | Target employment role and skill emphasis | RECOMMENDED, awaiting ratification |

No implementation shall begin until these are ratified.
