# 05 — System Architecture

**Document ID:** SETTLEIQ-ARCH-001
**Title:** SettleIQ System Architecture and Component Boundaries
**Version:** 1.0.0
**Status:** PROPOSED — specification only; no implementation claimed
**Domain:** ARCH
**Governing document:** `SETTLEIQ-MASTER-SPEC.md` (SETTLEIQ-MASTER-SPEC-001)
**Date:** 2026-10-28
**Canonical path:** `docs/specifications/05_ARCHITECTURE.md`
**Owner:** Bukya Naresh (CN2)
**Traces to:** SETTLEIQ-MASTER-SPEC-001 §3, §4; requirements R-DAT, R-REC, R-DET

---

## Document Control

This document translates the master specification into component responsibilities, boundaries, and interfaces.

**This is a specification-only document.** It describes intended architecture, not implemented software. No component described here exists. Where a design choice is stated, it is classified PROPOSED unless it restates a master OWNER-DEFINED requirement.

**SettleIQ-ARCH-R01 (OWNER-DEFINED):** This specification must not revoke, weaken, or silently alter any OWNER-DEFINED requirement in the master specification or in `04_REQUIREMENTS_AND_NON_GOALS.md`. Conflicts must be recorded explicitly, not resolved by omission.

---

## 1. Architectural Objectives

The architecture exists to serve six demonstrable properties, in this order of precedence:

1. **Correctness of money arithmetic** — exact, explicit, testable.
2. **Reproducibility** — identical inputs produce identical outputs, verifiably.
3. **Traceability** — every decision has a retrievable evidence trail.
4. **Integrity** — the audit record detects any modification.
5. **Measurability** — the system reports its own performance with a stated methodology.
6. **Operability** — one command reproduces the whole thing.

**Anything that trades 1 against 3, 4, or 5 is rejected.** This precedence is the architecture's primary constraint and the reason several otherwise-attractive designs are excluded.

---

## 2. Component Inventory

| Component | Responsibility | Classification |
|---|---|---|
| Settlement Data Model | Canonical typed representations: Charge, Fee, Refund, Adjustment, Payout, SettlementBatch, BankDeposit, ReconciliationRun, MatchDecision, Discrepancy, AuditJournalEntry. Decimal money, explicit currency | OWNER-DEFINED (R-FIN) |
| Source Adapters | Per-processor normalization into the canonical model behind a frozen interface. Stripe-shaped generator first; Adyen additive later | PROPOSED (Q1) |
| Settlement Decomposer | Payout → constituent decomposition; gross-to-net bridging; fee and FX attribution | PROPOSED |
| Matching Engine | Deterministic rule-based matching across charge/payout/deposit; confidence classification; ambiguous-case routing | PROPOSED |
| Discrepancy Engine | Typed break classification, ageing, severity, root-cause attribution, resolution workflow | PROPOSED |
| Audit Journal | Append-only hash-chained record store; digests computed by the system and verified on read | OWNER-DEFINED (R-AUD) |
| Metrics and Reporting | Instrumented counts; methodology-defined rate computation; reproducible reports | OWNER-DEFINED (R-MEA) |
| API Surface | REST + OpenAPI over the above; idempotent mutations | PROPOSED |
| Dashboard | Five functional views over the API | PROPOSED (Q4) |
| Fixture Generator | Deterministic synthetic processor and bank data with injectable known defects | OWNER-DEFINED (R-DAT-02) |

---

## 3. Component Boundaries and Rules

### 3.1 One-Way Data Flow

```
FixtureGenerator → SourceAdapter(s) → CanonicalModel
                                          ↓
                                   SettlementDecomposer
                                          ↓
                                    MatchingEngine
                                   ↙            ↘
                    DiscrepancyEngine        MatchDecision
                            ↘            ↙
                          AuditJournal (append-only, hash-chained)
                                   ↓
                          MetricsAndReporting
                                   ↓
                    API Surface ← → Dashboard
```

**SettleIQ-ARCH-R02 (OWNER-DEFINED):** Data flows in one direction through the pipeline. No component writes upstream. In particular, the matching engine never mutates a canonical record; it emits decisions. The discrepancy engine never mutates a decision; it references it.

**SettleIQ-ARCH-R03 (OWNER-DEFINED):** The canonical model is the only in-memory representation that crosses a component boundary. No component accepts or returns a processor-specific shape.

### 3.2 The Source Adapter Interface

The single most consequential boundary in the architecture.

**SettleIQ-ARCH-R04 (PROPOSED, Q1):** The `SourceAdapter` interface is defined, documented, and frozen at milestone M1, **before any adapter is implemented.** This is what makes Stripe-only a safe first scope: the interface is the decision, the adapter count is not.

The interface must:
* accept a raw source payload and a source version, and return canonical model objects;
* carry a declared `source_version` and `schema_version` into every produced object, so a run's identity includes what produced it;
* fail closed — a malformed or partially-understood payload produces a typed ingestion error, never a partially-canonicalized record;
* be exhaustively testable against a golden-file fixture without any network access.

**SettleIQ-ARCH-R05 (OWNER-DEFINED):** A processor-specific concept may not leak past its adapter. If Adyen's "payout reference" and Stripe's "balance transaction" both mean "the money moved on this date," the canonical model expresses that one concept once, and each adapter maps to it. Conditional processor-specific shape in the core model is a defect.

### 3.3 The Decomposer

**SettleIQ-ARCH-R06 (OWNER-DEFINED):** Decomposition is the core operation. A payout is decomposed into its constituent charges, fees, refunds, and adjustments, and the decomposition must be **complete and reconciling**: the sum of constituents equals the payout amount exactly, in Decimal, with no residual silently discarded.

**SettleIQ-ARCH-R07 (PROPOSED, resolves OQ-02):** When fees do not divide exactly across charges, a residual exists. The residual is **explicit** — it is modelled, named, attributed by a declared deterministic rule, and never rounded away in silence. The declared rule is part of the rule version and participates in the run identity. The rule's own correctness is tested against hand-computed cases.

### 3.4 The Matching Engine

**SettleIQ-ARCH-R08 (OWNER-DEFINED):** Matching is deterministic and rule-based. Rules are versioned. The rule version is part of run identity.

**SettleIQ-ARCH-R09 (OWNER-DEFINED):** Confidence is a classification, not a number. The classes are: `DETERMINISTIC` (the rule admits exactly one candidate), `AMBIGUOUS` (more than one candidate survives; fail closed), `HUMAN_REQUIRED` (insufficient evidence). A numeric confidence score is prohibited because it implies a certainty the engine cannot justify.

**SettleIQ-ARCH-R10 (PROPOSED, resolves OQ-01):** When two candidates are equally plausible, the engine does **not** tie-break. It emits an `AMBIGUOUS` decision containing both candidates, and the discrepancy engine raises a typed break. Choosing would be a guess, and guessing violates fail-closed. This must be settled in `07` before implementation; the architecture's position is stated here to prevent drift.

### 3.5 The Audit Journal

**SettleIQ-ARCH-R11 (OWNER-DEFINED):** Append-only, hash-chained, digests computed by the system and verified on read. See `08_DISCREPANCY_AND_AUDIT_SPEC.md`.

**SettleIQ-ARCH-R12 (PROPOSED):** The journal is a separate physical store from the canonical records, reached through a narrow interface with exactly two operations: `append(entry)` and `verify() -> Result`. This narrowness is deliberate: it makes the integrity property testable in isolation, and it prevents the rest of the system from accumulating write paths into the audit trail.

**SettleIQ-ARCH-R13 (OWNER-DEFINED):** No ambient clock, sequence counter, or random value participates in any digest preimage. Determinism and integrity would otherwise conflict, since a timestamp would make every digest unique and break reproducibility.

---

## 4. Deployment View

Single-node, single-database, Docker Compose.

| Element | Specification |
|---|---|
| Application | One service. No horizontal scaling in the first build (NG-10) |
| Database | PostgreSQL (PROPOSED, Q3), provisioned by Compose |
| Dashboard | TypeScript client served by the application's own API |
| Fixtures | Seeded on startup from a versioned generator with a fixed seed |
| Reproduction | `docker compose up` provisions, migrates, seeds, and is ready. Tests run in a second command or a test profile |

**SettleIQ-ARCH-R14 (PROPOSED, NG-10):** No distributed deployment, no message bus, no horizontal scaling. The architecture is single-node deliberately. `14_EMPLOYMENT_EVIDENCE.md` records honestly what this means the artifact does not demonstrate.

---

## 5. What This Architecture Deliberately Excludes

| Excluded | Reason |
|---|---|
| Event streaming / message bus | Batch deterministic processing first. Streaming would compromise determinism before it is proven (NG-12) |
| Caching layer | No demonstrated need; would add invalidation surface without evidence |
| Async job queue | A run is short and synchronous at demonstration scale; async would add failure modes without benefit |
| Separate ML serving component | NG-05 |
| Multi-tenant isolation | NG-02 |
| Read replicas | NG-10 |

---

## 6. Traceability

| Architecture requirement | Master requirement |
|---|---|
| ARCH-R01 | REQ-004 |
| ARCH-R02 | REQ-004, REQ-006 |
| ARCH-R03 | REQ-006 |
| ARCH-R04/R05 | REQ-002, REQ-006 |
| ARCH-R06 | REQ-005, REQ-006 |
| ARCH-R07 | REQ-005, REQ-009 |
| ARCH-R08 | REQ-012 |
| ARCH-R09 | REQ-007, REQ-009 |
| ARCH-R10 | REQ-009 |
| ARCH-R11 | REQ-010, REQ-011 |
| ARCH-R13 | REQ-012 |
| ARCH-R14 | REQ-015 |

---

## 7. Open Questions Carried Forward

* OQ-01 — tie-breaking when candidates are equally plausible. Architecture position: no tie-break, emit AMBIGUOUS. Must be confirmed in `07`.
* OQ-02 — residual allocation for non-dividing fees. Architecture position: explicit, named, deterministic, versioned. Must be confirmed in `07`.
* OQ-04 — scale target for performance work. Until set, no benchmark is designed.
* OQ-06 — whether M2's deliverable is "Stripe-shaped generators" (master §5) or the full adapter set. Architecture position: the **interface** is the deliverable; one adapter suffices to prove it.

**No component described in this document exists. Nothing is implemented.**
