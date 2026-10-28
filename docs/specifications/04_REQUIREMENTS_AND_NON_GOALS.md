# 04 — Requirements Register and Non-Goals

**Document ID:** SETTLEIQ-REQ-001
**Title:** Consolidated Requirements Register and Explicit Non-Goals
**Version:** 1.0.0
**Status:** PROPOSED — specification only; no implementation claimed
**Domain:** Requirements, priorities, traceability, non-goals
**Governing document:** `SETTLEIQ-MASTER-SPEC.md` (SETTLEIQ-MASTER-SPEC-001)
**Date:** 2026-10-28
**Canonical path:** `docs/specifications/04_REQUIREMENTS_AND_NON_GOALS.md`
**Owner:** Bukya Naresh (CN2)
**Traces to:** SETTLEIQ-MASTER-SPEC-001 §2 (all requirements)

---

## Document Control

This is the **single consolidated register** of SettleIQ requirements. Where a subordinate specification states a requirement, it traces to an entry here; it does not create a competing requirement.

**Classification:**
* **OWNER-DEFINED** — established by the OWNER. Changed only by explicit OWNER decision.
* **PROPOSED** — recommended; not binding until ratified.
* **IMPLEMENTED / VALIDATED** — reserved for statements backed by executed tests. **No requirement in this register carries these states. Nothing is implemented.**

**Priority:** `P1` must hold for the artifact to be honest. `P2` must hold for the artifact to be complete. `P3` improves it. A P1 requirement is never traded away for a P3 convenience.

---

## 1. Independence and Frame

| ID | Requirement | Class | Priority | Source |
|---|---|---|---|---|
| R-IND-01 | SettleIQ is independent; owns its product definition, architecture, decisions, and implementation | OWNER-DEFINED | P1 | Master REQ-IND-01 |
| R-IND-02 | Inherits no architecture, requirements, or roadmap from any other repository | OWNER-DEFINED | P1 | Master REQ-IND-02 |
| R-IND-03 | Imports no implementation from another repository; borrowed patterns require a recorded requirements-based justification | OWNER-DEFINED | P1 | Master REQ-IND-03 |
| R-IND-04 | No external governance document cited as authority for a requirement | OWNER-DEFINED | P1 | Master REQ-IND-04 |
| R-FRM-01 | No competitive, market-gap, pricing, or product-market-fit claim in any artifact | OWNER-DEFINED | P1 | Master REQ-001 |
| R-FRM-02 | Intent and implementation are never presented in the same register | OWNER-DEFINED | P1 | Master REQ-004 |

---

## 2. Data and Environment

| ID | Requirement | Class | Priority | Source |
|---|---|---|---|---|
| R-DAT-01 | Synthetic generator-produced data only; no real credentials, bank feeds, or customer data | OWNER-DEFINED | P1 | Master REQ-002 |
| R-DAT-02 | Deterministic fixtures: fixed seed, fixed generator version, fixed schema version; a run is identified by its input digest | OWNER-DEFINED | P1 | Master REQ-011/REQ-012, `06` |
| R-DAT-03 | PostgreSQL as sole durable store, provisioned by Docker Compose | PROPOSED (Q3) | P1 | `12` §Q3 |
| R-DAT-04 | Amount columns are `numeric`; unconstrained scale with per-currency exponent validation | PROPOSED (Q3, revised) | P1 | `06`, OQ-02 |
| R-DAT-05 | Forward-only versioned migrations; no destructive migration in any environment | PROPOSED (Q3) | P2 | `06` |

> **Note on R-DAT-04:** a single fixed `numeric(p,s)` scale is **not** assumed. ISO 4217 minor-unit exponents vary (JPY = 0, BHD = 3, USD = 2), and Postgres rounds beyond the declared scale, which would silently corrupt amounts. The working position is unconstrained `numeric` with validation against the currency's exponent, plus a raise-not-round test. This is a deliberate, documented departure from the original recommendation.

---

## 3. Financial Correctness

| ID | Requirement | Class | Priority | Source |
|---|---|---|---|---|
| R-FIN-01 | All monetary values are `decimal.Decimal` with explicit context and explicit rounding mode | OWNER-DEFINED | P1 | Master REQ-005 |
| R-FIN-02 | Binary floating point is never used for any amount, fee, balance, or rounding computation | OWNER-DEFINED | P1 | Master REQ-005 |
| R-FIN-03 | Every amount carries an explicit currency; no implicit currency is ever assumed | OWNER-DEFINED | P1 | Derived from REQ-005 |
| R-FIN-04 | A CI gate fails the build if a float appears in a monetary code path | PROPOSED | P1 | ADR-001 |
| R-FIN-05 | Rounding is never applied silently; every rounding is explicit and recorded | OWNER-DEFINED | P1 | Derived from REQ-005 |
| R-FIN-06 | Derived amounts (totals, nets, differences) are computed, not stored, or if stored are recomputed and compared on read | PROPOSED | P2 | Derived from REQ-004 |

---

## 4. Reconciliation Semantics

| ID | Requirement | Class | Priority | Source |
|---|---|---|---|---|
| R-REC-01 | Reconciliation operates at charge level; a payout is decomposed into charges, fees, refunds, and adjustments and each constituent is matched | OWNER-DEFINED | P1 | Master REQ-006 |
| R-REC-02 | Payout totals are never used as the reconciliation unit | OWNER-DEFINED | P1 | Master REQ-006 |
| R-REC-03 | Matching is deterministic and rule-based; rules carry a version that participates in the run identity | OWNER-DEFINED | P1 | Master REQ-012 |
| R-REC-04 | Every match decision carries provenance: fields used, rule that produced it, confidence class, determinism guarantee | OWNER-DEFINED | P1 | Master REQ-007 |
| R-REC-05 | Confidence is classified into explicit classes (deterministic / ambiguous / human-required), not a numeric score implying certainty | PROPOSED | P1 | `07` |
| R-REC-06 | Fail-closed: where evidence is insufficient, an unresolvable break is reported. Never guess, approximate, or silently absorb | OWNER-DEFINED | P1 | Master REQ-009 |
| R-REC-07 | Idempotent processing: reprocessing the same input produces the same decisions and no duplicate journal entries | PROPOSED | P1 | `09` |
| R-REC-08 | The source-adapter interface is frozen at M1, before any adapter is written | PROPOSED (Q1) | P1 | `12` §Q1 |

---

## 5. Discrepancy and Audit

| ID | Requirement | Class | Priority | Source |
|---|---|---|---|---|
| R-DSC-01 | Unmatched differences are classified into named, tested types; never a generic "mismatch" | OWNER-DEFINED | P1 | Master REQ-008 |
| R-DSC-02 | The taxonomy is exhaustive and closed, with an explicit `UNKNOWN` class for genuinely unmodelled breaks | PROPOSED (OQ-03) | P1 | `08` |
| R-DSC-03 | Each discrepancy carries age, severity, contributing records, and a resolution history | PROPOSED | P2 | `08` |
| R-AUD-01 | The discrepancy record store is append-only | OWNER-DEFINED | P1 | Master REQ-010 |
| R-AUD-02 | Journal entries are hash-chained; each digest is computed over the previous digest and the entry's canonical serialization | OWNER-DEFINED | P1 | Master REQ-011 |
| R-AUD-03 | Digests are computed by the system and verified on read. A hand-written, patterned, or placeholder digest is a critical defect treated as fabricated evidence | OWNER-DEFINED | P1 | Master REQ-011 |
| R-AUD-04 | A tamper-injection test proves modification is detected | PROPOSED | P1 | ADR-003 |
| R-AUD-05 | Journal append and ledger write are atomic | PROPOSED (Q3) | P1 | `06` |
| R-AUD-06 | Concurrent appends cannot interleave into an invalid chain; proven by a concurrency test | PROPOSED | P1 | `06` |

---

## 6. Determinism and Reproducibility

| ID | Requirement | Class | Priority | Source |
|---|---|---|---|---|
| R-DET-01 | Identical inputs and identical rule version produce byte-identical output | OWNER-DEFINED | P1 | Master REQ-012 |
| R-DET-02 | No ambient clock, wall time, sequence, or random seed participates in any output or any digest preimage | PROPOSED | P1 | `06` DATA-R09 |
| R-DET-03 | Determinism is tested, not asserted | OWNER-DEFINED | P1 | Derived from REQ-012 |
| R-DET-04 | Every run is identified by `run_id`, `input_digest`, `rule_version`, `schema_version` | PROPOSED (Q3) | P1 | `06` |
| R-REP-01 | `clone → install → one command` provisions, migrates, seeds, and runs tests, producing recorded output | OWNER-DEFINED | P1 | Master REQ-003 |

---

## 7. Measurement

| ID | Requirement | Class | Priority | Source |
|---|---|---|---|---|
| R-MEA-01 | The auto-match rate is published with an explicit methodology: denominator definition, population, observation window, treatment of human-confirmed matches | OWNER-DEFINED | P1 | Master REQ-013 |
| R-MEA-02 | The observation window is a declared input recorded in the input digest, never sampled from ambient time | OWNER-DEFINED | P1 | Master REQ-013 (determinism interaction) |
| R-MEA-03 | The rate is computed by the system from recorded instrumented counts | OWNER-DEFINED | P1 | Master REQ-014 |
| R-MEA-04 | The rate never appears in prose anywhere in the repository | OWNER-DEFINED | P1 | Master REQ-014 |
| R-MEA-05 | A human-confirmed or assisted match is counted separately from a deterministic match, never silently merged into one number | OWNER-DEFINED | P1 | Master REQ-013 |
| R-MEA-06 | The methodology is written so that a reader cannot mistake the figure for an unqualified accuracy claim | PROPOSED | P1 | `10` |

---

## 8. Interface and Presentation

| ID | Requirement | Class | Priority | Source |
|---|---|---|---|---|
| R-API-01 | REST resources with OpenAPI as the contract source of truth; the API is not implemented without a contract test | PROPOSED | P1 | `09` |
| R-API-02 | Every mutating endpoint is idempotent by client-supplied key; duplicate submission returns the original result | PROPOSED | P1 | `09` |
| R-API-03 | The API never returns a confident answer where the engine is unresolved | OWNER-DEFINED | P1 | Master REQ-009, `09` |
| R-UI-01 | Five functional views: run list, discrepancy queue, investigation detail, metrics, run history/diff | PROPOSED (Q4) | P1 | `10` |
| R-UI-02 | No styling system, component library, or design tokens until a functional requirement demands them | PROPOSED | P2 | `10` |

---

## 9. Quality

| ID | Requirement | Class | Priority | Source |
|---|---|---|---|---|
| R-QUA-01 | No component is described as working without a recorded passing test | OWNER-DEFINED | P1 | Master REQ-016 |
| R-QUA-02 | Modular, tested, documented, Docker-runnable components with a documented evolutionary path | OWNER-DEFINED | P1 | Master REQ-015 |
| R-QUA-03 | Test taxonomy covers unit, property-based Decimal invariants, determinism, fault injection, tamper injection, contract, and end-to-end | PROPOSED | P1 | `11` |
| R-QUA-04 | A benchmark is produced only under the four Q2 gating conditions; otherwise none is produced and its absence is stated | PROPOSED (Q2) | P2 | `12` §Q2 |

---

## 10. Explicit Non-Goals

Each non-goal is binding with its reason. A proposal that would satisfy a non-goal requires an OWNER decision to add it.

| # | Non-goal | Reason |
|---|---|---|
| NG-01 | No live money movement, no real customer data, no production credentials | REQ-002; safety and honesty — a demo on real data would be evidence of nothing a reviewer can reproduce |
| NG-02 | No multi-tenancy, no authentication UI, no user management | Not required by any use case; adds surface without evidence |
| NG-03 | No C++17 production component | No identified compute-bound workload. Four gating conditions must be met first |
| NG-04 | No Java service | Java is not justified by this architecture. If it is an employment requirement, it is separate focused practice, recorded honestly as such in `14` |
| NG-05 | No machine-learning or LLM matching component | The deterministic core is the point. An assistive layer would require its own evaluation harness and falsifiable accuracy claims before being claimed |
| NG-06 | No Adyen adapter in the first build | Q1 recommends Stripe-only; the frozen adapter interface is the deliverable, not the adapter count |
| NG-07 | No competitor benchmarking | Competitor claims are prohibited by REQ-001; benchmarking against them would require capabilities we have verified exist |
| NG-08 | No pricing, go-to-market, or commercial-viability work | No buyer evidence exists. Writing such a document would be fabricating the evidence for it |
| NG-09 | No claim that competitors lack any capability | Directly contradicted by verified sources |
| NG-10 | No distributed-systems or horizontal-scaling work | The system is single-node. `14` records honestly what this means the artifact does not demonstrate |
| NG-11 | No accounting/bookkeeping functionality | SettleIQ reconciles settlements; it does not keep books |
| NG-12 | No real-time streaming or webhook ingestion in the first build | Batch and deterministic processing first; streaming would compromise determinism guarantees before they are proven |

---

## 11. Requirement Coverage Check

| Master requirement area | Covered by |
|---|---|
| Independence | R-IND-01…04 |
| Frame and non-claims | R-FRM-01/02, NG-07/08/09 |
| Synthetic data | R-DAT-01, NG-01 |
| Decimal money | R-FIN-01…06 |
| Charge-level reconciliation | R-REC-01/02 |
| Provenance | R-REC-04 |
| Typed discrepancies | R-DSC-01/02 |
| Fail-closed | R-REC-06 |
| Append-only hash chain | R-AUD-01…03 |
| Determinism | R-DET-01…04 |
| Reproducibility | R-REP-01 |
| Measurement methodology | R-MEA-01…06 |
| No completion claim without tests | R-QUA-01 |
| Quality and finish | R-QUA-02/03/04 |

**Unresolved requirements — none may be closed by assertion:**

* The exact `numeric` scale policy (OQ-02).
* Whether the discrepancy taxonomy is closed-with-UNKNOWN or open (OQ-03).
* Tie-breaking when two candidate matches are equally plausible (OQ-01).
* Residual allocation when fees do not divide exactly across charges (OQ-02, `07`).
* The scale target for performance work (OQ-04).
