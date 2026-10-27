# SETTLEIQ MASTER SPECIFICATION

**Document ID:** SETTLEIQ-MASTER-SPEC-001
**Title:** SettleIQ Master Specification — Payment Settlement Reconciliation & Discrepancy Investigation Engine
**Version:** 1.0.0
**Status:** PROPOSED — specification only; no implementation claimed
**Domain:** Master
**Governing document:** PROJECT TOP 1 Master Blueprint; Pillar 2 Manager Charter
**Date:** 2026-10-27 (Project Day 074, Week 11)
**Canonical path:** `docs/specifications/SETTLEIQ-MASTER-SPEC.md`
**Owner:** Bukya Naresh (CN2)

---

## Document Control

### Purpose

This document defines the governing frame, scope, requirements, and acceptance conditions for SettleIQ. It is the single source of requirements against which all subordinate SettleIQ documents (architecture, data model, engine, API, test, deployment) are authored and classified.

This is a **specification-only document**. It describes intended scope and requirements, not implemented software. Nothing in this document constitutes an implementation, a tested component, or evidence that SettleIQ satisfies its objectives.

### Purpose Classification — OWNER-DEFINED

SettleIQ exists to produce **verifiable employment evidence**. Its customer is a hiring manager evaluating candidates for financial-systems, ledgering, or backend engineering roles. This frame was selected by the OWNER on 2026-10-27 after research established that the alternative frame — commercial product differentiation — was not supportable on available evidence.

**SETTLEIQ-REQ-000 (OWNER-DEFINED):** SettleIQ shall not be positioned, marketed, documented, or described as a commercially competitive product, a superior alternative to named competitors, or a fill for a proven market gap. Every artifact this project produces must be defensible as engineering evidence rather than as commercial positioning.

### Requirement Classification Convention

Requirements are classified as:

* **OWNER-DEFINED** — established by the OWNER or by governing PROJECT TOP 1 law. These may only change by explicit OWNER decision.
* **PROPOSED** — recommended by this specification. Not binding until ratified by the OWNER.
* **IMPLEMENTED / VALIDATED** — reserved for statements backed by executed tests with recorded output. **No requirement in this document carries these states.** Nothing is implemented.

### Relationship to Verified Research

This specification rests on a primary-source verification log (`docs/research/02_verification_log.md`) in which claims carried forward from subordinate research agents were re-checked against original sources. 16 claims were verified verbatim, several were found unverified, and one prior conclusion was contradicted by its own source. The classification states below reflect that log, not the original agent reports.

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

**SETTLEIQ-REQ-013:** SettleIQ shall publish its own auto-match rate **with an explicit, documented measurement methodology**: the denominator definition (what counts as an eligible record), the population (which records were in scope), the time window, and the treatment of AI-assisted or human-confirmed matches.

**SETTLEIQ-REQ-014:** The rate shall be computed and reported by the system from recorded instrumented counts. It shall not be stated in prose anywhere in the repository.

**Rationale (PROPOSED, evidence-backed):** No competitor examined publishes such a methodology, and Numeric's own documentation advises buyers to weigh controls and explainability "over headline match-rate claims" (Class A, verified). SettleIQ does not claim competitors lack this practice — it **demonstrates the practice on itself**, on data a third party can inspect. This converts the verified research finding into a demonstrable property without making any competitive assertion.

### 2.5 Quality and Finish — OWNER-DEFINED (PROJECT TOP 1 law)

**SETTLEIQ-REQ-015:** Per the Scalability & Future-Proofing Law, SettleIQ shall not be a disposable slice. Every component shall be modular, tested, documented, and runnable in Docker, with a documented evolutionary path.

**SETTLEIQ-REQ-016:** Per RSK-04, no completion claim shall be made without executed test output. "Checkbox theater" is a named project risk; this project is a place it could recur.

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

**Reuse posture (PROPOSED, evidence-backed):** The typed-discrepancy pattern, Decimal money discipline, and provenance-sidecar pattern already exist and are tested in `Forex-platform`. The append-only journal, checkpointed recovery, and RBAC patterns exist in `crypto-platform`. Reuse those patterns through re-implementation under SettleIQ's own contracts — do not vendor them across repository boundaries, and do not claim their test coverage as SettleIQ's own.

---

## 4. The Demonstration Contract

The artifact's value is that a stranger can verify it. The contract, in order:

1. `docker compose up` starts the engine with seeded synthetic data.
2. A single command runs the full test suite (unit, property-based Decimal invariants, determinism, fault injection) and emits recorded output.
3. A worked discrepancy investigation runs end to end against a dataset with **known, injected defects**: a phantom charge, an amount break, a fee misattribution, a mid-payout refund, and an FX rounding carryover. The engine must classify each correctly, and the expected classification is asserted, not narrated.
4. The metrics report computes the auto-match rate with its stated denominator from instrumented counts, and the same figure reproduces across runs.
5. A benchmark runs the hot path in Python and C++17 and reports ns/op, allocations, and honest limits of the comparison.

**SETTLEIQ-REQ-017 (OWNER-DEFINED):** The demonstration shall fail loudly. A test that cannot run, a benchmark that cannot reproduce, or an investigation that cannot classify an injected defect is reported as such. Documentation shall never describe capability that the demonstration does not execute.

---

## 5. Milestones — evidence-based acceptance

Each milestone is closed only by executed output recorded in the repository. No milestone is closed by prose.

| # | Milestone | Acceptance evidence | Target role evidence |
|---|---|---|---|
| M1 | Canonical data model + Decimal invariants, property-tested | Property test suite output; invariant violations fail the build | Ledgering, Quant Dev |
| M2 | Source adapters + Stripe/Adyen-shaped generators with injected defects | Golden-file tests; defect generator tests | Data Infra, Backend |
| M3 | Settlement decomposer + charge-level reconciliation | Worked decomposition test with exact expected totals | Financial Systems |
| M4 | Matching engine + typed discrepancy taxonomy | Injected-defect classification suite, all classes asserted | Financial Systems, Backend |
| M5 | Append-only hash-chained audit journal, digests computed and verified | Tamper-injection test proves verification detects modification; determinism test proves byte-identical output | Backend, Financial Systems |
| M6 | Metrics with published methodology | Reproducible report across runs; denominator documented in code | All |
| M7 | REST + OpenAPI + investigation dashboard | Contract tests; running UI against live engine | Backend, AI-eng |
| M8 | Python-vs-C++17 benchmark with honest limits | Benchmark output; stated comparison caveats | Quant Dev, HFT |
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
| SR-05 | Abandonment mid-build (PROJECT TOP 1 Anti-Abandonment Invariant) | High | Milestones are small and independently closing; each produces evidence |
| SR-06 | Multi-source research restated as fact without verification | Medium | Verification log discipline (`docs/research/`) applies to all claims |
| SR-07 | Xero-style regulatory constraint blocks a planned integration | Medium | Bank/processor-direct connections; GL-mediated integration is not assumed available |

---

## 7. Alignment Register — PROJECT TOP 1

| Governing item | SettleIQ's relationship |
|---|---|
| Pillar 2, Goal 2 — Build & Package Sellable Solution Vertical Slice | SettleIQ is the vertical slice. **Commercial lane unproven**; do not report it as satisfying the revenue lane until buyer evidence exists. |
| Pillar 2, Goal 4 — High-Trajectory Career Pipeline & Systems Engineer CV / Outcome 4 | Primary satisfied lane. Milestones M1–M9 map directly onto target-role evidence. |
| Pillar 2, Outcome 3 — Sellable Problem-Solution Product Asset & Pre-Build Dossier | Partial. The pre-build dossier is satisfied by this specification plus the research record. The "sellable" qualifier is **not** evidenced. |
| Unified Product Asset Law (Single-Asset Multi-Channel Rule) | Satisfied on the career-proof, portfolio, and IP-compounding lanes. **Not** satisfied on direct-revenue or client-services lanes on current evidence. Stating otherwise would violate RSK-04. |
| Scalability & Future-Proofing Law | REQ-015. |
| Zero Live Trading Capital Law | Not applicable; SettleIQ moves no capital. |
| RSK-04 — Checkbox theater | SR-01, SR-02. |

---

## 8. Subordinate Documents — required, not yet authored

| Document | Purpose | Prerequisite |
|---|---|---|
| `03_DATA_MODEL_AND_CONTRACTS.md` | Canonical types, Decimal rules, settlement schema, data contracts | This spec ratified |
| `04_RECONCILIATION_ENGINE.md` | Decomposition, matching rules, determinism, confidence classes | Ratified |
| `05_DISCREPANCY_INVESTIGATION_SPEC.md` | Typed taxonomy, ageing, root-cause, resolution workflow | Ratified |
| `06_AUDIT_AND_INTEGRITY_SPEC.md` | Hash-chaining, digest computation/verification, tamper tests | Ratified |
| `07_API_AND_INTEGRATION_SPEC.md` | REST/OpenAPI, adapter contracts | Ratified |
| `08_TESTING_AND_VALIDATION_SPEC.md` | Property tests, golden files, fault injection, metric methodology | Ratified |
| `09_ACCEPTANCE_CRITERIA.md` | Milestone closure conditions | Ratified |

This specification does not authorize implementation. It authorizes the next specification step, contingent on OWNER ratification.

---

## 9. Open Questions for the OWNER

1. **Primary processor shape.** Stripe-shaped is the best-documented (verified limitations available). Adyen-shaped adds net-of-costs gross-to-net bridging. One or both for M2?
2. **Language split.** Python core with a C++17 hot-path benchmark (M8) is the proposal. Confirm.
3. **Persistence.** Postgres is proposed for the ledger/audit store. Confirm against the single-command reproduction requirement.
4. **Dashboard scope.** Minimum viable: discrepancy queue + investigation detail + metrics. Confirm.
5. **Target-role emphasis.** If one role is to be prioritised (ledgering vs. backend vs. quant dev), milestone ordering should follow it. Currently M1–M9 is balanced.

No implementation shall begin until these are answered.
