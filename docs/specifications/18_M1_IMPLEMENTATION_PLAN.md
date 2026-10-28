# 18 — M1 Implementation Plan

**Document ID:** SETTLEIQ-M1-001
**Title:** Milestone M1 — Canonical Data Model, Exact Arithmetic, and Frozen Source-Adapter Interface: Implementation Plan
**Version:** 1.0.0
**Status:** PROPOSED — plan only. Implementation is NOT authorized by this document.
**Domain:** Implementation planning
**Governing document:** `SETTLEIQ-MASTER-SPEC.md`; `13_ROADMAP_AND_ACCEPTANCE.md`
**Date:** 2026-10-28
**Canonical path:** `docs/specifications/18_M1_IMPLEMENTATION_PLAN.md`
**Owner:** Bukya Naresh (CN2)
**Traces to:** `13` M1; `16` §B.1, §B.2, §B.3, §B.8; master REQ-002, 003, 004, 005, 006, 007, 008, 012, 016

---

## Document Control

This document is the **implementation plan** for milestone M1. It defines file-level scope, the requirement each file satisfies, and the acceptance criterion that closes it.

**This document authorizes nothing.** It is a plan. The boundary is explicit: writing these files is implementation; the OWNER has not authorized implementation.

**SETTLEIQ-M1-R01 (OWNER-DEFINED):** This plan covers M1 only. It must not be read as authorization for M2 onward. `13` states the full sequence.

---

## 1. Why M1 is the right first milestone

M1 was selected because it depends **only on master OWNER-DEFINED requirements** and on the three `16` resolutions that must land in the data model anyway. A verification of that claim, item by item:

| M1 component | Depends on an unratified Q decision? | Basis |
|---|---|---|
| Decimal money and context | **No** | REQ-005 is OWNER-DEFINED |
| Currency exponent table and validator | **No** | REQ-005; `16` §B.3 resolves the open method |
| Canonical entity types | **No** | REQ-006 is OWNER-DEFINED |
| `RESIDUAL` and candidate-set shapes | **No** | `16` §B.1 and §B.2 resolve the open methods |
| `DataProvenance` field | **No** | REQ-002; `16` §B.8 |
| Run identity (`run_id`, `input_digest`, `rule_version`, `schema_version`) | **No** | REQ-012; determinism is OWNER-DEFINED |
| `SourceAdapter` interface | **Yes — Q1** | The *interface* is frozen regardless of how many adapters exist. Q1 governs Stripe-only, not the interface shape. **Mitigation:** the interface is specified adaptedly — it describes what any source must satisfy, so it is correct whether or not Adyen is later added. |
| Postgres schema and migrations | **Yes — Q3** | PostgreSQL is recommended but unratified. **Mitigation:** M1's persistence work is specified as the **migration tooling and DDL discipline** (forward-only, versioned, non-destructive), which applies under any Q3 outcome. The concrete `numeric` column work is called out as Q3-dependent. |
| Test suite | **No** | REQ-016 |

**Conclusion:** M1 is safe to start with two explicitly Q3-dependent callouts, and it does not require Q1–Q5 ratification to be *correct*. It does still require OWNER authorization to *begin*.

---

## 2. Scope

### In scope

| # | Deliverable | Requirement satisfied |
|---|---|---|
| S1 | Canonical financial data model (typed entities, Decimal money, explicit currency) | REQ-005, REQ-006 |
| S2 | Currency exponent table and validation raising on excess precision | REQ-005; `16` §B.3 |
| S3 | `RESIDUAL` constituent type and candidate-set shapes on decisions | `16` §B.1, §B.2 |
| S4 | `DataProvenance` enum on every canonical record | REQ-002; `16` §B.8 |
| S5 | Deterministic run identity: `run_id`, `input_digest`, `rule_version`, `schema_version` | REQ-012 |
| S6 | Canonical serialization with declared sort order and no ambient values | REQ-012; `06` DATA-R09 |
| S7 | Input validation and typed error taxonomy (fail-closed) | REQ-009; `07` R22 |
| S8 | `SourceAdapter` interface, frozen before any adapter is written | `05` ARCH-R04/R05 |
| S9 | Unit and property-based test suite over S1–S8 | REQ-016 |
| S10 | Reproducible development setup (lockfile, tooling config, one-command test) | REQ-003 |

### Explicitly out of scope for M1

* Any adapter implementation (M2).
* Any reconciliation logic, matching rule, or rule registry (M3).
* Any discrepancy classification (M4).
* Any journal implementation or hashing (M5).
* Any HTTP surface or OpenAPI document (M6).
* Any dashboard (M7).
* Any benchmark (M8, and only if the four conditions hold).
* Docker Compose stack beyond what M1's test command needs (M9).
* Java or C++ of any kind — not deferred, excluded (`16` §A.2).

---

## 3. File-level plan

Proposed Python package layout. **No file below exists.** This is the intended structure.

```
settleiq/
├── pyproject.toml                   # S10 — deps pinned; linter + type-checker config
├── README.md                        # S10 — reproduction command, honest status
├── Makefile                         # S10 — `make test` is the single command
├── docs/
│   ├── specifications/              # existing, unchanged by M1
│   └── research/
├── src/settleiq/
│   ├── __init__.py
│   ├── money/
│   │   ├── __init__.py
│   │   ├── amount.py                # S1 — Money type: Decimal + currency, immutable
│   │   ├── context.py               # S1 — declared DecimalContext and rounding mode
│   │   ├── currency.py              # S2 — declared exponent table + CurrencyCode value type
│   │   └── errors.py                # S7 — CurrencyNotSupported, CurrencyPrecisionExceeded
│   ├── model/
│   │   ├── __init__.py
│   │   ├── entities.py              # S1/S3/S4 — Charge, Fee, Refund, Adjustment,
│   │   │                           #          Payout, SettlementBatch, BankDeposit,
│   │   │                           #          ReconciliationRun, MatchDecision,
│   │   │                           #          Discrepancy, plus RESIDUAL, candidate sets
│   │   ├── identifiers.py           # S5 — EntityId, RunId derived deterministically
│   │   ├── provenance.py            # S4 — DataProvenance enum
│   │   └── run_identity.py          # S5/S6 — RunIdentity tuple + input digest
│   ├── canonical/
│   │   ├── __init__.py
│   │   ├── serialization.py         # S6 — canonical bytes; declared sort; no ambient values
│   │   └── digest.py                # S6 — SHA-256 over canonical serialization
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── ingest.py                # S7 — record-level validation, typed errors
│   │   └── errors.py                # S7 — ingestion error taxonomy
│   └── adapters/
│       ├── __init__.py
│       ├── interface.py             # S8 — SourceAdapter protocol, frozen at M1
│       └── errors.py                # S8 — normalization errors
└── tests/
    ├── unit/                        # S9
    ├── property/                    # S9 — hypothesis or equivalent, fixed seed recorded
    ├── golden/                      # S9 — canonical serialization fixtures
    ├── determinism/                 # S9
    └── fixtures/                    # deterministic seeds
```

### Notes on deliberately absent files

* **No `adapters/stripe.py`.** M2's work. Writing it in M1 would violate "frozen before written".
* **No `engine/` or `reconciliation/`.** M3's work.
* **No `journal/`.** M5's work.
* **No `api/`.** M6's work.
* **No `bench/`.** M8's work, and conditional.
* **No `Cargo.toml`, `pom.xml`, or any non-Python build file.** Excluded by `16` §A.2.

---

## 4. Acceptance criteria

M1 closes only when **every** criterion below is satisfied by executed tests with recorded output. A criterion satisfied by prose is not satisfied.

### AC-1 — Exact money

* **AC-1.01:** `Money` is immutable, carries an explicit currency, and rejects construction from a binary float (including via a JSON-parsed float). Test asserts `Money("10.5", "USD") == Money("10.50", "USD")` and that `Money(10.5, "USD")` raises.
* **AC-1.02:** the declared `DecimalContext` and rounding mode are set once, reused, and a rounding event is recorded wherever it occurs. A test asserts the context is the declared one and that no path uses the default context for money.
* **AC-1.03:** mixed-currency arithmetic raises rather than converting. Test asserts `Money("1","USD") + Money("1","EUR")` raises `CurrencyMismatch`.

### AC-2 — Currency exponent validation (`16` §B.3)

* **AC-2.01:** `"100.5"` in JPY is rejected with `CurrencyPrecisionExceeded`.
* **AC-2.02:** `"1043.275"` in USD is rejected.
* **AC-2.03:** `"1043.275"` in BHD is accepted.
* **AC-2.04:** an unknown currency code is rejected with `CurrencyNotSupported` — never defaulted to 2.
* **AC-2.05:** the exponent table is versioned and its version participates in `schema_version`/run identity.

### AC-3 — Canonical model

* **AC-3.01:** every entity carries an explicit currency on every amount and a `DataProvenance`.
* **AC-3.02:** `RESIDUAL` exists as a constituent type with amount, currency, `allocation_rule_id`, and `rule_version` fields (`16` §B.2).
* **AC-3.03:** `MatchDecision` can carry a candidate set with **no** member marked selected (`16` §B.1).
* **AC-3.04:** settled-record immutability is expressed in the type system — a correction is a superseding record, not an in-place update.
* **AC-3.05:** the entity set is fixed; adding/removing one requires an OWNER decision recorded in `12` (mirrors `06` DATA-R10).

### AC-4 — Determinism and run identity (`16`, REQ-012)

* **AC-4.01:** `RunIdentity` is the tuple `(input_digest, rule_version, schema_version)` and `run_id` is derived from it deterministically — not a UUID, not a client value, not a DB sequence.
* **AC-4.02:** `input_digest` is SHA-256 over the canonical serialization of the complete input set, including the fixture manifest and adapter/generator identity and version.
* **AC-4.03:** two runs differing only in `rule_version` do not compare equal.
* **AC-4.04:** canonical serialization sorts every collection by a declared key; no wall clock, PID, sequence counter, random value, or memory address appears in any serialization. A **structural test** asserts prohibited values do not reach the serializer.
* **AC-4.05:** byte-identical output across repeated runs, recorded diff empty.
* **AC-4.06:** byte-identical output across varied environments (locale, hash seed, dict ordering, parallelism).
* **AC-4.07:** `rule_version` and `schema_version` are placeholders at M1 with declared semantics, because no rules and no migrations exist yet — and their participation in run identity is **already tested**.

### AC-5 — Input validation and fail-closed

* **AC-5.01:** malformed payload → typed ingestion error; no partial canonicalization.
* **AC-5.02:** missing required field → typed error naming the field.
* **AC-5.03:** duplicate submission → idempotent result, identical decision, no duplicate record.
* **AC-5.04:** truncated stream → typed error; no partial record.
* **AC-5.05:** unparseable currency → `CurrencyNotSupported`.
* **AC-5.06:** amount exceeding precision → raise, not round (AC-2).
* **AC-5.07:** empty batch → clean no-op run, not an error.
* **AC-5.08:** unmodelled defect → `UNKNOWN` — note: `UNKNOWN` classification is M4's job; at M1 the requirement is only that the *model* can represent it.

### AC-6 — SourceAdapter interface (`05` ARCH-R04/R05)

* **AC-6.01:** the interface is defined, documented, and **frozen before any adapter is written** — verified by the repository containing no adapter implementation.
* **AC-6.02:** the interface declares: a `source_version`, a `schema_version` carried into every produced object, a fail-closed contract returning typed errors, and a canonical-model return type.
* **AC-6.03:** a **mock adapter** exists in tests and satisfies the interface — proving the interface is implementable — without being a Stripe adapter.
* **AC-6.04:** the contract is exercised against a golden-file fixture with no network access.

### AC-7 — Reproducibility (REQ-003)

* **AC-7.01:** `make test` (or the single documented command) runs unit, property, golden-file, and determinism suites and exits non-zero on any failure.
* **AC-7.02:** dependencies are pinned by lockfile; a clean environment reproducibly installs.
* **AC-7.03:** property tests use a **recorded** fixed seed in test configuration.
* **AC-7.04:** a static check fails the build if a binary float appears in a monetary code path (`11` T-ST-R03). At M1 this is enforced on `src/settleiq/money/` and `src/settleiq/model/`.
* **AC-7.05:** a third party on a clean clone runs the single command and gets recorded output.

### AC-8 — Traceability

* **AC-8.01:** every AC above cites its source requirement in the test file's docstring.
* **AC-8.02:** the traceability matrix (`17`) lists each M1 acceptance criterion against its master requirement.

---

## 5. What M1 does not claim when it closes

Even fully green, M1 does **not** establish:

* that the reconciliation engine works (M3);
* that discrepancies are classified correctly (M4);
* that the audit journal detects tampering (M5);
* that the API or dashboard exists (M6/M7);
* any performance figure whatsoever (M8, conditional);
* any commercial or market property (prohibited entirely by REQ-001).

M1 closing means: **the money arithmetic is exact, the model is canonical and provenance-carrying, run identity is deterministic and reproducible, the adapter interface is frozen, and the fail-closed validation behaviour is tested.** That is a real and substantial claim. It is not more than that.

---

## 6. Risks specific to M1

| ID | Risk | Mitigation / gate |
|---|---|---|
| M1-R1 | Float enters via JSON parsing or a dependency, silently defeating AC-1 | AC-7.04 static gate; test constructs Money from a float-parsed JSON and asserts rejection |
| M1-R2 | Determinism broken by an ambient value that only appears under a different environment | AC-4.06 varied-environment test, not just repeated-run |
| M1-R3 | Adapter interface designed around Stripe's shape specifically, making Adyen additive-but-costly | AC-6.02 requires source-versioned, source-agnostic contract; the mock adapter is not Stripe-shaped |
| M1-R4 | Canonical serialization order left implicit, so a refactor changes digests | AC-4.04 declared sort order; golden-file fixtures |
| M1-R5 | Entity set drifts during M1, invalidating M2–M5 plans | AC-3.05; entity set frozen with an OWNER-decision gate to change |
| M1-R6 | A "test" that asserts a type exists rather than a behaviour | Every AC states an observable outcome, not a shape |

---

## 7. Readiness verdict for M1

**Ready to plan — not ready to start.**

* File-level scope: defined above.
* Acceptance criteria: defined above, all executable.
* Dependencies: none on unratified Q1/Q2/Q4/Q5. **Q3-dependent callouts are isolated to the migration-tooling discipline**, which transfers under any Q3 outcome.
* Blocking prerequisite: **explicit OWNER authorization to implement.**

The single unresolved item that would change this plan is Q3 ratification, and only in the migration-tooling section. Everything else is independent of the five decisions.
