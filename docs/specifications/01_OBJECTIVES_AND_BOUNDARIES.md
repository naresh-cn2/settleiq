# 01 — Objectives and Boundaries

**Document ID:** SETTLEIQ-OBJ-001
**Title:** Objectives, Independence, Scope Boundaries, and Success Criteria
**Version:** 1.0.0
**Status:** PROPOSED — specification only; no implementation claimed
**Domain:** Objectives, boundaries, independence, success criteria
**Governing document:** `SETTLEIQ-MASTER-SPEC.md` (SETTLEIQ-MASTER-SPEC-001)
**Date:** 2026-10-28
**Canonical path:** `docs/specifications/01_OBJECTIVES_AND_BOUNDARIES.md`
**Owner:** Bukya Naresh (CN2)
**Traces to:** SETTLEIQ-MASTER-SPEC-001 §1, §2.1, §8 (row 01)

---

## Document Control

This document states what SettleIQ is for, where its boundaries are, and what "done" means. It is the document to read first and the document to return to when a scope question arises.

It is a **specification-only document**. Nothing here is implemented.

---

## 1. The Objective

SettleIQ is built to demonstrate, on synthetic data a third party can inspect, the engineering involved in payment settlement reconciliation and discrepancy investigation. Its audience is a hiring manager evaluating a candidate for financial-systems, ledgering, or backend engineering work.

The artifact is judged on whether a competent stranger can satisfy themselves, from the repository alone, that:

1. the money arithmetic is exact and provably so;
2. the reconciliation logic is correct and reproducible;
3. discrepancies are classified into named types rather than discarded into a generic mismatch;
4. every decision carries traceable evidence;
5. the audit record cannot be altered without detection;
6. the project's own performance claims are measured with a stated methodology, not asserted.

That is the whole objective. It is narrow on purpose. A project that demonstrates six things rigorously is stronger evidence than one that gestures at twenty.

**Why this objective and not a commercial one:** research completed 2026-10-27 established, at primary-source level, that the capabilities a commercial thesis would have rested on — auditability, explainability, human-approval gating, published pricing, fast deployment — are all documented by funded competitors. The commercial differentiation thesis was therefore rejected on evidence and is not to be revived without new buyer evidence. See `03_EVIDENCE_AND_RESEARCH_REGISTER.md` for the record, including which claims were verified and which were not.

**Employment-first does not mean technically modest.** Client work and commercial use remain possible later. What is prohibited is making product decisions on an unproven market gap.

---

## 2. Project Independence

SettleIQ is an independent project. This is binding and is restated from the master specification for visibility:

* **SETTLEIQ-OBJ-R01 (OWNER-DEFINED):** SettleIQ owns its own product definition, architecture, technical decisions, specifications, implementation, tests, benchmarks, and engineering documentation. No other repository governs any of these.
* **SETTLEIQ-OBJ-R02 (OWNER-DEFINED):** SettleIQ inherits no architecture, requirements, roadmap, or implementation task from PROJECT-TOP1, STRATA-ENGINE, Forex-platform, crypto-platform, or any other repository. Those projects are separately owned.
* **SETTLEIQ-OBJ-R03 (OWNER-DEFINED):** SettleIQ imports no implementation from another repository. Prior work may be consulted as reference material. Every line SettleIQ runs is written here and tested here, and any borrowed pattern carries a requirements-based justification recorded in `12_DECISIONS_AND_OPEN_QUESTIONS.md` — never "it exists elsewhere."
* **SETTLEIQ-OBJ-R04 (OWNER-DEFINED):** No external governance document is cited as authority for a SettleIQ requirement. Principles adopted from elsewhere are restated here as SettleIQ's own requirements, owned and testable in this repository.
* **SETTLEIQ-OBJ-R05 (OWNER-DEFINED):** SettleIQ's presence on a personal roadmap is progress tracking only, is one-directional, and confers no engineering authority. Progress reported externally must match the repository's own milestone state.

**What this means in practice:** a reader of this repository should never need to open another repository to understand, build, or evaluate SettleIQ. If a document references another repository, the reference must be in a clearly-marked historical or contextual note, never as a dependency.

---

## 3. What SettleIQ Is

A payment settlement reconciliation and discrepancy investigation engine that:

* ingests processor transaction data and bank settlement data through a frozen source-adapter interface;
* decomposes payout-level records into charge-level components — charges, fees, refunds, adjustments — using exact-decimal arithmetic;
* reconciles the decomposed constituents against the bank and ledger sides;
* classifies unmatched differences into **named, typed discrepancies** with age, severity, and provenance;
* records every decision in an append-only, hash-chained journal whose digests are computed by the system and verified on read;
* computes and reports its own auto-match rate with an explicit, documented measurement methodology.

**The distinguishing practice, stated precisely:** the last item. SettleIQ does not claim that any vendor lacks a measurement methodology. It *demonstrates the practice on itself*, on data a third party can inspect, with the denominator, population, window, and human-confirmation treatment recorded in code. That converts a genuine industry gap in published practice into a property the artifact possesses, without making any competitive assertion.

---

## 4. What SettleIQ Is Not

Binding non-claims, restated from `SETTLEIQ-REQ-001`:

1. Not a claim that any named competitor lacks auditability, explainability, or charge-level capability. Verified sources show these are documented by Numeric, Ramp, and Xero.
2. Not a claim of a market gap, market size, or underserved segment.
3. Not a claim of product-market fit, commercial viability, or willingness to pay. **No buyer contact exists and no buyer validation has been performed.**
4. Not a claim of superior matching accuracy against any named product.
5. Not a competitive analysis, pricing recommendation, or go-to-market plan.
6. Not connected to live money movement, live customer financial data, or any real payment instrument.

Additional boundaries specific to this project:

7. Not a general-purpose accounting or bookkeeping system. It reconciles settlements; it does not keep books.
8. Not a machine-learning project. The matching core is deterministic and rule-based. Any assistive layer is out of scope for the first build and would require its own evaluation harness before being claimed.
9. Not a distributed systems project. It is a single-node, single-database system. See `14_EMPLOYMENT_EVIDENCE.md` for the honest list of what that means it does *not* demonstrate.
10. Not a performance-engineering showcase. A benchmark is produced only if a compute-bound workload is identified and measured; otherwise none is produced and none is claimed.

---

## 5. Success Criteria

The project succeeds when all of the following hold. Each is verifiable; none is satisfied by prose.

| # | Criterion | Verified by |
|---|---|---|
| SC-1 | A third party clones the repository and runs one command that provisions the environment, migrates the schema, seeds deterministic fixtures, and executes the full test suite | Clean-clone reproduction, recorded |
| SC-2 | No monetary computation anywhere in the codebase uses binary floating point | Property test suite plus a CI gate that fails the build on a float in a monetary code path |
| SC-3 | Identical inputs plus identical rule version produce byte-identical output | Determinism test with a recorded comparison |
| SC-4 | An injected set of known defects is classified into the correct named discrepancy types, every class asserted | Injected-defect classification suite |
| SC-5 | Modifying any journal entry is detected on read | Tamper-injection test that proves detection, not merely that hashes exist |
| SC-6 | The auto-match rate is computed by the system from instrumented counts, reproduces across runs, and displays its denominator, population, declared window, and human-confirmation treatment | Metrics report with a reproducibility diff |
| SC-7 | A typed discrepancy can be traced end to end: produced, investigated, resolved, with the full evidence trail visible in the dashboard | Worked investigation against a known dataset |
| SC-8 | Every milestone in `13_ROADMAP_AND_ACCEPTANCE.md` is closed by recorded executed output or is explicitly marked not closed | Repository state |

**The project does not succeed** if any of the following is true, regardless of how much code exists:

* a test is described but not run;
* a digest is present but not computed and verified;
* a rate is stated in prose without its methodology;
* a component is documented as working without a passing test;
* a benchmark exists without a correctness-equivalence proof.

---

## 6. Non-Negotiable Constraints

| Constraint | Basis |
|---|---|
| Synthetic data only; no real credentials, feeds, or customer data | SETTLEIQ-REQ-002 |
| `decimal.Decimal` for all money; no binary float | SETTLEIQ-REQ-005 |
| Charge-level reconciliation, never payout-total comparison | SETTLEIQ-REQ-006 |
| Provenance on every match decision | SETTLEIQ-REQ-007 |
| Named typed discrepancies, never a generic mismatch | SETTLEIQ-REQ-008 |
| Fail-closed: insufficient evidence reports an unresolvable break | SETTLEIQ-REQ-009 |
| Append-only, hash-chained audit journal; digests computed and verified | SETTLEIQ-REQ-010/011 |
| Determinism: byte-identical output for identical inputs and rule version | SETTLEIQ-REQ-012 |
| Measurement methodology published in code, never in prose | SETTLEIQ-REQ-013/014 |
| No completion claim without executed test output | SETTLEIQ-REQ-016 |

---

## 7. Authorization Status

**No implementation is authorized.** The five engineering questions (processor scope, language architecture, persistence, dashboard scope, target role) are recommended in `12_DECISIONS_AND_OPEN_QUESTIONS.md` and await OWNER ratification. Ratification order matters: **Q5 before Q2**, because Q2's conditional C++17 gate depends on the target-role decision.

Until ratification, the correct activity is specification, not implementation.
