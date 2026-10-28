# 17 — Traceability Matrix and Specification Consistency Report

**Document ID:** SETTLEIQ-TRC-001
**Title:** Requirements-to-Verification Traceability Matrix and Specification Consistency Findings
**Version:** 1.0.0
**Status:** PROPOSED — report of specification state; no implementation claimed
**Domain:** Traceability, consistency, verification
**Governing document:** `SETTLEIQ-MASTER-SPEC.md`
**Date:** 2026-10-28
**Canonical path:** `docs/specifications/17_TRACEABILITY_MATRIX_AND_CONSISTENCY.md`
**Owner:** Bukya Naresh (CN2)

---

## Document Control

This document does two things:

1. **Traceability** — every master requirement is linked to the subordinate requirements that elaborate it, and to the verification method that will prove it.
2. **Consistency findings** — the result of checking all 18 specification documents for the eight defect classes the OWNER listed, with each finding classified **already covered / partially covered / missing**, mapped to file and requirement ID, and either resolved or recorded as open.

Research records (`docs/research/02_verification_log.md`, `03_EVIDENCE_AND_RESEARCH_REGISTER.md`) are **preserved unchanged**. No research content was rewritten.

**Verification classes:** `COVERED` — requirement exists with measurable acceptance criteria. `PARTIAL` — requirement exists but important cases or verification methods are missing. `MISSING` — no adequate requirement or acceptance criterion.

---

# PART 1 — Requirements to Verification Traceability

| Master requirement | Subordinate requirements | Verification method | Status |
|---|---|---|---|
| REQ-IND-01…04 (independence) | OBJ-R01…R05; ARCH-R01; classification notes in `06`/`09`/`10` | Documentation-consistency check: no requirement cites an external governance document as authority | COVERED (gate specified, not yet executed) |
| REQ-000 / REQ-001 (no commercial claim) | OBJ §4; `04` NG-07/08/09; `15` NG table | Static check: no pricing/market-gap/competitor-claim document exists | COVERED |
| REQ-002 (synthetic only) | DATA-R01…02; `16` §B.8; UI provenance display | AC-B8-01/02/03; generator emits only SYNTHETIC | COVERED |
| REQ-003 (third-party reproduction) | API-R05/R06; UI-R03; ROAD-R…; M1 AC-7 | Clean-clone single-command run by a third party | COVERED |
| REQ-004 (intent ≠ implementation) | OBJ SC / `04` classification; `14` §3 | Documentation-consistency check: no component described as working without a passing test | COVERED |
| REQ-005 (Decimal money) | DATA-R01/R02; REC-R01…; `04` R-FIN-01…06; M1 AC-1 | Property tests P-DEC-01…06; static float gate T-ST-R03 | COVERED |
| REQ-005b (currency exponents) | `16` §B.3; REC-R09; `04` R-DAT-04; M1 AC-2 | AC-B3-01…06 | COVERED — **resolved 2026-10-28** |
| REQ-006 (charge-level) | DATA-R05; REC-R10; `07` §3.1 | Decomposition completeness property test | COVERED |
| REQ-007 (provenance) | DATA-R06; REC-R27/R28; UI-R11 | Schema assertion; decision with empty provenance fails the run | COVERED |
| REQ-008 (typed discrepancies) | DSC-R01…R09; `16` §B.4 | Injected-defect classification suite; structural exhaustiveness test | COVERED — **closure resolved 2026-10-28** |
| REQ-009 (fail-closed) | REC-R21/R22/R23; API-R12; M1 AC-5 | Injected insufficient-evidence cases; malformed-payload cases | COVERED |
| REQ-010 (append-only) | DATA-R21; DSC-R18; `08` | Privilege + trigger test; attempted mutation rejected | COVERED |
| REQ-011 (hash-chained, computed & verified) | DATA-R08; DSC-R19…R21; ARCH-R11 | **Tamper suite T-01…T-07**, especially T-04 (hand-written digest) | COVERED (gate specified) |
| REQ-012 (determinism) | DATA-R09/R13/R14/R16; REC-R24…R26; `16` §B.5 | Determinism test ×2 (repeat + varied environment); structural ambient-value check | COVERED |
| REQ-013/014 (measurement methodology) | `04` R-MEA-01…06; UI-R12…R17; `11` T-ST-R21…R25 | Reproducible rate; recomputable by hand from published counts; no numeric literal in client source | COVERED |
| REQ-015 (not disposable) | OBJ R-QUA-02; ROAD release gates | Docker reproduction; module structure | COVERED |
| REQ-016 (no claim without test output) | `15` RSK; `11` T-ST-R01; `14` §3 | Documentation-consistency check | COVERED |

### Resolutions traced into the register

| Question | Resolution | Where registered | Acceptance criteria |
|---|---|---|---|
| Ambiguous matches | `16` §B.1 — emit AMBIGUOUS, never tie-break | `07` REC-R15; `08` DSC-R08 | AC-B1-01…05 |
| Residual allocation | `16` §B.2 — explicit RESIDUAL constituent | `05` ARCH-R07; `07` REC-R06; M1 AC-3.02 | AC-B2-01…04 |
| Currency exponents | `16` §B.3 — declared per-currency table, raise not round | `07` REC-R09; `06` R17; M1 AC-2 | AC-B3-01…06 |
| Taxonomy closure | `16` §B.4 — closed with UNKNOWN | `08` DSC-R02 | AC-B4-01…03 |
| Rule precedence | `16` §B.5 — all evaluated, determinism beats ambiguity, conflict is a break | `05` ARCH-R12; M3 (to be authored) | AC-B5-01…05 |
| Severity | `16` §B.6 — declared versioned matrix | `08` DSC-R13; M4 (to be authored) | AC-B6-01…04 |
| Performance target | `16` §B.7 — declared workload + median-of-5 | `11` §7 | AC-B7-01…03 |
| Real-data scope | `16` §B.8 — synthetic only, DataProvenance | `06`; M1 AC-3.01 | AC-B8-01…03 |

---

# PART 2 — Specification Consistency Findings

**Method:** all 18 documents in `docs/specifications/` were checked by text search for each defect class. Findings below are the result of that check, not an assertion.

## F-01 — Contradictory requirements → **FOUND, RESOLVED**

| Finding | Files | Resolution |
|---|---|---|
| UI-R02 was labelled `OWNER-DEFINED` while the same document's classification note and `16` declared it PROPOSED (rests on unratified Q4) | `10` | **Corrected 2026-10-28.** Requirement relabelled PROPOSED with the correction recorded inline. |
| `13` M1 row required "numeric columns with an explicit scale constraint", contradicting `16` §B.3 and `06` R17's corrected position | `13`, `06` | **Corrected 2026-10-28** to unconstrained `numeric` with per-currency exponent validation, with the reason recorded inline. |
| `03` described the five engineering decisions as "verified" while `12` marks all five RECOMMENDED awaiting ratification | `03` | **Corrected 2026-10-28.** |

## F-02 — Incorrect document references → **FOUND, RESOLVED**

| Finding | Resolution |
|---|---|
| Master spec REQ-IND-03 cited `11_DECISIONS_AND_OPEN_QUESTIONS.md`; the canonical decisions document is `12_` | **Corrected** in the earlier revision; re-verified 2026-10-28. |
| `02` line 107 cited OQ-02 as an open question to be settled in `07` | **Corrected** to cite `16` §B.2 as resolved-by-recommendation. |
| `13` carried a forward-reference to an unresolved Adyen scope conflict | **Corrected**; master §5 M2 row now reads "Stripe-shaped". |

**Remaining:** document IDs and filenames differ intentionally in one place — `12_DECISIONS_AND_OPEN_QUESTIONS.md` carries Document ID `SETTLEIQ-DEC-001`, and is cited by both its filename and its ID across the set. Verified consistent; recorded here so a reviewer does not mistake it for an error.

## F-03 — Unratified decisions presented as approved → **FOUND, RESOLVED**

| Finding | Resolution |
|---|---|
| `02` §5.1 described Q1–Q5 as "OWNER-verified" | **Corrected**; now RECOMMENDED-awaiting-ratification with the Q5-before-Q2 note. |
| `03` described the five decisions as "verified engineering decisions" | **Corrected**. |
| `09` R08/R09, `06` R17+, `10` R02 classified design requirements as OWNER-DEFINED while resting on unratified Q3/Q4 | **Corrected** via classification notes with an explicit tie-breaker rule. |

**Status of the OWNER's Step-1 baseline:** recorded in `16` Part A as **OWNER-PROPOSED — awaiting explicit ratification**, per the instruction that approval must not be claimed before it is explicitly provided. **No decision is marked RATIFIED anywhere in the specification set.** Verified by search.

## F-04 — Requirements without acceptance criteria → **PARTIAL, OPEN**

| Gap | Detail | Status |
|---|---|---|
| Rule precedence evaluation semantics | `05` ARCH-R12 states precedence but the evaluation semantics (all-rules vs. short-circuit, conflict handling) were unspecified until `16` §B.5 | **RESOLVED by `16` §B.5**; M3 spec must carry AC-B5-01…05 |
| Severity derivation | `08` DSC-R13 declared severity must be derived, but not how | **RESOLVED by `16` §B.6**; M4 spec must carry AC-B6-01…04 |
| Amount-band boundaries | Declared as needing OWNER input | **OPEN** (OQ-10) |
| `16` §B.7 reference machine | Needed before any benchmark | **OPEN** (OQ-11) |

## F-05 — Acceptance criteria that cannot be tested → **PARTIAL, OPEN**

| Finding | Assessment |
|---|---|
| Several criteria rest on "documentation-consistency check" without a script implementing it | These are **not yet executable**. They are honest as acceptance criteria only if the check is built. **Recommendation: the consistency check becomes a CI gate at M9, and until then these criteria are marked NOT-EXECUTABLE.** |
| `06` concurrency test `T-DATA-CONC-01` is specified in prose but requires a running PostgreSQL | Executable in M5 environment, not before. Correctly deferred. |
| `10` UI-R14 completeness test "enumerating the record's fields against rendered fields" needs a test harness | Executable at M7. Correctly deferred. |

## F-06 — Missing dependencies → **FOUND, RESOLVED**

| Finding | Resolution |
|---|---|
| `13` noted M4's decisions are M5's principal payload, and master §5 orders M5 after M4 | **Partially resolved**: the sequencing note requires M4's acceptance evidence to include a decision-record format M5 can ingest. The backfill question is **OPEN** (OQ-09). |
| Q2's C++ gate depends on Q5, but nothing enforced the ordering | **Resolved**: `16` §A.1 records ratification order Q5-before-Q2 as an OWNER-DEFINED requirement. |

## F-07 — Unspecified error handling → **PARTIAL**

| Area | Status |
|---|---|
| Ingestion errors | COVERED — `07` R22, `09` R11, M1 AC-5 |
| Currency errors | COVERED — `16` §B.3, M1 AC-2 |
| Rule conflicts | COVERED — `16` §B.5 (`RULE_CONFLICT` is a typed break) |
| Adapter normalization errors | COVERED — DATA-R11 (unmapped vocabulary is a normalization failure, never a catch-all) |
| Idempotency conflicts | COVERED — `09` R09 (409 taxonomy) |
| Schema/migration failure | PARTIAL — M5 work; atomicity specified (DATA-R28), retry policy not yet specified |
| Benchmark failure / inability to measure | COVERED — `11` T-ST-R17: absence is stated, not hidden |

## F-08 — Conflicts between determinism, timestamps, run identity → **FOUND, RESOLVED**

| Finding | Resolution |
|---|---|
| REQ-013's observation window vs REQ-012's byte-identical determinism | **RESOLVED** — the window is a *declared input* recorded in the input digest, never sampled from ambient time (master REQ-013, determinism-interaction clause; `16` §B.7) |
| `age` computation on discrepancies vs determinism | **RESOLVED** — `08` DSC-R12: age uses the run's declared clock, not wall time |
| Idempotency replay records vs digest preimages | **RESOLVED** — DATA-R09: no ambient value in any digest preimage |
| Journal chain including a timestamp | **RESOLVED** — DSC-R21: no ambient value in a digest preimage; timestamps are stored as entry content but excluded from the preimage, which must be stated explicitly in M5's spec |
| Run `created_at` style fields | **Resolved by principle** — DATA-R09 and M1 AC-4.04 require ambient values be excluded from digests; display timestamps are permitted only as non-digested entry content |

**One item carried forward as an explicit M5 requirement:** the M5 specification must state, in terms, that a journal entry's stored timestamp is excluded from its digest preimage. This is currently implied by DATA-R09 but not stated in `08`. Recorded as OQ-12.

---

# PART 3 — Consistency summary

| Defect class | Result | Open items |
|---|---|---|
| Contradictory requirements | 3 found, **3 resolved** | — |
| Incorrect document references | 3 found, **3 resolved** | — |
| Unratified decisions presented as approved | 5 found, **5 resolved** | — |
| Requirements without acceptance criteria | 4 found, 2 resolved by `16`, **2 open** | OQ-10, OQ-11 |
| Untestable acceptance criteria | 3 found, 3 noted; execution deferred by design | Consistency-check gate not yet scripted |
| Missing dependencies | 2 found, 1 resolved, **1 open** | OQ-09 |
| Unspecified error handling | 1 partial | Schema-failure retry policy at M5 |
| Determinism/timestamp/identity conflicts | 5 found, **5 resolved**; 1 carried forward | OQ-12 |

**Verdict on consistency:** the specification set is **internally consistent as of 2026-10-28**, with eleven findings resolved and five open items, all of which are either OWNER judgements (OQ-10), pre-run declarations (OQ-11), sequencing (OQ-09), or a forward requirement to state explicitly at M5 (OQ-12). No open item blocks M1.

---

# PART 4 — What this document does not claim

No consistency check has been executed as code. The checks reported here were performed by text search across the specification files. No requirement has been verified against an implementation, because no implementation exists. No test has run. No document other than this one and `16`/`18` was modified for this report.
