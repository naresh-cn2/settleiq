# 08 — Discrepancy Investigation and Audit Integrity

**Document ID:** SETTLEIQ-DSC-001
**Title:** Typed Discrepancy Taxonomy, Investigation Workflow, and Hash-Chained Audit
**Version:** 1.0.0
**Status:** PROPOSED — specification only; no implementation claimed
**Domain:** Discrepancy, investigation, audit integrity
**Governing document:** `SETTLEIQ-MASTER-SPEC.md`; `07_RECONCILIATION_ENGINE_SPEC.md`
**Date:** 2026-10-28
**Canonical path:** `docs/specifications/08_DISCREPANCY_AND_AUDIT_SPEC.md`
**Owner:** Bukya Naresh (CN2)
**Traces to:** master requirements SETTLEIQ-REQ-007, 008, 009, 010, 011; register R-DSC, R-AUD

---

## Document Control

This document specifies the discrepancy taxonomy, the investigation workflow, and the audit journal.

**This is a specification-only document.** No taxonomy is implemented. No journal exists. No discrepancy has been raised.

---

## 1. Why a Taxonomy and Not a Mismatch Field

**SettleIQ-DSC-R01 (OWNER-DEFINED):** Unmatched differences are classified into named types. A generic `mismatch: true` is prohibited.

The reason is operational, not cosmetic: a break that cannot be named cannot be triaged, aged, assigned, or explained to an auditor. A queue of indistinguishable breaks is indistinguishable from no tool at all. The taxonomy is the product's investigation surface.

**SettleIQ-DSC-R02 (PROPOSED, resolves OQ-03):** The taxonomy is **closed with an explicit `UNKNOWN` class**. A closed taxonomy is testable for exhaustiveness — every break is either a named type or `UNKNOWN`, and `UNKNOWN` is itself a reportable, countable outcome. An open taxonomy admits unmodelled breaks that silently look like handled ones.

An `UNKNOWN` break is not a failure of the design; it is the honest output of a fail-closed engine encountering something it does not model. It must be countable, visible, and never absorbed.

---

## 2. The Discrepancy Taxonomy

### 2.1 Presence and absence

These are the breaks that arise when a record exists on one side only.

| Type | Definition |
|---|---|
| `PHANTOM` | Present on one side, absent on the other — e.g. a charge in the processor with no corresponding ledger record |
| `LOST` | A record that was agreeably reconciled and later disappeared from one side |
| `SIDE_MISMATCH` | Records exist on both sides but agree with a third party in different groupings |

**SettleIQ-DSC-R03 (OWNER-DEFINED):** A presence/absence break must name **which side** holds the record. `PHANTOM_PROCESSOR` and `PHANTOM_LEDGER` are distinct types with distinct investigations. A single `PHANTOM` type that loses the side is defective.

This is not invented taxonomy. It is the distinction a processor vendor itself publishes: an open-settlement report reflects transactions "present in NetSuite and not present at the processor, or present at the processor and not present in NetSuite" — two different investigations, recorded as one class, would be useless.

### 2.2 Amount

| Type | Definition |
|---|---|
| `AMOUNT_BREAK` | Both sides have the record; amounts differ by more than the declared tolerance |
| `ROUNDING_RESIDUAL` | Amounts differ by at most the declared rounding tolerance, with a traced residual |
| `CURRENCY_BREAK` | Same reference, different currencies, with no recorded conversion |

**SettleIQ-DSC-R04 (OWNER-DEFINED):** `ROUNDING_RESIDUAL` carries an explicit traced residual with its allocation rule and rule version. A residual that cannot be traced is an `AMOUNT_BREAK`, not a rounding case.

**SettleIQ-DSC-R05 (OWNER-DEFINED):** A `CURRENCY_BREAK` is never resolved by converting silently. It is raised as a break unless an explicit conversion record exists in the run.

### 2.3 Fee and composition

| Type | Definition |
|---|---|
| `FEE_MISATTRIBUTION` | Fees exist on both sides but are attributed to different charges or types |
| `FEE_MISSING` | Fees deducted on one side are absent on the other |
| `NET_GROSS_BREAK` | Gross, deductions, and net do not reconcile under the declared bridging rule |

**SettleIQ-DSC-R06 (OWNER-DEFINED):** Fee breaks are typed by fee type. A `FEE_MISATTRIBUTION` on a processing fee is a different investigation from one on a cross-border fee.

### 2.4 Timing

| Type | Definition |
|---|---|
| `TIMING_BREAK` | Both sides hold the record; the settlement dates differ by more than the declared window |
| `SETTLEMENT_LAG_BREAK` | The payout arrived at the bank later than the declared expectation window |

**SettleIQ-DSC-R07 (PROPOSED):** The expectation window is a declared input to the run, recorded in the input digest — never a wall-clock "now". A window sampled from ambient time would make the discrepancy output non-reproducible.

### 2.5 Ambiguity and sufficiency

| Type | Definition |
|---|---|
| `AMBIGUOUS_MATCH` | More than one candidate survived matching; emitted rather than tie-broken |
| `INSUFFICIENT_EVIDENCE` | The engine could not resolve and fail-closed, with no candidate surviving |
| `RULE_VIOLATION` | A rule's declared preconditions were not all satisfied, so the rule did not apply |

**SettleIQ-DSC-R08 (OWNER-DEFINED):** `AMBIGUOUS_MATCH` carries the complete surviving candidate set in its evidence. An ambiguous break that does not show what it was ambiguous between cannot be investigated.

### 2.6 Exhaustiveness

**SettleIQ-DSC-R09 (OWNER-DEFINED):** Every path through the engine that fails to produce a `DETERMINISTIC` match must terminate in exactly one taxonomy type or `UNKNOWN`. There is no path that produces an unclassified break.

**SettleIQ-DSC-R10 (PROPOSED):** Exhaustiveness is tested structurally: a test iterates the engine's exit paths and asserts each maps to a declared type. A new code path that produces an untyped break fails the test. This is what makes the closed taxonomy enforced rather than aspirational.

---

## 3. Discrepancy Records

**SettleIQ-DSC-R11 (OWNER-DEFINED):** Every discrepancy record carries:

| Field | Purpose |
|---|---|
| `discrepancy_id` | Stable identity |
| `type` | Taxonomy type, or `UNKNOWN` |
| `severity` | Declared severity, derived from a declared rule — not a judgement |
| `age` | Derived from the run's declared clock, never ambient time |
| `contributing_records` | The records on each side |
| `decision_reference` | The `MatchDecision` that produced it |
| `provenance` | Fields consumed, rules applied, rule version |
| `status` | Open / assigned / resolved / unresolvable |
| `resolution_history` | Append-only record of state changes with actor and reason |

**SettleIQ-DSC-R12 (OWNER-DEFINED):** `age` is computed from the run's declared clock, not wall time, so that age is reproducible across runs of the same input. An age sampled from ambient time would break REQ-012.

**SettleIQ-DSC-R13 (PROPOSED):** `severity` is derived by a versioned declared rule from the type and the amount at stake, never a manual judgement recorded as data. Manual judgement belongs in `resolution_history`, where it is visible.

---

## 4. Investigation Workflow

**SettleIQ-DSC-R14 (PROPOSED):** The workflow is: raise → triage → investigate → resolve or mark unresolvable. Each transition is recorded append-only with actor, reason, and the evidence consulted at that step.

**SettleIQ-DSC-R15 (OWNER-DEFINED):** A resolution records what the investigator concluded, which records they relied on, and what changed. A resolution without a reason is not a resolution.

**SettleIQ-DSC-R16 (PROPOSED):** `UNRESOLVABLE` is a first-class, legitimate outcome. Marking a break unresolvable with a stated reason is correct engineering. Leaving it open with no reason is not.

**SettleIQ-DSC-R17 (PROPOSED):** The investigation workflow is exercised end to end by the worked demonstration: an injected defect is raised, triaged, investigated with its full evidence trail, and resolved. The demonstration asserts the final classification, not merely that a break appeared.

---

## 5. Audit Integrity

### 5.1 The journal

**SettleIQ-DSC-R18 (OWNER-DEFINED):** The discrepancy record store is append-only. No update, no delete, no in-place modification.

**SettleIQ-DSC-R19 (OWNER-DEFINED):** Journal entries are hash-chained. Each entry's digest is computed over the previous entry's digest and the entry's canonical serialization.

**SettleIQ-DSC-R20 (OWNER-DEFINED):** Digests are **computed by the system and verified on read**. A hand-written, patterned, or placeholder digest is a critical defect and is treated as fabricated evidence. This is the single most important integrity requirement in the project, because the fabrication of hash values is a defect found repeatedly in prior work and is trivially detectable by a reviewer who actually verifies.

**SettleIQ-DSC-R21 (OWNER-DEFINED):** No ambient value — wall clock, PID, sequence counter, random — participates in a digest preimage. A digest containing ambient data cannot be reproduced, which would break determinism.

### 5.2 The narrow interface

**SettleIQ-DSC-R22 (PROPOSED):** The journal is reachable only through two operations: `append(entry)` and `verify() -> Result`. The narrowness is what makes integrity testable in isolation and prevents write paths from accumulating.

### 5.3 Concurrency

**SettleIQ-DSC-R23 (PROPOSED):** Two concurrent appends must not be able to interleave into an invalid chain. Proven by a concurrency test using the database's transaction semantics, not by documentation.

### 5.4 Verification

**SettleIQ-DSC-R24 (OWNER-DEFINED):** `verify()` recomputes every digest from the stored entries' canonical serializations and compares against the stored digests. Any mismatch is a tamper detection.

**SettleIQ-DSC-R25 (PROPOSED):** Verification is a recorded, dated operation whose result is stored. "We verify on read" is not evidence; a recorded verification result is.

---

## 6. Acceptance Criteria

| # | Criterion | Test that proves it |
|---|---|---|
| AC-01 | Every injected defect class is classified into the correct named type | Injected-defect classification suite, all classes asserted |
| AC-02 | No path produces an unclassified break | Structural test iterating engine exit paths |
| AC-03 | `PHANTOM` variants distinguish sides | Injected cases on both sides produce distinct types |
| AC-04 | An untraced residual is an `AMOUNT_BREAK`, not a rounding case | Injected residual without allocation record |
| AC-05 | `UNKNOWN` is reachable and countable | Injected genuinely-unmodelled defect |
| AC-06 | Modifying a stored entry is detected | Tamper-injection test asserting detection |
| AC-07 | Modifying a digest is detected | Tamper-injection test on the digest itself |
| AC-08 | Deleting an entry is detected | Tamper-injection test asserting chain break |
| AC-09 | A fabricated digest is detected | Tamper-injection test with a hand-written digest value |
| AC-10 | Reordering entries is detected | Tamper-injection test |
| AC-11 | Concurrent appends cannot corrupt the chain | Concurrency test under contention |
| AC-12 | Age is reproducible | Two runs of identical input produce identical age |
| AC-13 | The worked investigation completes end to end with a resolution and evidence trail | Demonstration run with recorded output |

**Tests AC-06 through AC-10 are the core of the integrity claim.** A repository that shows hashes but does not run these tests has not demonstrated integrity; it has demonstrated formatting.

---

## 7. Open Questions

* **OQ-03** — closed-with-`UNKNOWN` is the recommendation. Not ratified.
* **Severity derivation rule** — the mapping from type and amount to severity is unspecified and must be declared before records are created.
* **Resolution authority** — whether a resolution requires a second actor is unspecified. The first build models a single investigator role.
* **Retention** — journal retention is unspecified and probably unbounded for the first build.

---

## 8. What This Document Does Not Claim

No taxonomy is implemented. No journal exists. No discrepancy has been raised, classified, aged, investigated, or resolved. No tamper test has been run. No verification result has been recorded.
