# 11 — Testing and Performance Specification

**Document ID:** SETTLEIQ-TST-001
**Title:** Test Taxonomy, Financial Correctness Gates, and Benchmark Methodology
**Version:** 1.0.0
**Status:** PROPOSED — specification only; no implementation claimed
**Domain:** Testing, validation, benchmarking
**Governing document:** `SETTLEIQ-MASTER-SPEC.md`
**Date:** 2026-10-28
**Canonical path:** `docs/specifications/11_TESTING_AND_PERFORMANCE_SPEC.md`
**Owner:** Bukya Naresh (CN2)
**Traces to:** master requirements SETTLEIQ-REQ-003, 004, 005, 011, 012, 016; register R-QUA

---

## Document Control

This document specifies how SettleIQ proves its claims, and the conditions under which a performance benchmark may exist.

**This is a specification-only document.** No test is written. No test has been run. No benchmark exists. No performance figure has been measured.

**SettleIQ-TST-R01 (OWNER-DEFINED):** A test that is described but not run is not evidence. A test whose result is not recorded in the repository is not evidence. This specification's whole purpose is to make that enforceable.

---

## 1. Test Taxonomy

Seven classes, each with a distinct purpose. All seven must exist; a project with only unit tests has not tested a financial system.

| Class | Purpose | Proves |
|---|---|---|
| **Unit** | Individual functions in isolation | Local correctness |
| **Property-based** | Invariants hold over generated inputs | Correctness over a population, not examples |
| **Golden-file** | Recorded expected output for a fixed input | No unintended behavioural drift |
| **Determinism** | Identical inputs produce identical output | Reproducibility |
| **Fault injection** | Behaviour under malformed, partial, or hostile input | Fail-closed behaviour |
| **Tamper injection** | Audit integrity under modification | The integrity claim |
| **End-to-end** | The full workflow against a known dataset | The demonstration contract |

**SettleIQ-TST-R02 (OWNER-DEFINED):** Every one of the seven classes must exist and run in the single reproduction command. A class that is absent is reported as absent, not omitted from the list.

---

## 2. Financial Correctness Gates

### 2.1 The float gate

**SettleIQ-TST-R03 (OWNER-DEFINED):** A CI gate fails the build if a binary floating-point type appears in any monetary code path. This is a static/structural check, not a runtime test — a runtime test would only catch the paths that were exercised.

**SettleIQ-TST-R04 (OWNER-DEFINED):** The gate also rejects `float` entering through a JSON or API boundary. A float that arrives as a string and is parsed into a Decimal is fine; a float that is parsed into a Python `float` on the way in is a defect.

### 2.2 Property tests on Decimal

The following invariants are tested over generated inputs, not hand-picked examples:

| ID | Invariant |
|---|---|
| P-DEC-01 | `Decimal` addition is exact for generated values within the declared precision |
| P-DEC-02 | Mixed-currency arithmetic raises rather than converts |
| P-DEC-03 | Amounts are never silently rounded to a scale that loses precision |
| P-DEC-04 | A decomposition's constituents sum exactly to the payout amount |
| P-DEC-05 | Applying and reversing an operation (where reversible) returns the original value exactly |
| P-DEC-06 | Rounding, where applied, uses the declared mode and produces the declared result |

**SettleIQ-TST-R05 (OWNER-DEFINED):** Property tests use generated inputs with a fixed seed recorded in the test configuration. A property test with an unrecorded seed cannot be re-run and is not evidence.

### 2.3 Precision-loss detection

**SettleIQ-TST-R06 (OWNER-DEFINED):** A test asserts that an amount which would lose precision under a scale limit **raises** rather than rounds. This is the test that makes R-FIN-05 and REC-R09 real.

---

## 3. Determinism Testing

**SettleIQ-TST-R07 (OWNER-DEFINED):** The determinism test runs the same pipeline twice on identical input and compares output byte-for-byte, recording the diff (empty) in the repository.

**SettleIQ-TST-R08 (PROPOSED):** A stronger variant varies the *environment* — locale, hash seed, dict ordering, parallelism — and asserts identical output. This catches ambient leakage that a simple repeat run would miss.

**SettleIQ-TST-R09 (PROPOSED):** A structural check asserts that no prohibited value (wall clock, PID, sequence, random, memory address) reaches any serialization that feeds a digest.

---

## 4. Fault Injection

**SettleIQ-TST-R10 (OWNER-DEFINED):** Fault injection is mandatory. At minimum the following are injected and the engine's response asserted:

| Injected fault | Required behaviour |
|---|---|
| Malformed payload | Typed ingestion error; no partial canonicalization |
| Missing required field | Typed error naming the field |
| Duplicate submission | Idempotent: identical decision, no duplicate journal entry |
| Truncated file / stream | Typed error; no partial record |
| Unparseable currency code | Typed error |
| Amount exceeding precision | Raise, not round (P-DEC-03) |
| Empty batch | A clean no-op run, not an error |
| Unmodelled defect | `UNKNOWN` classification, countable |

**SettleIQ-TST-R11 (PROPOSED):** Each injected fault has a fixture with a recorded expected outcome. "The engine did not crash" is not a passing result; the *typed* result is.

---

## 5. Tamper Injection — the Integrity Suite

This is the suite that substantiates the project's integrity claim. It is the one a reviewer should run first.

| ID | Tamper | Required behaviour |
|---|---|---|
| T-01 | Modify a stored journal entry's payload | Detected on verify |
| T-02 | Modify a stored digest | Detected on verify |
| T-03 | Delete an entry | Detected (chain break) |
| T-04 | Insert a hand-written digest | Detected — this is the fabrication case |
| T-05 | Reorder entries | Detected |
| T-06 | Duplicate an entry | Detected |
| T-07 | Truncate the journal | Detected |

**SettleIQ-TST-R12 (OWNER-DEFINED):** All seven tamper cases must pass. A repository that stores hashes but has not run T-01 through T-07 has not demonstrated integrity — it has demonstrated that it can compute a hash function, which is not a security property.

**SettleIQ-TST-R13 (OWNER-DEFINED):** T-04 exists specifically because hand-written or patterned digests are a defect found in prior work. The test asserts that a digest value that was not computed from its entry is rejected.

---

## 6. End-to-End and the Demonstration Contract

**SettleIQ-TST-R14 (OWNER-DEFINED):** The end-to-end test executes the full workflow against a dataset with **known, injected defects** and asserts the final outcome for each. The assertion is on the classification, not on the mere presence of a break.

**SettleIQ-TST-R15 (OWNER-DEFINED):** The demonstration contract is: `clone → install → one command` → environment provisioned, schema migrated, fixtures seeded, all seven test classes run, worked investigation executed, recorded output produced. This is tested by a third party on a clean clone, not by the author on a warm machine.

**SettleIQ-TST-R16 (PROPOSED):** The injected defect set for the demonstration includes at minimum: a phantom charge on each side, an amount break, a fee misattribution, a mid-payout refund, a currency break, and an ambiguous match. Each has a known expected classification recorded before the run.

---

## 7. Benchmark Methodology — and Its Gate

### 7.1 No benchmark without a workload

**SettleIQ-TST-R17 (OWNER-DEFINED):** A benchmark is produced only if **all four** of the following conditions are satisfied:

1. A **specific, identified workload** exists whose measured runtime is dominated by computation rather than I/O.
2. A **Python baseline has been measured** on that workload, reproducibly.
3. A **correctness-equivalence test** exists proving two implementations agree exactly on Decimal results, including rounding.
4. A **meaningful benefit** is demonstrated — not asserted.

If any condition fails, no benchmark is produced. **The absence of a benchmark is stated, not hidden.** An empty benchmark section is a defect; a deleted milestone M8 with its deletion recorded is correct.

### 7.2 If a benchmark exists

**SettleIQ-TST-R18 (PROPOSED):** It must report: ns/op, allocations, memory profile, the exact input and its digest, the hardware and Python version, the number of iterations and warm-up policy, the variance across runs, and the **honest limits of the comparison**.

**SettleIQ-TST-R19 (OWNER-DEFINED):** A benchmark without a correctness-equivalence proof is not a benchmark; it is a stopwatch on two programs that may compute different things.

**SettleIQ-TST-R20 (PROPOSED):** If the workload turns out to be I/O-bound, the honest finding is recorded — "no C++17 component is justified; the engine is I/O-bound" — and no port is made. This is a legitimate and valuable outcome, not a failure.

---

## 8. Measurement Methodology — the Project's Own Metric

**SettleIQ-TST-R21 (OWNER-DEFINED):** The auto-match rate is computed by the system from recorded instrumented counts, never stated in prose.

**SettleIQ-TST-R22 (OWNER-DEFINED):** The methodology records and displays:
* **denominator definition** — what counts as an eligible record;
* **population** — which records were in scope for the run;
* **observation window** — a declared input, recorded in the input digest, never sampled from ambient time;
* **treatment of human-confirmed matches** — counted separately from deterministic matches, never silently merged.

**SettleIQ-TST-R23 (PROPOSED):** The metrics view presents the methodology inline with the figure, so a reader cannot strip the number from its definition.

**SettleIQ-TST-R24 (PROPOSED):** The rate is reproducible: two runs of identical input and identical rule version produce the same rate. This is tested, and the reproduction diff is recorded.

### 7.3 Guarding the metric against its own author

**SettleIQ-TST-R25 (PROPOSED):** Because the project authors both the engine and the methodology, the methodology itself must be inspectable: the denominator computation is code a reviewer can read, and a reviewer can recompute the rate from the raw counts by hand. A methodology that cannot be independently recomputed from published counts is unauditable regardless of how explicit it is.

---

## 9. CI Gates

**SettleIQ-TST-R26 (PROPOSED):** The pipeline runs, in order: lint → static/float gate → unit → property → golden-file → determinism → fault injection → tamper injection → contract → end-to-end. A later stage does not run if an earlier stage fails.

**SettleIQ-TST-R27 (PROPOSED):** The float gate and the tamper suite are **non-bypassable**. They are the two properties the artifact exists to demonstrate; allowing them to be skipped would make the artifact dishonest by configuration.

---

## 10. Acceptance Criteria

| # | Criterion |
|---|---|
| AC-01 | All seven test classes exist and run under the single reproduction command |
| AC-02 | The float gate rejects a deliberately introduced float in a monetary path |
| AC-03 | All six Decimal property tests pass with a recorded seed |
| AC-04 | Determinism produces byte-identical output across runs and across varied environments |
| AC-05 | Every fault-injection case produces its recorded typed outcome |
| AC-06 | All seven tamper cases detect modification |
| AC-07 | T-04 detects a hand-written digest specifically |
| AC-08 | The end-to-end demonstration classifies every injected defect correctly |
| AC-09 | A clean-clone third party reproduces the whole run |
| AC-10 | The auto-match rate reproduces across runs and is recomputable by hand from published counts |
| AC-11 | Either the four benchmark conditions hold and a benchmark exists, or they do not and the milestone's deletion is recorded |

---

## 11. Open Questions

* **OQ-04** — scale target for performance work. Until set, no benchmark is designed and no workload can be identified, so the Q2 gate cannot be evaluated.
* **Exact property-test framework and seed policy** — unspecified; any choice is acceptable provided the seed is recorded.
* **Whether contract tests are generated from OpenAPI or hand-written** — unspecified.
* **Coverage thresholds** — deliberately **not** specified. A coverage number is not evidence of correctness, and a coverage target invites tests written to hit the number.

---

## 12. What This Document Does Not Claim

No test exists. No test has run. No fixture is generated. No benchmark has been measured. No rate has been computed. No CI gate is configured. No third party has reproduced anything.
