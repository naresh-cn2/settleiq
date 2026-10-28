# 13 — Roadmap and Acceptance

**Document ID:** SETTLEIQ-ROAD-001
**Title:** SettleIQ Roadmap, Dependency Order, and Acceptance Gates
**Version:** 1.0.0
**Status:** PROPOSED — specification only; no implementation claimed
**Domain:** Milestones, sequencing, acceptance evidence, release gates
**Governing document:** `SETTLEIQ-MASTER-SPEC.md` (SETTLEIQ-MASTER-SPEC-001)
**Date:** 2026-10-28
**Canonical path:** `docs/specifications/13_ROADMAP_AND_ACCEPTANCE.md`
**Owner:** Bukya Naresh (CN2)
**Traces to:** SETTLEIQ-MASTER-SPEC-001 §4 (Demonstration Contract), §5 (Milestones), §8 row 13, §9; SETTLEIQ-DEC-001 Q1–Q5 and OQ-01…OQ-05; SETTLEIQ-REQ-003, REQ-004, REQ-012, REQ-015, REQ-016

---

## Document Control

### Purpose

This document fixes SettleIQ's milestone numbering, dependency order, and closure mechanics. It takes the milestone table of `SETTLEIQ-MASTER-SPEC-001` §5 as given — the same numbers, the same names, the same acceptance-evidence gist, the same role-evidence column — and adds what that table does not carry: what must exist before a milestone may start, what recorded output closes it, what blocks what, and what may be said about the project at each stage.

### Authority and classification convention

Requirements are classified:

* **OWNER-DEFINED** — restated from a binding requirement of `SETTLEIQ-MASTER-SPEC-001` or `SETTLEIQ-DEC-001`. These may only change by explicit OWNER decision.
* **PROPOSED** — recommended by this document. Not binding until ratified by the OWNER.

**No requirement in this document is IMPLEMENTED or VALIDATED.** Nothing is built. Every milestone below is not started. Any statement in this document about what a component will do is a statement of intent governed by SETTLEIQ-REQ-004.

Where a requirement below rests on one of the five engineering questions Q1–Q5, it is classified **PROPOSED**, because none of those questions is ratified (`SETTLEIQ-DEC-001` status convention: RATIFIED — none yet).

### What this document does not claim

No milestone has started. No milestone has been closed. No milestone has been deleted. No test has been executed, no benchmark has been run, no container has been built, and no code exists. The words "implemented", "complete", "verified", and "working" are not available for any SettleIQ component as of 2026-10-28.

---

## 1. Sequencing Rules

**SETTLEIQ-ROAD-R01 (OWNER-DEFINED):** The milestone set is M1 through M9 as enumerated in `SETTLEIQ-MASTER-SPEC-001` §5. That table is the source of the milestone numbers, names, acceptance-evidence statements, and target-role column. This document shall not renumber, rename, split, merge, or add milestones. A change to the milestone set is an amendment to the master specification and requires an OWNER decision recorded there.

**SETTLEIQ-ROAD-R02 (OWNER-DEFINED):** No milestone is closed by prose. Closure requires recorded executed output committed to the repository at a recorded path, together with the command that produced it, the rule version active at the time, and the environment it ran in. A milestone whose evidence cannot be re-executed by a third party is not closed (SETTLEIQ-REQ-003, REQ-016).

**SETTLEIQ-ROAD-R03 (OWNER-DEFINED):** Every milestone's acceptance evidence shall be re-executable by the M9 single-command reproduction path. Evidence recorded outside that path — a terminal transcript, a screenshot, a narrated result — does not close a milestone.

**SETTLEIQ-ROAD-R04 (PROPOSED):** A milestone shall not be closed while any milestone it depends on is unclosed. Dependencies are stated per milestone in §3 and summarised in the graph in §4.

**SETTLEIQ-ROAD-R05 (OWNER-DEFINED):** Implementation of any milestone requires the five engineering questions Q1–Q5 to be marked **RATIFIED** in `SETTLEIQ-DEC-001`. Until then, no code shall be written, and every milestone requirement in this document remains PROPOSED. See §5.1.

**SETTLEIQ-ROAD-R06 (OWNER-DEFINED):** M8 is conditional. It exists only if all four gating conditions in `SETTLEIQ-DEC-001` §Q2 hold, each with recorded evidence. If any condition does not hold, M8 is **deleted, not deferred**, and its absence is stated in the repository rather than hidden (restated from `SETTLEIQ-MASTER-SPEC-001` §5 row M8 and §4 item 5).

**SETTLEIQ-ROAD-R07 (PROPOSED):** A deletion of M8 shall be recorded as an explicit entry naming which of the four conditions failed and what evidence was examined. A milestone set in which M8 is simply absent from the list, with no deletion record, is a documentation defect.

**SETTLEIQ-ROAD-R08 (OWNER-DEFINED):** The repository's own milestone state is authoritative for all external progress reporting (`SETTLEIQ-MASTER-SPEC-001` §7). If the repository says a milestone is not started, no external report may say otherwise. External reporting is generated from the repository state, never written independently of it.

**SETTLEIQ-ROAD-R09 (PROPOSED):** The "Target role evidence" column of each milestone is interpreted against the Q5 recommendation — primary emphasis financial systems and ledgering engineering, supporting frame backend engineering, secondary data infrastructure — which is **RECOMMENDED, awaiting ratification**. A role-emphasis claim is not available until Q5 is ratified.

**SETTLEIQ-ROAD-R10 (PROPOSED):** Each milestone entry in this document carries an explicit status line. A milestone's status takes exactly one of: **NOT STARTED**, **IN PROGRESS**, **CLOSED** (with recorded evidence at a recorded path), or **DELETED** (M8 only, per R07). As of 2026-10-28 every milestone is NOT STARTED.

---

## 2. Milestone Status Summary

Milestone names and acceptance-evidence gist are reproduced from `SETTLEIQ-MASTER-SPEC-001` §5 without alteration. Dependencies and status are added by this document.

| # | Milestone (master §5) | Acceptance evidence (master §5) | Dependencies | Status |
|---|---|---|---|---|
| M1 | Canonical data model + Decimal invariants, property-tested | Property test suite output; invariant violations fail the build | Q1–Q5 ratified | **NOT STARTED — NOT BUILT** |
| M2 | Source adapters + Stripe/Adyen-shaped generators with injected defects | Golden-file tests; defect generator tests | M1 | **NOT STARTED — NOT BUILT** |
| M3 | Settlement decomposer + charge-level reconciliation | Worked decomposition test with exact expected totals | M1, M2 | **NOT STARTED — NOT BUILT** |
| M4 | Matching engine + typed discrepancy taxonomy | Injected-defect classification suite, all classes asserted | M1, M3 | **NOT STARTED — NOT BUILT** |
| M5 | Append-only hash-chained audit journal, digests computed and verified | Tamper-injection test proves verification detects modification; determinism test proves byte-identical output | M1, M4 | **NOT STARTED — NOT BUILT** |
| M6 | Metrics with published methodology | Reproducible report across runs; denominator documented in code | M1, M4, M5 | **NOT STARTED — NOT BUILT** |
| M7 | REST + OpenAPI + investigation dashboard | Contract tests; running UI against live engine | M1–M6 | **NOT STARTED — NOT BUILT** |
| M8 | **Conditional.** Python-vs-C++17 benchmark, only if the four Q2 gating conditions are satisfied | Benchmark output; stated caveats; correctness-equivalence proof | M3 or M4 workload identification, Q5 ratified, four Q2 conditions | **CONDITIONAL — NOT STARTED, NOT BUILT. Existence not established; deletion not recorded** |
| M9 | Docker + single-command reproduction | Clean-clone reproduction by a third party | M1–M7 (M8 if and only if it exists) | **NOT STARTED — NOT BUILT** |

---

## 3. Milestone Detail

### M1 — Canonical data model + Decimal invariants, property-tested

**Status: NOT STARTED. Nothing is built.** No domain class exists, no schema exists, no migration has run, no property test has executed, and no `SourceAdapter` interface has been frozen.

**Deliverable (PROPOSED):** The canonical typed model for charge, payout, fee, refund, chargeback/dispute, adjustment, FX conversion, bank deposit, and discrepancy, with `decimal.Decimal` money under an explicit context and an explicit rounding mode (SETTLEIQ-REQ-005). Amounts carry explicit currency. Settled records are immutable once committed; a correction is a superseding record, not an in-place update. The persistence shape of that model — `numeric` columns **without a fixed scale constraint** (per-currency exponent validation instead; see `16` §B.3) and a database-level check rejecting non-finite input, forward-only versioned migrations, deterministic seed fixtures identified by an input digest — is owned by `06_DATA_MODEL_AND_PERSISTENCE.md` and depends on the Q3 recommendation. **[Corrected 2026-10-28: an earlier draft of this row required "numeric columns with an explicit scale constraint", which contradicts the B.3 resolution. A single fixed scale cannot hold because ISO minor-unit exponents vary (JPY 0, USD 2, BHD 3) and Postgres rounds beyond a declared scale, silently corrupting amounts.]** In addition, and non-negotiably, the **`SourceAdapter` interface is defined and frozen at M1, before either adapter is written** (`SETTLEIQ-DEC-001` §Q1, non-negotiable condition).

**Acceptance evidence required to close (OWNER-DEFINED gist, PROPOSED detail):**

1. Property test suite output recorded in the repository: Decimal invariants (exact decimal arithmetic, no binary float on any monetary path, explicit rounding mode, currency carried with every amount) exercised over generated inputs; any invariant violation fails the build.
2. A test that the canonical model cannot represent a monetary value as a binary float through the domain, persistence, serialization, or JSON boundary.
3. A recorded interface definition for `SourceAdapter` with a contract test suite that any future adapter must pass.
4. Migration output from a clean database producing the declared schema version, recorded.
5. A fixture-generator manifest recording generator version, fixed seeds, and schema version, from which an input digest is computed.

**Dependencies:** Ratification of Q1–Q5 (ROAD-R05). Q3 governs the persistence choices exercised here; Q1 governs the adapter interface's first implementer. Neither is ratified, so the detail above is PROPOSED.

**Target role evidence (master §5: Ledgering, Quant Dev):** Exact-decimal monetary modelling, rounding-mode discipline, schema and constraint design, invariant-driven testing.

### M2 — Source adapters + Stripe/Adyen-shaped generators with injected defects

**Status: NOT STARTED. Nothing is built.** No adapter exists, no generator exists, no golden file exists, and no injected defect has been produced.

**Deliverable (PROPOSED):** A Stripe-shaped source adapter implementing the M1-frozen `SourceAdapter` contract, plus a synthetic generator producing processor-shaped transaction records, bank-shaped deposit records, and ledger-shaped records with **injected defects**: a phantom charge, an amount break, a fee misattribution, a mid-payout refund, and an FX rounding carryover (the set named in `SETTLEIQ-MASTER-SPEC-001` §4 item 3). All data is generator-produced; no real credentials, no real bank feeds (SETTLEIQ-REQ-002).

**Acceptance evidence required to close:**

1. Golden-file test output: adapter output for a fixed input digest is byte-identical across runs and matches the recorded golden file (SETTLEIQ-REQ-012).
2. Defect-generator test output: each named injected defect is asserted present with its expected type and location, and the count of defects injected equals the count asserted.
3. Contract-test output: the adapter passes the M1 `SourceAdapter` suite.
4. A recorded statement of generator provenance (version, seeds, schema version) for the dataset used.

**Scope note:** the master §5 row names "Stripe/Adyen-shaped generators", while `SETTLEIQ-DEC-001` §Q1 recommends Stripe-only for the first build and `02_PROBLEM_AND_USE_CASES.md` §5.2 item 5 excludes Adyen from the first build. **[RESOLVED 2026-10-28: the master §5 M2 row has been corrected to "Stripe-shaped" generators, with the frozen `SourceAdapter` interface named as the deliverable rather than the adapter count.]** This milestone's generator scope therefore follows the Q1 recommendation: M2 delivers the Stripe-shaped generator only, with the adapter interface frozen so that an Adyen-shaped generator is additive rather than a rewrite.

**Dependencies:** M1 (frozen interface, canonical model, fixture format). Q1 governs whether an Adyen-shaped generator is in this milestone.

**Target role evidence (master §5: Data Infra, Backend):** Adapter and interface design, normalization of heterogeneous source shapes into a canonical model, golden-file testing, generator and fixture design with known injected faults.

### M3 — Settlement decomposer + charge-level reconciliation

**Status: NOT STARTED. Nothing is built.** No decomposition exists, no gross-to-net bridge has been constructed, and no fee attribution or FX conversion has been performed.

**Deliverable (PROPOSED):** Payout-to-constituent decomposition; the gross-to-net bridge (`02` §2.4) closed exactly in `decimal.Decimal`; FX conversion and fee attribution; per-constituent attribution recorded as attested or inferred with a confidence class (SETTLEIQ-REQ-006, REQ-007, REQ-009). Attested and inferred attributions are distinguishable in the record.

**Acceptance evidence required to close:**

1. Worked decomposition test with exact expected totals: for a fixed dataset the bridge closes exactly, and the expected constituent set, amounts, currencies, and attribution classes are asserted.
2. A test that a bridge which does not close exactly is reported with an explicit residual and a reason, never silently absorbed.
3. A test that constituents which cannot be attributed on available evidence are reported as unresolvable breaks rather than attributed by assumption.
4. A test that no binary float appears on the decomposition path, including FX conversion.

**Dependencies:** M1, M2. The residual-allocation and rounding convention is open question OQ-02, owned by `07_RECONCILIATION_ENGINE_SPEC.md`; M3 cannot close while that convention is undefined for a case that arises in its test data.

**Target role evidence (master §5: Financial Systems):** Gross-to-net bridging, fee and tax composition, FX conversion attribution, exact-decimal derivation with recorded residuals.

### M4 — Matching engine + typed discrepancy taxonomy

**Status: NOT STARTED. Nothing is built.** No rule set exists, no taxonomy exists, no match decision has been produced, and no confidence class has been assigned.

**Deliverable (PROPOSED):** Deterministic rule-based matching across processor, payout, and bank sides, operating on constituents rather than payout totals; confidence classification; ambiguous-case routing; the named typed discrepancy taxonomy with ageing and root-cause attribution (SETTLEIQ-REQ-007, REQ-008, REQ-012). Fail-closed behaviour: insufficient evidence yields an unresolvable break, never a guess, an approximation, or a silently absorbed difference.

**Acceptance evidence required to close:**

1. Injected-defect classification suite output in which **every class of the taxonomy is asserted** against at least one injected defect, and every injected defect is classified to the expected named type. No test may pass on a generic "mismatch" label.
2. A determinism test: identical inputs and identical rule version produce byte-identical output across repeated runs and across separate processes.
3. A provenance test: every match decision carries the fields used, the rule identifier and version that produced it, the confidence class, and the determinism guarantee.
4. A fail-closed test: a deliberately under-evidenced case yields an unresolvable break, and no output path exists by which it is stored or displayed as resolved.
5. A taxonomy-gap test: a difference fitting no named type is surfaced as a taxonomy gap, not forced into the nearest type (OQ-03).

**Dependencies:** M1, M3. OQ-01 (tie-breaking when two candidates are equally plausible) and OQ-03 (closed versus closed-with-explicit-unknown taxonomy) are owned by `07` and `08`; both bear directly on M4's acceptance evidence and must be settled before it closes.

**Target role evidence (master §5: Financial Systems, Backend):** Rule-engine design, deterministic matching with confidence classes, typed-discrepancy taxonomy design, provenance modelling.

**Sequencing note:** the master §5 order places M5 (audit journal) after M4. M4's match decisions are the journal's principal payload. M4's acceptance evidence shall therefore include a decision-record format that M5 can ingest without re-derivation, and no run shall be described as audited before M5 closes. Whether pre-M5 runs must be backfilled into the journal once it exists is recorded as open question OQ-09 in `15_RISKS_AND_NON_GOALS.md`.

### M5 — Append-only hash-chained audit journal, digests computed and verified

**Status: NOT STARTED. Nothing is built.** No journal exists, no chain has been constructed, no digest has been computed by the system, and no tamper-injection test has run.

**Deliverable (PROPOSED):** An append-only record store for discrepancy records and decisions, hash-chained such that each entry's digest is computed over the previous entry's digest and the current entry's canonical serialization; digests computed by the system and verified on read; a tamper-injection test proving that verification detects modification; a determinism test proving byte-identical output (SETTLEIQ-REQ-010, REQ-011, REQ-012).

**Acceptance evidence required to close:**

1. Tamper-injection test output: modifying a stored entry — payload field, stored digest, ordering, deletion, truncation — is detected by read-time verification, and the first divergence is reported with the offending entry identified. Each mutation class is a separate asserted case; the journal is never silently repaired.
2. A negative test that no public path accepts a caller-supplied digest; an insert attempting to set the digest is rejected.
3. Determinism test output: identical inputs and identical rule version produce byte-identical journal output.
4. Concurrency test output against PostgreSQL (not SQLite, per `06`): two simultaneous journal appends cannot interleave into an invalid chain.
5. A test that canonical serialization is unambiguous, and that where it is not, verification reports the journal unverifiable rather than assuming it valid (UC-7 failure mode).

**Dependencies:** M1, M4. Q3 governs the transaction boundary and locking semantics exercised by the concurrency test; Q3 is not ratified.

**Target role evidence (master §5: Backend, Financial Systems):** Append-only store design, canonical serialization, hash-chain construction, integrity verification, transactional write boundaries under concurrency.

### M6 — Metrics with published methodology

**Status: NOT STARTED. Nothing is built.** No instrumented count exists, no methodology is encoded, and no auto-match rate has been computed by anything.

**Deliverable (PROPOSED):** Instrumented counts for matched, unmatched-by-type, human-confirmed, and unresolvable outcomes; a measurement methodology encoded as code defining the denominator (what counts as an eligible record), the population in scope, the time window, and the treatment of AI-assisted or human-confirmed matches; a report that computes the auto-match rate from those counts (SETTLEIQ-REQ-013, REQ-014).

**Acceptance evidence required to close:**

1. Reproducible report across runs: the same figure reproduces from the same instrumented counts, asserted in a test.
2. The denominator definition, population, window, and human-confirmation treatment are documented **in code** and displayed inline with the figure, not only in prose.
3. A test that the rate is not stated in prose anywhere in the repository (SETTLEIQ-REQ-014).
4. A test that the published figure equals an independent recomputation from the recorded journal entries and count records by a second code path.
5. A test that an uncomputable rate — a missing count for a category the denominator includes — is reported as uncomputable with the missing count named, and that an ambiguous record class is excluded with the exclusion stated rather than silently absorbed (UC-4 failure modes).

**Dependencies:** M1, M4, M5. The time-window definition must be derived from recorded data timestamps rather than ambient clock readings; see open question OQ-07 in `15_RISKS_AND_NON_GOALS.md`.

**Target role evidence (master §5: All):** Instrumentation design, measurement-methodology authorship, honest metric definition, reproducibility of a published figure.

### M7 — REST + OpenAPI + investigation dashboard

**Status: NOT STARTED. Nothing is built.** No API exists, no OpenAPI document exists, no client exists, and no view has rendered.

**Deliverable (PROPOSED):** A REST surface with an OpenAPI contract over the engine, plus the minimum complete investigation interface. Under the Q4 recommendation the client carries exactly five views — run list, discrepancy queue, investigation detail, metrics, run history — each bound to a named use case (UC-1…UC-5), built as a TypeScript client inside this repository, served by this project's own API, with no styling system, component library, or design tokens until a functional requirement demands them. The client renders values read verbatim from API responses and does not recompute counts, rates, ages, or amounts.

**Acceptance evidence required to close:**

1. Contract-test output: the implemented API conforms to the OpenAPI document, recorded.
2. A running client against a live engine, exercised end to end over the seeded synthetic dataset, with recorded output demonstrating the workflow: a typed discrepancy produced, investigated against contributing records and provenance, and resolved or declared unresolvable.
3. URL-addressable view state, so an investigation state can be shared, reloaded, and reproduced by a third party (SETTLEIQ-REQ-003).
4. A test that no view renders a recomputed figure.

**Dependencies:** M1–M6. Q4 governs the view set and the "nothing decorative" constraint; Q4 is not ratified. The target-role wording in master §5 row M7 ("Backend, AI-eng") does not correspond to any AI component in the proposed architecture; see `15_RISKS_AND_NON_GOALS.md` §4 item 3.

**Target role evidence (master §5: Backend, AI-eng — with the inconsistency noted above):** Contract-first API design, OpenAPI discipline, a client that reads rather than recomputes, an interface that exposes provenance rather than hiding it.

### M8 — Conditional. Python-vs-C++17 benchmark

**Status: CONDITIONAL — NOT STARTED, NOT BUILT.** Its existence is not established. Its absence has not been recorded as a deletion, because no determination has been made. No benchmark has been run and no C++ code exists.

**Deliverable (PROPOSED, conditional):** If and only if all four gating conditions in `SETTLEIQ-DEC-001` §Q2 hold — (a) a specific identified workload whose measured runtime is dominated by computation rather than I/O, (b) a measured Python baseline on that workload with reproducible benchmarks, (c) a correctness-equivalence test proving the two implementations agree exactly on Decimal results including rounding, and (d) a demonstrated, not asserted, performance or systems-engineering benefit — then a C++17 hot-path benchmark comparing the two, reporting ns/op, allocations, correctness equivalence, and the honest limits of the comparison.

**Acceptance evidence required to close:** benchmark output; stated caveats; correctness-equivalence proof. All four conditions must be recorded as satisfied with their own evidence. A benchmark produced without (a) and (b) records a number and demonstrates no capability, and is a defect under SETTLEIQ-REQ-004.

**Deletion condition (OWNER-DEFINED):** if any of the four conditions does not hold, this milestone is deleted, not deferred, and the deletion is recorded with the failing condition named (ROAD-R07). It is never silently dropped from the list.

**Dependencies:** an identified compute-bound workload arising from M3 or M4; Q5 ratified first, because `SETTLEIQ-DEC-001` §Q2 records that Q2 cannot be finalised before Q5; the four conditions each with recorded evidence. If Q5 resolves to a non-quantitative primary emphasis, the C++ calculus changes and deletion is the expected outcome.

**Target role evidence (master §5: Quant Dev, HFT):** performance measurement discipline, allocation profiling, cross-language correctness equivalence. This is the only milestone that touches a second language, and it does not currently exist.

### M9 — Docker + single-command reproduction

**Status: NOT STARTED. Nothing is built.** No container definition exists, no single command exists, and no third-party reproduction has been performed.

**Deliverable (PROPOSED):** An environment definition in which `docker compose up` provisions the engine, the database, migrations, and deterministic seed fixtures, and a single documented command runs the full test suite — unit, property-based Decimal invariants, determinism, fault and tamper injection — together with the worked discrepancy investigation and the metrics report, emitting recorded output (SETTLEIQ-REQ-003, §4 of the master specification).

**Acceptance evidence required to close:**

1. A clean-clone reproduction performed by a third party with no access to the author, with the recorded output committed to the repository: clone, install, one command, and the recorded result.
2. The worked investigation classifies each of the five injected defects — phantom charge, amount break, fee misattribution, mid-payout refund, FX rounding carryover — to its expected named type, asserted rather than narrated.
3. The metrics report computes the auto-match rate from instrumented counts with the stated denominator, and the same figure reproduces across runs.
4. The M8 benchmark is included only if M8 exists.
5. Failures are reported as failures: a test that cannot run, a benchmark that cannot reproduce, or an investigation that cannot classify an injected defect is reported as such (SETTLEIQ-REQ-017).

**Dependencies:** M1–M7, and M8 if and only if M8 exists.

**Target role evidence (master §5: All):** reproducible environment definition, single-command demonstration, third-party verifiability.

---

## 4. Dependency Graph

Text form. An arrow reads "blocks": `A → B` means B may not start or close before A closes.

```
        OWNER ratification of Q1–Q5  (SETTLEIQ-DEC-001)
                     │
                     ▼
                   ┌───┐
                   │ M1 │  canonical data model, Decimal invariants,
                   └───┘  frozen SourceAdapter interface
                  │   │   │
        ┌─────────┘   │   └──────────┐
        ▼             ▼              ▼
     ┌───┐         ┌───┐          ┌───┐
     │ M2 │         │ M3 │◄─────────┘ (generator data feeds decomposition)
     └───┘         └───┘
   adapters +        │
   generators        ▼
                  ┌───┐
                  │ M4 │  matching engine + typed taxonomy + provenance
                  └───┘
                  │   │
        ┌─────────┘   └──────────┐
        ▼                        ▼
     ┌───┐                    ┌───┐
     │ M5 │                    │ M6 │  metrics + published methodology
     └───┘                    └───┘
        │                        │
        └───────────┬────────────┘
                    ▼
                  ┌───┐
                  │ M7 │  REST + OpenAPI + five-view dashboard
                  └───┘
                    │
                    ▼
                  ┌───┐
                  │ M9 │  Docker + single-command reproduction
                  └───┘

  M8 (conditional)
     ├─ requires: identified compute-bound workload from M3 or M4
     ├─ requires: Q5 ratified first (Q2 cannot be finalised before Q5)
     ├─ requires: all four Q2 conditions, each with recorded evidence
     └─ if any condition fails → M8 is DELETED with the failing condition
        recorded; M9 proceeds without it and its absence is stated
```

Additional blocking relations that the linear numbering does not show:

* **M1 blocks every other milestone** — the canonical model and the frozen adapter interface are the shared contract (SETTLEIQ-DEC-001 §Q1 non-negotiable condition).
* **M4's decision-record format blocks M5's payload** — the journal stores what the matcher decides; M5 cannot be closed without a format M4 produces.
* **M6 blocks M7's metrics view** — the dashboard renders figures the metrics component computes and does not recompute them.
* **M3 and M4 block M8's workload identification** — a compute-bound workload can only be identified after the engine's hot path exists to measure.
* **OQ-01, OQ-02, OQ-03 block M4 and M3 respectively** — open questions owned by `07`/`08` are blocking when their cases arise in acceptance data.
* **Q5 blocks Q2, and Q2 blocks M8** — ratification order is itself a dependency.

---

## 5. Release Gates

### 5.1 Gate 0 — implementation authorization

**SETTLEIQ-ROAD-R11 (OWNER-DEFINED):** Implementation is not authorized until the OWNER has marked Q1, Q2, Q3, Q4, and Q5 as **RATIFIED** in `12_DECISIONS_AND_OPEN_QUESTIONS.md`. Until that happens, this document is a plan, and the plan's requirements are PROPOSED.

What must be true before implementation is authorized at all:

1. Q1 ratified — processor scope for the first build, with the `SourceAdapter` interface condition accepted as written.
2. Q2 ratified — language architecture, including the explicit statement of whether C++17 is in or out of the first build. Q2 requires Q5 to be ratified first.
3. Q3 ratified — persistence choice, including the reproducibility properties and the concurrency-test requirement.
4. Q4 ratified — dashboard scope, including the five-view bound and the "nothing decorative" constraint.
5. Q5 ratified — target role and skill emphasis, since Q2's conditional gate depends on it.
6. The specification set those decisions depend on — `04`, `05`, `06`, `07`, `08`, `09`, `10`, `11` — authored to a state the OWNER accepts. `06`, `09`, and `10` exist; `04`, `05`, `07`, `08`, and `11` are not yet written.
7. The open questions that block the first milestones — OQ-01, OQ-02, OQ-03 — answered in their owning documents, with tests either way.

Nothing in items 1–7 is true as of 2026-10-28.

### 5.2 Gate 1 — when a component may be described as "implemented"

A single component may be described as implemented only when all of the following hold, and the description names the evidence:

1. The component's milestone is **CLOSED** per ROAD-R02: recorded executed output exists at a recorded path, produced by a recorded command, under a recorded rule version and environment.
2. The output is re-executable by a third party through the M9 single-command path (ROAD-R03).
3. Every requirement the component claims to satisfy has at least one recorded passing test that fails when the requirement is violated — including the negative cases (float rejection, tamper detection, fail-closed behaviour, determinism under a changed environment).
4. The component's documentation states its scope and its limits; documentation that describes capability the tests do not execute is a defect (SETTLEIQ-REQ-004, REQ-017).
5. No statement anywhere in the repository upgrades the component from implemented to complete, correct, accurate, fast, or production-ready without a corresponding measurement recorded under the measurement methodology.

A component that is described in prose as working without a recorded passing test is a defect (SETTLEIQ-REQ-016). Partial components are described by their status line, not by an adjective.

### 5.3 Gate 2 — when the project may be described as complete

The project may be described as complete only when:

1. M1 through M7 are CLOSED, and M9 is CLOSED with third-party clean-clone reproduction recorded.
2. M8 is either CLOSED with all four Q2 conditions evidenced, or DELETED with the failing condition recorded (ROAD-R06, R07). A project description that omits M8's status is incomplete.
3. Every OWNER-DEFINED requirement (SETTLEIQ-REQ-000 through REQ-017, SETTLEIQ-REQ-IND-01 through IND-04) has recorded passing evidence, not a prose restatement.
4. The auto-match rate is published by the system with its methodology, and the figure is not stated in prose anywhere in the repository.
5. The audit journal's integrity is demonstrated by a tamper-injection test, not asserted.
6. Determinism is demonstrated by byte-identical outputs across runs, processes, and environments, not asserted.
7. Every open question that blocked a milestone has been closed in its owning document, or is recorded as still open with the reason.

None of conditions 1–7 holds. The project is not complete and is not started.

### 5.4 Claims that are never available

Regardless of milestone state, the following are never available for SettleIQ:

* any competitive, market-gap, market-size, pricing, product-market-fit, or willingness-to-pay claim (SETTLEIQ-REQ-000, REQ-001);
* any claim that a named product lacks auditability, explainability, charge-level decomposition, or a published measurement methodology;
* any claim of live-money operation, real customer data, or real payment instruments;
* any auto-match rate stated in prose;
* any hash, digest, or benchmark figure written by hand rather than computed by the system.

---

## 6. Roadmap Requirements Register

| ID | Statement | Classification |
|---|---|---|
| SETTLEIQ-ROAD-R01 | Milestone set M1–M9 as enumerated in master §5; no renumbering, renaming, or addition without an OWNER amendment | OWNER-DEFINED |
| SETTLEIQ-ROAD-R02 | No milestone closes by prose; closure requires recorded executed output plus the producing command, rule version, and environment | OWNER-DEFINED |
| SETTLEIQ-ROAD-R03 | Every milestone's acceptance evidence is re-executable through the M9 single-command path | OWNER-DEFINED |
| SETTLEIQ-ROAD-R04 | A milestone may not close while a dependency is unclosed | PROPOSED |
| SETTLEIQ-ROAD-R05 | Implementation requires Q1–Q5 ratified | OWNER-DEFINED |
| SETTLEIQ-ROAD-R06 | M8 exists only if all four Q2 conditions hold with recorded evidence | OWNER-DEFINED |
| SETTLEIQ-ROAD-R07 | A failed M8 condition produces a recorded deletion naming the condition, never a silent omission | PROPOSED |
| SETTLEIQ-ROAD-R08 | Repository milestone state is authoritative for external reporting | OWNER-DEFINED |
| SETTLEIQ-ROAD-R09 | Target-role interpretations follow the Q5 recommendation and are not available until Q5 is ratified | PROPOSED |
| SETTLEIQ-ROAD-R10 | Every milestone carries an explicit status line; status values are NOT STARTED / IN PROGRESS / CLOSED / DELETED | PROPOSED |
| SETTLEIQ-ROAD-R11 | Implementation authorization conditions (Gate 0) as stated in §5.1 | OWNER-DEFINED |
| SETTLEIQ-ROAD-R12 | Per-component "implemented" claims satisfy Gate 1 and name their evidence | OWNER-DEFINED (restated from REQ-004, REQ-016) |
| SETTLEIQ-ROAD-R13 | Project-level "complete" claims satisfy Gate 2, including M8's explicit existence or recorded deletion | PROPOSED |

---

## 7. Explicit Statement of Status

Every milestone in this document is **NOT STARTED**. Nothing is built. No test has been executed, no benchmark has been run, no container has been built, no journal has been written, no rate has been computed, and no component has been closed. M8 is conditional and has neither been established nor deleted. This document states intended sequencing and intended acceptance conditions, and is subordinate to `SETTLEIQ-MASTER-SPEC-001`. Intent and implementation are never presented in the same register (SETTLEIQ-REQ-004).
