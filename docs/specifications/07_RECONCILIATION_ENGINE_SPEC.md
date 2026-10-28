# 07 — Reconciliation Engine Specification

**Document ID:** SETTLEIQ-REC-001
**Title:** Settlement Decomposition, Matching Rules, Determinism, and Confidence
**Version:** 1.0.0
**Status:** PROPOSED — specification only; no implementation claimed
**Domain:** Engine
**Governing document:** `SETTLEIQ-MASTER-SPEC.md`; `05_ARCHITECTURE.md`
**Date:** 2026-10-28
**Canonical path:** `docs/specifications/07_RECONCILIATION_ENGINE_SPEC.md`
**Owner:** Bukya Naresh (CN2)
**Traces to:** master requirements SETTLEIQ-REQ-005, 006, 007, 008, 009, 012; register R-FIN, R-REC, R-DET

---

## Document Control

This document specifies the reconciliation engine: decomposition, matching, confidence, fail-closed behaviour, and determinism.

**This is a specification-only document.** No engine exists. No rule is implemented. No match has been produced.

**SettleIQ-REC-R01 (OWNER-DEFINED):** This specification must not weaken any master OWNER-DEFINED requirement. In particular it must not introduce a numeric confidence score, a silent rounding, or a tie-break that guesses.

---

## 1. What the Engine Does

Given a canonical set of charges, fees, refunds, adjustments, payouts, and bank deposits, the engine:

1. decomposes each payout into its constituents, exactly;
2. matches each constituent against the bank and ledger sides using versioned deterministic rules;
3. classifies each match as `DETERMINISTIC`, `AMBIGUOUS`, or `HUMAN_REQUIRED`;
4. raises a typed discrepancy for everything that did not match deterministically;
5. emits a `MatchDecision` with provenance for every comparison, matched or not;
6. contributes to the instrumented counts from which the auto-match rate is computed.

It never compares payout totals as the unit of reconciliation (REQ-006), never guesses (REQ-009), and never produces different output for identical input (REQ-012).

---

## 2. Decomposition

### 2.1 The operation

A payout `P` with amount `A` and currency `C` is decomposed into a set of constituents `{c₁…cₙ}` where each `cᵢ` is a charge, fee, refund, or adjustment with its own amount and currency.

**SettleIQ-REC-R02 (OWNER-DEFINED):** The decomposition must be **complete and reconciling**: `Σ amount(cᵢ) = A` exactly, as Decimal, in currency `C`. A decomposition with an unexplained residual is a defect. A residual that is silently discarded is a critical defect.

**SettleIQ-REC-R03 (OWNER-DEFINED):** A constituent that cannot be attributed to a known charge, fee, refund, or adjustment is modelled as an explicit `UNATTRIBUTED` constituent with its amount preserved. It is never absorbed into another constituent to make the sum work.

### 2.2 Fees, FX, and netting

**SettleIQ-REC-R04 (OWNER-DEFINED):** Fees are decomposed by fee type, not aggregated. A payout containing a processing fee and a cross-border fee carries both as separate constituents with separate types, so that a discrepancy on one is distinguishable from a discrepancy on the other.

**SettleIQ-REC-R05 (PROPOSED):** Where a payout is net of costs (the processor deducts fees/refunds before paying), the engine bridges gross-to-net explicitly: it records the gross total, the deductions by type, and the net paid, and reconciles all three. The net figure alone is never treated as the reconciled value.

**SettleIQ-REC-R06 (PROPOSED, resolves OQ-02):** When fees do not divide exactly across charges, a residual exists. The engine allocates it by a **declared deterministic rule** that is part of the rule version. The candidate rules to be evaluated are:
* **largest-remainder** — allocate integer parts, then distribute remaining units by descending remainder;
* **last-item absorption** — all residual assigned to a deterministic final item;
* **explicit residual constituent** — residual kept as its own named constituent and never allocated.

**The recommendation is the third option**: keeping the residual explicit is the only one that never assigns money to a wrong charge. It also makes the residual visible to the discrepancy engine, which is where it belongs. This must be confirmed before implementation; it is not settled here.

**SettleIQ-REC-R07 (OWNER-DEFINED):** Whatever rule is chosen, it is declared, versioned, and tested against hand-computed cases with known residuals. A residual allocation that is not tested is not implemented.

### 2.3 Currency

**SettleIQ-REC-R08 (OWNER-DEFINED):** Amounts in different currencies are never summed or compared. Conversion, where required, produces a new explicit record with the source amount, source currency, target currency, rate, rate source, and conversion timestamp recorded — and the rate is a declared input to the run, not an ambient lookup.

**SettleIQ-REC-R09 (PROPOSED, resolves OQ-02/R-DAT-04):** Currency minor-unit exponents vary (JPY 0, USD 2, BHD 3). The engine validates every amount against its currency's exponent and **raises rather than rounds** when precision would be lost. No single fixed scale is assumed anywhere in the model.

---

## 3. Matching

### 3.1 The unit and the sides

Reconciliation matches a **constituent** against a **record on the other side**. There are three sides in play:

* **processor side** — charges, fees, refunds, adjustments, and the payout that nets them;
* **bank side** — the deposit that received the money;
* **ledger side** — the internal record, if present.

**SettleIQ-REC-R10 (OWNER-DEFINED):** The reconciliation unit is the constituent, never the payout. Two payouts with equal totals and different compositions must not reconcile as equal.

### 3.2 Rules

**SettleIQ-REC-R11 (OWNER-DEFINED):** Matching is performed by versioned deterministic rules. A rule is a pure function from records to a candidate set. A rule carries: an identifier, a version, an ordered predicate list, and the fields it consumes.

**SettleIQ-REC-R12 (OWNER-DEFINED):** Rules are applied in declared order. Earlier rules take precedence. A later rule never overrides an earlier rule's decision; if the earlier rule resolves deterministically, later rules are not consulted.

**SettleIQ-REC-R13 (OWNER-DEFINED):** The rule version is part of the run identity. Two runs with different rule versions are different runs and must not be compared as if identical.

### 3.3 Candidate formation and classification

**SettleIQ-REC-R14 (OWNER-DEFINED):** A rule produces a **candidate set**, not a decision. Exactly one surviving candidate yields `DETERMINISTIC`. Zero surviving candidates yields a break. More than one yields `AMBIGUOUS`.

**SettleIQ-REC-R15 (OWNER-DEFINED, resolves OQ-01):** When more than one candidate survives, the engine does **not** tie-break. It emits `AMBIGUOUS` with the full candidate set, and the discrepancy engine raises a typed break. Choosing between equally plausible candidates is a guess, and guessing violates fail-closed. A numeric confidence score is prohibited because it would create a false ordering among candidates the engine cannot distinguish.

**SettleIQ-REC-R16 (OWNER-DEFINED):** `HUMAN_REQUIRED` is emitted when evidence is present but insufficient for a rule to resolve — for example, a match that requires interpreting free-text reference data the engine is not permitted to interpret.

### 3.4 Match fields

**SettleIQ-REC-R17 (PROPOSED):** Matching consumes, in declared precedence: exact amount, currency, a processor-supplied reference, a bank narration reference, and a date within a declared tolerance. The tolerance is a declared input, not a default.

**SettleIQ-REC-R18 (PROPOSED):** Narration and free-text reference matching is **not** performed by the first build's rules. It is the primary source of false confidence, and omitting it means every `DETERMINISTIC` match is genuinely deterministic. Adding it later requires an explicit decision and an evaluation harness, not a heuristic.

### 3.5 Duplicate and idempotency handling

**SettleIQ-REC-R19 (PROPOSED):** Reprocessing an identical input produces identical decisions and no duplicate journal entries. Idempotency is keyed on a canonical digest of the constituent and the rule version, not on arrival order.

**SettleIQ-REC-R20 (PROPOSED):** A duplicate submission is reported as a distinct typed event, not silently deduplicated. Deduplication is itself a reconciliation fact worth seeing.

---

## 4. Fail-Closed Behaviour

**SettleIQ-REC-R21 (OWNER-DEFINED):** Fail-closed is absolute. Where evidence is insufficient:
* an unresolvable break is reported;
* no approximate match is emitted;
* no difference is absorbed into a rounding residual;
* no default is applied to make a rule resolve.

**SettleIQ-REC-R22 (OWNER-DEFINED):** An ingestion error is never partially canonicalized. A malformed payload produces a typed ingestion error record, and no constituent enters the model from it.

**SettleIQ-REC-R23 (PROPOSED):** A rule that would produce `DETERMINISTIC` on fewer than all of its declared preconditions is defective and the run fails. Rules do not partially apply.

---

## 5. Determinism

**SettleIQ-REC-R24 (OWNER-DEFINED):** Identical canonical input plus identical rule version plus identical schema version produce byte-identical output. This is tested, not asserted.

**SettleIQ-REC-R25 (OWNER-DEFINED):** The following must not participate in any output or digest preimage: wall-clock time, monotonic clocks, PID, sequence counters, memory addresses, hash-map iteration order, or unsorted set iteration.

**SettleIQ-REC-R26 (PROPOSED):** Every collection that reaches a digest is canonically sorted by a declared key before serialization. Unordered iteration into a digest is a determinism defect and must be caught by the determinism test.

---

## 6. Decision Records

**SettleIQ-REC-R27 (OWNER-DEFINED):** Every comparison — matched or not — emits a `MatchDecision` containing:
* the constituent and the candidate records considered;
* the rule identifier and version applied;
* the classification (`DETERMINISTIC` / `AMBIGUOUS` / `HUMAN_REQUIRED`);
* the fields the rule consumed and their values;
* for `AMBIGUOUS`, the complete surviving candidate set;
* the input digest and rule version of the run.

**SettleIQ-REC-R28 (OWNER-DEFINED):** A decision with an empty provenance record is defective. Provenance is not optional metadata; it is the evidence the artifact exists to produce.

---

## 7. Acceptance Criteria

| # | Criterion | Test that proves it |
|---|---|---|
| AC-01 | Decomposition is exact: constituents sum to payout amount with no unexplained residual | Property test over generated payouts with known compositions |
| AC-02 | Fees are separated by type, never aggregated | Golden-file test |
| AC-03 | Residual allocation is explicit and matches the declared rule | Hand-computed cases with known residuals, including non-dividing fees |
| AC-04 | Cross-currency amounts are never summed | Property test that raises on mixed-currency arithmetic |
| AC-05 | Precision is never silently lost to a scale limit | Raise-not-round test against currencies with exponent 0 and 3 |
| AC-06 | Identical inputs produce byte-identical output | Determinism test, repeated runs, recorded diff |
| AC-07 | No ambient value reaches a digest | Determinism test with frozen and varied environment |
| AC-08 | Ambiguity is emitted, never tie-broken | Injected two-candidate case asserts `AMBIGUOUS` with both candidates present |
| AC-09 | Insufficient evidence yields a break, not an approximation | Injected incomplete-evidence case |
| AC-10 | Every decision carries provenance | Schema-level assertion; a decision with empty provenance fails the run |
| AC-11 | Reprocessing is idempotent | Duplicate-submission test asserting identical output and no duplicate journal entry |
| AC-12 | Rule version participates in run identity | Two runs differing only in rule version must not compare equal |

---

## 8. Open Questions This Specification Does Not Close

* **OQ-01** — architecture and engine position is *no tie-break, emit AMBIGUOUS*. Confirmed as the recommendation; not ratified.
* **OQ-02** — residual allocation. Recommendation is *explicit residual constituent*. Not ratified.
* **OQ-02b** — exact `numeric` scale policy across currencies. Recommendation is unconstrained with per-currency validation. Not ratified.
* **Date tolerance** — the declared tolerance for date matching is unspecified. It must be a declared input; its default value is a design decision not yet made.
* **Rule precedence order** — the order of field precedence in R-REC-17 is a proposal. The final ordering must be settled before rules are written, because changing it later changes every decision and invalidates prior runs.

**No engine exists. No rule is written. No match has been produced.**
