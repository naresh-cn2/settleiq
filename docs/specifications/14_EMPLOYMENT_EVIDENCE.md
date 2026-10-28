# 14 — Employment Evidence

**Document ID:** SETTLEIQ-EMP-001
**Title:** SettleIQ Employment Evidence — Requirement-to-Skill Mapping, Role Emphasis, and Honest Presentation
**Version:** 1.0.0
**Status:** PROPOSED — specification only; no implementation claimed
**Domain:** Skills-to-artifact mapping, interview readiness, role emphasis, presentation discipline
**Governing document:** `SETTLEIQ-MASTER-SPEC.md` (SETTLEIQ-MASTER-SPEC-001)
**Date:** 2026-10-28
**Canonical path:** `docs/specifications/14_EMPLOYMENT_EVIDENCE.md`
**Owner:** Bukya Naresh (CN2)
**Traces to:** SETTLEIQ-MASTER-SPEC-001 §1.2 (Purpose Classification), §2.1 (SETTLEIQ-REQ-000, REQ-004), §2.5 (REQ-016), §8 row 14; SETTLEIQ-DEC-001 Q5

---

## Document Control

### Purpose

This document maps SettleIQ's requirements and milestones to the engineering skills they exercise, to the implementation task that exercises each one, to the test or benchmark that verifies it, to the documentation it requires, to the artifact a hiring manager can be handed, and to the interview question the work prepares the candidate to answer. Its second purpose is negative and equally load-bearing: to state plainly which skills this project does **not** develop, so that the artifact is not presented as broader coverage than it has.

### Authority and classification convention

* **OWNER-DEFINED** — restated from a binding requirement of `SETTLEIQ-MASTER-SPEC-001` or `SETTLEIQ-DEC-001`.
* **PROPOSED** — recommended by this document; not binding until ratified.

Nothing in this document is implemented. Every skill listed in §5 is a skill this project is *intended* to exercise. No skill is claimed as demonstrated, because no test has run and no component exists (SETTLEIQ-REQ-004, REQ-016).

### What this document does not claim

No job listing, salary figure, hiring statistic, market-size figure, or employer name appears in this document. Role names used here are limited to those established in the governing documents: financial systems engineering, ledgering engineering, backend engineering, data infrastructure engineering, quantitative development, and low-latency systems engineering, plus the actor roles of `02` (reconciliation engineer, investigator, auditor/reviewer). No claim is made that SettleIQ competes with, substitutes for, or differs from any product (SETTLEIQ-REQ-000, REQ-001).

---

## 1. Purpose and Frame

**SETTLEIQ-EMP-R01 (OWNER-DEFINED):** The artifact's audience is a hiring manager evaluating candidates for financial-systems, ledgering, or backend engineering roles. Every skill claim in this document must be defensible as engineering evidence, not as positioning.

**SETTLEIQ-EMP-R02 (OWNER-DEFINED):** A skill is listed as developed only where a named test, benchmark, or recorded artifact verifies it. A skill that no test exercises is not listed in §5, and is listed in §6 instead.

**SETTLEIQ-EMP-R03 (PROPOSED):** The mapping in §3 is one table with a fixed seven-column schema, presented in sections that share identical columns so that no row can be read under a different column meaning.

**SETTLEIQ-EMP-R04 (PROPOSED):** Each row's "test or benchmark that verifies it" names a specific executed check, not a category of check. "Unit tests" is not an answer; "property test asserting Decimal round-trip through JSON boundary" is.

---

## 2. Role Emphasis and Its Status

**SETTLEIQ-EMP-R05 (OWNER-DEFINED, status):** The role emphasis recorded in `SETTLEIQ-DEC-001` §Q5 is **RECOMMENDED, awaiting ratification**. It is not decided. No statement in this document may present it as a settled target.

The recommendation reads:

| Frame | Emphasis | Status |
|---|---|---|
| Financial systems and ledgering engineering | **Primary** | RECOMMENDED — awaiting OWNER ratification (Q5) |
| Backend engineering | Supporting frame | RECOMMENDED — awaiting OWNER ratification (Q5) |
| Data infrastructure engineering | Secondary, not pursued simultaneously | RECOMMENDED — awaiting OWNER ratification (Q5) |
| Quantitative development / low-latency systems | Alternative centre of gravity; would replace rather than supplement the primary emphasis, and reopens Q2 | RECOMMENDED as an alternative — awaiting OWNER ratification |

**SETTLEIQ-EMP-R06 (PROPOSED):** `SETTLEIQ-DEC-001` §Q5 records the research findings the recommendation rests on: job descriptions examined describe settlement reconciliation, discrepancy investigation, and ledgering as the work itself; the reconciliation domain was found to span the roles investigated; ledger domain was identified as the rarest differentiator among the candidates; open-source presence was listed as a plus in at least one job description; and data-infrastructure and backend roles value pipeline, SQL, and testing depth. These findings are carried as research record, not as facts about SettleIQ's execution, and they are not restated here as claims about any employer or market.

**SETTLEIQ-EMP-R07 (PROPOSED):** Because Q2's conditional C++ gate depends on Q5, and Q5 is unratified, the quantitative-development row above is genuinely open rather than merely deferred. Until Q5 is ratified, no artifact may present C++ work as part of SettleIQ's skill coverage.

---

## 3. Requirement-to-Skill Mapping

One table, seven columns, presented in sections that share the columns exactly. Every row's verification column names a specific check. Every row is currently **unexecuted**; the artifact column names an artifact that will exist only when its milestone closes.

### 3.1 Frame, independence, and honesty requirements

| Requirement / milestone | Technical skill demonstrated | Implementation task | Test or benchmark that verifies it | Documentation required | Artifact a hiring manager can be shown | Interview question the work prepares the candidate to answer |
|---|---|---|---|---|---|---|
| SETTLEIQ-REQ-IND-01…04 (independence, no cross-repository reuse) | Requirement ownership; distinguishing inherited from original work; specification as an engineering artifact | Write the specification set with every requirement owned and testable in-repository; record a decisions register instead of citing external authority | Review gate: every requirement carries a SettleIQ-owned ID and an in-repo justification; a documentation-consistency check fails any requirement citing an external governance document as authority | Master spec §1.1–1.3; `03_EVIDENCE_AND_RESEARCH_REGISTER.md` §4.2 | The specification set itself, with traceability from master requirement to subordinate document | "How do you keep a personal project's requirements owned rather than inherited, and why does that distinction matter?" |
| SETTLEIQ-REQ-000, REQ-001 (no commercial, competitive, market-gap claims) | Discipline in claim scope; separating evidence from positioning | Bind the non-claims in the master spec; add a gate that rejects prohibited claim vocabulary in artifacts | Repository scan asserting no artifact asserts a competitor capability gap, market gap, pricing, or product-market fit | Master spec §1.3; `03` §5.3 standing constraints | The non-claims list, and the gate that enforces it | "What would you refuse to claim about a project you built, and how would you enforce that in the repository?" |
| SETTLEIQ-REQ-002 (synthetic generator data only) | Data generation design; seeded reproducibility; fault injection by construction | Build a generator with fixed seeds, recorded version, and named injected defects | Fixture manifest test: same seeds and generator version reproduce the same input digest; defect-count test asserts injected count equals observed count | `06` fixture-generation contract; `13` M2 | The generator and its manifest, with the input digest of the demonstration dataset | "How do you make a synthetic dataset reproducible enough that a stranger can re-run your benchmark?" |
| SETTLEIQ-REQ-003 (third-party verifiability, one command) | Reproducible environment definition; documentation that a stranger can follow | Author the Compose environment and the single reproduction command covering tests, benchmark, and worked investigation | Clean-clone reproduction by a third party, output recorded in the repository | `13` §5.3; M9 acceptance | The reproduction command and its recorded output | "What does 'reproducible' mean operationally, and what breaks it?" |
| SETTLEIQ-REQ-004 (intent vs implementation registers) | Technical writing discipline; claim hygiene under pressure | Keep specifications, decisions, and test outputs in separate registers with explicit status lines | Documentation-consistency check: every implementation claim references an artifact path that exists | Every document's status line; `13` Gate 1 | The specification set alongside recorded test output — the two registers, visibly separate | "How do you stop a README from drifting ahead of the code?" |

### 3.2 Money, data model, and persistence (M1)

| Requirement / milestone | Technical skill demonstrated | Implementation task | Test or benchmark that verifies it | Documentation required | Artifact a hiring manager can be shown | Interview question the work prepares the candidate to answer |
|---|---|---|---|---|---|---|
| SETTLEIQ-REQ-005 (Decimal money, explicit context and rounding mode) | Exact-decimal arithmetic; rounding-mode semantics; knowing where binary float is and is not acceptable | Implement the Decimal money type with a single declared context and rounding mode, and route every amount through it | Property test: Decimal round-trip through domain, persistence, JSON, and API boundaries preserves exact value; a test feeding a float literal at the JSON boundary is rejected; a CI gate rejects float on monetary paths | `06` §1.1 (SETTLEIQ-DATA-R01, R02) | The money type, its context declaration, and the property-test output | "Why is `0.1 + 0.2 != 0.3` a payments defect and not a curiosity, and where does float sneak back in?" |
| M1 canonical data model (charge, payout, fee, refund, adjustment, FX, deposit, discrepancy) | Domain modelling; vocabulary alignment with a real settlement domain; immutability modelling | Implement the typed model, including superseding corrections rather than in-place updates | Property tests on model invariants; a test asserting a settled record cannot be mutated in place | `06` canonical model | The model definition and the invariant-test output | "How would you model a payment, a payout, and a refund so that history is reconstructable?" |
| Q3 (PROPOSED) — PostgreSQL with `numeric` columns, explicit scale, DB-level check | Relational schema design; constraint-based integrity; migration discipline | Author the schema, the scale constraint, the check constraint, and forward-only versioned migrations | Migration test: clean database reaches the declared schema version; a migration-graph test asserts forward-only and acyclic; a test asserts a non-numeric amount is rejected by the database, not only by application code | `06` migration policy | The migration set and the clean-database migration output | "What can a database enforce that application code cannot, and where have you relied on it?" |
| Q3 (PROPOSED) — concurrency: two simultaneous journal appends cannot interleave | Transaction boundaries; isolation-level reasoning; race-condition testing | Implement the journal append inside an explicit transaction with the required locking | Concurrency test against PostgreSQL (not SQLite) asserting an invalid chain cannot be produced by two simultaneous appends | `06` transaction boundaries | The concurrency test and its recorded output | "How do you prove a race does not exist rather than asserting it?" |
| Deterministic fixtures identified by input digest | Content addressing; deterministic generation | Generator with fixed seeds and recorded version; digest computed over the fixture set | Test: identical inputs produce an identical digest; re-running the generator produces byte-identical fixtures | `06` fixture contract | The fixture manifest and digest | "How would you identify a dataset by content rather than by name?" |

### 3.3 Decomposition and charge-level reconciliation (M3)

| Requirement / milestone | Technical skill demonstrated | Implementation task | Test or benchmark that verifies it | Documentation required | Artifact a hiring manager can be shown | Interview question the work prepares the candidate to answer |
|---|---|---|---|---|---|---|
| SETTLEIQ-REQ-006 (charge-level, not payout-level reconciliation) | Understanding why aggregate comparison fails; compensating-error reasoning | Implement the decomposer so a payout is a container of constituents, each individually matched | Worked decomposition test with exact expected totals; a compensating-error test showing two opposite-sign defects produce a non-zero net difference and are both surfaced | `02` §2.3–2.4; `07` decomposition | The worked decomposition output showing constituents, not totals | "Two errors cancel to zero at payout level. What does your design do about that?" |
| Gross-to-net bridge closing exactly in Decimal | Algebraic modelling of a netting process; residual accounting | Implement the bridge, the fee and FX attribution, and the residual rule | Test: the bridge closes exactly; a deliberately non-dividing case produces an explicit recorded residual, never an absorbed one | `07` bridge and residual convention (OQ-02 must be closed) | The bridge statement with recorded residuals | "How do you attribute fees that do not divide evenly across charges, and where does the remainder go?" |
| FX conversion attribution | Currency conversion modelling; derived-money derivation records | Implement FX conversion with a recorded derivation per conversion result | Test: every persisted FX result carries rule ID, inputs, precision, rounding mode, and residual handling | `06` R04 | The derivation records | "Which of these amounts is source data and which is derived, and how does the system tell them apart?" |
| Attested vs inferred attribution with confidence classes | Evidence grading; epistemic honesty in a data pipeline | Record whether each attribution came from processor attestation or engine inference | Test: an unattested case is recorded as inferred with a confidence class and is never presented as fact | `07` confidence classes | A mixed run's attribution records | "What is the difference between a fact and an inference in your data model?" |
| SETTLEIQ-REQ-009 (fail-closed) | Designing for the insufficient-evidence case | Make unresolvable the explicit outcome; remove every path that could store an unresolved state as resolved | Test: an under-evidenced input yields an unresolvable break; a negative test asserts no schema path can store it as resolved | `07` fail-closed behaviour | The unresolvable-break output | "What does your system do when it cannot decide, and how would it fail if it guessed?" |

### 3.4 Matching engine and typed discrepancies (M4)

| Requirement / milestone | Technical skill demonstrated | Implementation task | Test or benchmark that verifies it | Documentation required | Artifact a hiring manager can be shown | Interview question the work prepares the candidate to answer |
|---|---|---|---|---|---|---|
| SETTLEIQ-REQ-007 (provenance per match decision) | Explainability engineering; decision-record design | Persist fields used, rule ID and version, confidence class, and determinism guarantee per decision | Test: every persisted decision carries all four provenance elements; a decision lacking any element is rejected at write time | `08` provenance | A decision record with its full provenance | "What would you need to store for a reviewer to accept your match without re-deriving it?" |
| SETTLEIQ-REQ-008 (named typed discrepancies) | Taxonomy design; exhaustive classification; rejecting the generic label | Implement the taxonomy with ageing and root-cause attribution | Injected-defect classification suite asserting **every** class against at least one defect; a taxonomy-gap test asserting an unclassifiable difference is surfaced, not forced into the nearest type | `08` taxonomy (OQ-03 must be closed) | The taxonomy and the classification-suite output | "Why is 'mismatch' an unacceptable label, and what would your taxonomy be?" |
| Deterministic rule engine with confidence classes and ambiguous-case routing | Rule-versioning; determinism reasoning; routing under ambiguity | Version the rule set; route ambiguous cases rather than resolving them silently | Determinism test: byte-identical output across runs and processes for identical inputs and rule version; an ambiguous-input test asserts routing, not arbitrary selection | `07` rules, versions, confidence | Two byte-identical run outputs plus the ambiguous-case routing record | "How do you version rules so a result can be reproduced a year later?" |
| SETTLEIQ-REQ-012 (determinism tested, not asserted) | Determinism engineering: no ambient clocks, seeded randomness, ordered iteration, no unordered parallelism | Remove ambient inputs from the output path; seed every RNG; make iteration order total | Test: repeated runs byte-identical; runs under different `TZ`, different `PYTHONHASHSEED`, and a different host produce identical output; a fault-injection run asserting an ambient clock read is rejected | `11` determinism methodology | The determinism-test matrix output | "What breaks byte-identical reproduction in a Python program, and how do you test for it?" |

### 3.5 Audit journal integrity (M5)

| Requirement / milestone | Technical skill demonstrated | Implementation task | Test or benchmark that verifies it | Documentation required | Artifact a hiring manager can be shown | Interview question the work prepares the candidate to answer |
|---|---|---|---|---|---|---|
| SETTLEIQ-REQ-010 (append-only store) | Immutable-store design; supersession modelling | Implement an append-only store with no update or delete path | Negative test: every attempt to mutate or delete an existing entry is rejected; corrections are supersession records | `08` journal | The store's enforced-append-only behaviour in the test output | "How do you make a record un-editable without making the system unable to correct errors?" |
| SETTLEIQ-REQ-011 (hash chain, digests computed and verified on read) | Cryptographic digesting; canonical serialization; read-time verification | Compute each digest over the previous digest plus the canonical serialization of the current entry; verify on read | Tamper-injection test: mutation of a payload field, a stored digest, entry ordering, deletion, and truncation are each detected with the offending entry identified; a negative test asserts no public path accepts a caller-supplied digest | `08` chain construction and verification | The tamper-injection suite output — the single most inspectable artifact in the project | "How would you demonstrate that your audit log detects tampering, rather than claiming it does?" |
| Canonical serialization | Serialization determinism; ambiguity elimination | Define the canonical byte form for each entry type | Test: ambiguous serialization cases are detected and reported as unverifiable rather than assumed valid | `08` canonical form | The canonicalization definition and its test | "What makes a serialization canonical, and what happens when it is not?" |
| Determinism of the journal (REQ-012) | Determinism applied to a stateful component | Ensure chain construction is order- and environment-independent | Test: identical inputs and rule version produce byte-identical journal output | `11` | The byte-identical journal output | "A hash chain is stateful. How do you keep it deterministic?" |

### 3.6 Measurement methodology (M6)

| Requirement / milestone | Technical skill demonstrated | Implementation task | Test or benchmark that verifies it | Documentation required | Artifact a hiring manager can be shown | Interview question the work prepares the candidate to answer |
|---|---|---|---|---|---|---|
| SETTLEIQ-REQ-013 (documented methodology: denominator, population, window, human-confirmation treatment) | Measurement design; denominator reasoning; defining a metric so it is falsifiable | Encode the methodology as code: eligible-record definition, population scope, window derivation, human-confirmation treatment | Test: the methodology is displayed inline with the figure; a test asserts an ambiguous record class is excluded with the exclusion stated, and an uncomputable rate is reported with the missing count named | `09` metrics endpoint; methodology in code | The metrics report showing the figure beside its own methodology | "Define your auto-match rate so that I could falsify it." |
| SETTLEIQ-REQ-014 (rate computed by the system from instrumented counts; never stated in prose) | Instrumentation discipline; preventing a number from being hand-copied | Instrument the counts at the decision points; compute the rate only from them | Test: the published figure equals an independent recomputation from journal entries by a second code path; a repository scan asserts the figure does not appear in prose | `11` | The report and the recomputation cross-check | "How does a metric in a README become a lie, and how do you prevent it structurally?" |
| Human-confirmed vs automated vs unresolvable counted separately | Measurement of human-in-the-loop systems | Instrument the confirmation path distinctly from the automated path | Test: numerator, denominator, and exclusions reconcile to journal entry totals with no residual | `08`, `11` | The count reconciliation output | "If a human confirms a match, is that an automation rate of 100%? What is your denominator?" |

### 3.7 API, dashboard, and reproduction (M7, M9)

| Requirement / milestone | Technical skill demonstrated | Implementation task | Test or benchmark that verifies it | Documentation required | Artifact a hiring manager can be shown | Interview question the work prepares the candidate to answer |
|---|---|---|---|---|---|---|
| M7 — REST + OpenAPI over the engine | Contract-first API design; OpenAPI discipline; read-only reference surfaces | Implement the API against the spec; publish the OpenAPI document; generate client types from it | Contract-test output asserting the implementation conforms to the published document | `09` | The OpenAPI document and the contract-test output | "How do you keep a client and a server from drifting apart?" |
| M7 — five-view investigation client (Q4, PROPOSED) | Minimum-viable interface design; a UI that exposes evidence rather than decorating it | Build the five views bound to UC-1…UC-5, each rendering values read verbatim from API responses | End-to-end recorded run over the seeded dataset: a typed discrepancy produced, investigated against provenance, and resolved or declared unresolvable; a test asserting no view recomputes a displayed figure | `10` | The running client against a live engine, recorded | "What is the smallest interface that still shows an investigation?" |
| M9 — Docker + single-command reproduction | Reproducible environments; container composition; instruction-following precision | Compose engine, database, migrations, and fixtures; one command runs tests, benchmark, and worked investigation | Third-party clean-clone reproduction with recorded output; the five injected defects each classified to the expected named type | `13` §5.3 | The one command and its recorded output | "What is the difference between 'it works on my machine' and a reproducible run?" |
| SETTLEIQ-REQ-017 (the demonstration fails loudly) | Failure-mode honesty; defect surfacing | Report a test that cannot run, a benchmark that cannot reproduce, or an unclassifiable defect as a failure | Fault-injection tests recorded, including their failures | `11` | The recorded failure output, where failures exist | "Show me a run of your test suite that failed, and tell me what you did." |

### 3.8 Conditional benchmark (M8 — currently non-existent)

| Requirement / milestone | Technical skill demonstrated | Implementation task | Test or benchmark that verifies it | Documentation required | Artifact a hiring manager can be shown | Interview question the work prepares the candidate to answer |
|---|---|---|---|---|---|---|
| M8 (conditional on all four Q2 conditions) | Performance measurement methodology; allocation profiling; cross-language correctness equivalence | Identify a compute-bound workload, measure a Python baseline, implement a C++17 hot path, and prove exact Decimal equivalence including rounding | All four Q2 conditions evidenced: workload identified as computation-dominated, baseline measured reproducibly, correctness-equivalence test proving exact agreement including rounding, benefit demonstrated not asserted | `11` benchmark methodology; M8 caveats | Benchmark output with ns/op, allocations, equivalence proof, and stated limits | "How do you benchmark honestly, and when is a benchmark a number rather than a capability?" |
| M8 deletion path (if conditions fail) | Knowing when not to build something; recording a decision not to proceed | Record the deletion naming the failing condition | The deletion record itself, cross-referenced from the roadmap state | `13` §3 M8 | The recorded deletion | "What did you decide not to build, and why?" |

### 3.9 Cross-cutting engineering practice

| Requirement / milestone | Technical skill demonstrated | Implementation task | Test or benchmark that verifies it | Documentation required | Artifact a hiring manager can be shown | Interview question the work prepares the candidate to answer |
|---|---|---|---|---|---|---|
| SETTLEIQ-REQ-015 (modular, tested, documented, runnable, with an evolutionary path) | Modular design; testable component boundaries; writing for the next engineer | Structure components with stable interfaces; document each; keep the replacement path open | Component boundary test: each component runs against its interface in isolation; coverage of every OWNER-DEFINED requirement by at least one named test | Architecture document; component READMEs | The module layout with its interface tests | "How would a new engineer change one rule without breaking a test?" |
| Property-based testing of Decimal and determinism invariants | Property test design; invariant selection; shrinking and counterexample reading | Author the property suites the milestones name | Property-suite output with generated case counts and any shrunk counterexamples | `11` | The property-test output | "What property would you assert about money arithmetic, and how would you generate inputs that break it?" |
| Fault and tamper injection | Adversarial testing; thinking like the person who will break the system | Build the injection harness the milestones name | Each injection class asserted detected and reported, never silently repaired | `11` | The injection harness and its output | "How do you test that a safety property holds, not just that the happy path works?" |
| Specification discipline and requirement traceability | Requirements engineering; ID discipline; classification of claim states | Author and maintain the specification set with classification and traceability | Consistency check: every requirement classified; every subordinate requirement traces to a master requirement or an OWNER decision | The specification set | The specification set with its traceability columns | "How do you write a specification that another engineer can implement without asking you what you meant?" |

---

## 4. Role Emphasis in Detail

### 4.1 Primary — financial systems and ledgering engineering (RECOMMENDED, unratified)

Drawn from: charge-level settlement decomposition, gross-to-net bridging, exact-decimal ledgering with explicit rounding and residual recording, fee/tax/FX composition, typed discrepancy investigation with ageing and root-cause attribution, append-only hash-chained audit, and measurement methodology. This is where the project's centre of gravity sits, because the problems it takes on — decomposition, attribution, residual handling, integrity, and honest measurement — are the substance of settlement reconciliation rather than incidental to it.

### 4.2 Supporting frame — backend engineering (RECOMMENDED, unratified)

Drawn from: relational schema and migration discipline, transaction boundaries and concurrency, contract-first REST/OpenAPI design, a client that reads rather than recomputes, reproducible containerised environments, and property/fault-injection testing depth. These are required by the primary emphasis in any case; the frame costs nothing additional and is where most of the generalizable engineering craft is visible.

### 4.3 Secondary — data infrastructure engineering (RECOMMENDED, unratified, not simultaneous)

Drawn from: adapter and interface design, normalization of heterogeneous source shapes into a canonical model, generator and fixture design with content-addressed datasets, golden-file testing. The volume is synthetic and single-node, so this is pipeline and modelling craft rather than scale engineering (see §6).

### 4.4 Alternative emphasis — quantitative development / low-latency systems

`SETTLEIQ-DEC-001` §Q5 records that this is a legitimate target but a different centre of gravity, that pursuing it in addition splits focus, and that choosing it would reopen Q2. Its only expression in the current milestone set is the conditional M8, which does not exist unless the four Q2 conditions are met. No claim of quantitative-development coverage is available while Q5 is unratified.

---

## 5. Skills This Project Teaches

Stated as intended exercise, not as demonstrated achievement. Each item names the milestone that exercises it.

1. **Exact-decimal monetary modelling** — context, precision, rounding modes, residual allocation, and where binary float re-enters through boundaries. (M1)
2. **Domain modelling of a settlement lifecycle** — authorisation, capture, settlement, payout, refund, chargeback, adjustment, FX conversion, and the supersession of settled records. (M1)
3. **Gross-to-net decomposition and bridging** — inverting a netting process and making the inversion close exactly, with recorded derivations for every derived amount. (M3)
4. **Fee, tax, and FX attribution** — attributing a processor's costs and currency conversions across constituents, including the non-dividing case. (M3, subject to OQ-02)
5. **Deterministic rule engineering** — versioned rules, confidence classes, ambiguous-case routing, and determinism achieved by construction and proved by test. (M4)
6. **Taxonomy design** — building an exhaustive, named classification of failures and refusing the generic label, including an explicit unknown. (M4, subject to OQ-03)
7. **Provenance modelling** — recording the evidence behind a machine decision so a reviewer can accept it without re-deriving it. (M4, M5)
8. **Fail-closed design** — engineering the insufficient-evidence path as a first-class outcome rather than an exception. (M4)
9. **Append-only, hash-chained store construction** — canonical serialization, chain construction, computed-and-verified digests, and tamper detection proven by injection. (M5)
10. **Transactional integrity under concurrency** — explicit transaction boundaries and a test proving two simultaneous appends cannot corrupt a chain. (M5, subject to Q3)
11. **Measurement-methodology authorship** — defining a denominator, population, window, and human-confirmation treatment so a published figure is falsifiable, then computing it from instrumentation rather than asserting it. (M6)
12. **Property-based and fault-injection testing** — generating inputs that break invariants, and injecting failures to prove detection. (M1, M4, M5, M9)
13. **Relational schema and migration discipline** — `numeric` typing, scale and check constraints at the database level, forward-only versioned migrations, and deterministic seeding. (M1, subject to Q3)
14. **Contract-first API and client design** — OpenAPI as the source of truth, generated client types, and a client that renders rather than recomputes. (M7, subject to Q4)
15. **Reproducible environment definition** — a single command that brings up engine, database, migrations, fixtures, tests, benchmark, and a worked investigation, verified by a third party on a clean clone. (M9)
16. **Requirements and specification discipline** — requirement IDs, claim-state classification, traceability, and the separation of intent from implementation. (All)

---

## 6. Skills This Project Does NOT Teach — Requiring Separate Focused Practice

Stated plainly. Listing these is part of the artifact's honesty; each is a real gap in the proposed architecture, not a modest omission.

1. **Distributed systems.** The proposed architecture is a single-node, single-process system with one PostgreSQL instance. There is no replication, sharding, partitioning, consensus, distributed transaction, or network-partition handling. Nothing in the milestone set exercises any of them.
2. **Concurrency at scale.** The only concurrency work in the proposed architecture is one narrow test: two simultaneous journal appends must not interleave into an invalid chain. There is no lock-free programming, no high-throughput contention work, no thread-pool or async-scheduling engineering, and no reasoning about throughput under contention. One correct test is not concurrency engineering.
3. **A second language.** The proposed architecture is Python-only in the core. C++17 exists only inside the conditional M8, which requires all four Q2 gating conditions and may be deleted. Java is explicitly excluded (`SETTLEIQ-DEC-001` §Q2). Until M8 exists, no second language is exercised at all.
4. **Low-latency and high-frequency systems engineering.** M8, if it exists, is a benchmark reporting ns/op, allocations, equivalence, and its own limits. It is not kernel-bypass networking, cache-line engineering, lock-free data structures, jitter characterisation, or production latency work. A benchmark is not a latency-critical system.
5. **Machine learning or AI engineering.** Despite the phrase "AI-assisted" appearing in SETTLEIQ-REQ-013's methodology requirement, the proposed matching engine is deterministic and rule-based. There is no model, no training pipeline, no feature store, no evaluation harness, and no inference serving. Any implication that this project demonstrates AI engineering would be false. (Whether the methodology must define a treatment for a category the system never produces is open question OQ-08.)
6. **Data engineering at volume.** Ingestion is batch, synthetic, and generator-produced. There is no streaming, no partition-tolerant ETL, no backfill machinery at scale, no schema-evolution under load, and no data-quality framework beyond the injected-defect generator. The scale target itself is open question OQ-04.
7. **Production operations, SRE, and observability.** There is no deployment beyond Docker Compose on a single host, no alerting, no SLO or error-budget discipline, no incident process, no capacity planning, and no production telemetry pipeline. `docker compose up` is a demonstration environment, not an operations story.
8. **Cloud infrastructure engineering.** No Kubernetes, no Terraform or other infrastructure-as-code beyond the Compose definition, no managed-service integration, no networking or IAM design, no cost engineering.
9. **Security engineering.** There is no authentication, authorization, or user management in the first build (`02` §5.2 item 4). Hash-chaining is data integrity, not access control, and the project does no threat modelling of a deployed system, no secrets management, and no penetration testing.
10. **Front-end engineering depth.** The proposed client is browser-default rendering over five functional views with no styling system, no component library, no state framework, no build pipeline beyond what the requirement demands, and no responsive or mobile work. It is a functional observation surface, not front-end craft.
11. **Regulatory, compliance, and controls knowledge.** The project records auditability as an engineering property. It does not implement a controls framework, does not map to any reporting regime, and does not claim compliance with any standard. Compliance domain knowledge is separate.
12. **Product and user research.** The commercial frame was closed on 2026-10-27. There has been no buyer contact, no user interview, and no validation of any kind (`03` §5.4). Nothing here develops product-discovery skill.
13. **Organisational and process engineering.** No code review with peers, no on-call, no cross-team coordination, no incident retrospective, no mentoring. The project is a single-author artifact.
14. **Domain breadth beyond card-payment settlement.** The proposed processor scope is narrow. There is no ACH, wire, real-time-rail, crypto, or cross-border treasury work in the first build, and none is planned in it.

---

## 7. Honest Presentation of the Artifact

### 7.1 What may be claimed, once the corresponding tests have run and their output is recorded

Each of the following is available only in the form "X, evidenced by recorded output at path Y, produced by command Z". None is available now.

1. That SettleIQ reconciles at charge level, evidenced by the worked decomposition test with exact expected totals.
2. That SettleIQ's money handling is exact-decimal end to end, evidenced by property-test output and the boundary-rejection tests.
3. That SettleIQ classifies unmatched differences into named types, evidenced by the injected-defect classification suite asserting every class.
4. That SettleIQ's journal detects tampering, evidenced by the tamper-injection suite.
5. That SettleIQ reproduces byte-identically, evidenced by the determinism matrix across runs, processes, and environments.
6. That SettleIQ publishes its auto-match rate with a documented methodology computed from instrumented counts, evidenced by the report and the independent recomputation cross-check.
7. That a third party can reproduce all of the above on a clean clone with one command, evidenced by the recorded third-party reproduction.

### 7.2 What may never be claimed

1. That SettleIQ is a commercially viable, competitive, or differentiated product; that it fills a market gap; that it has product-market fit; anything about pricing, willingness to pay, or a go-to-market plan (SETTLEIQ-REQ-000, REQ-001).
2. That any named product lacks auditability, explainability, charge-level decomposition, or a published measurement methodology. Verified research establishes these are documented capabilities elsewhere; the practice SettleIQ demonstrates is demonstrated on itself.
3. That SettleIQ handles live money, real customer data, or real payment instruments (SETTLEIQ-REQ-002, REQ-001(6)).
4. That SettleIQ is production-ready, hardened, secure, or scalable. The demonstration environment is not a production environment, and no load, security, or operations claim exists.
5. That SettleIQ demonstrates distributed systems, concurrency at scale, low-latency engineering, machine learning, or a second language. See §6.
6. That SettleIQ's auto-match rate is high, or any value for it, stated in prose (SETTLEIQ-REQ-014).
7. That SettleIQ is complete. Completeness is defined by `13` §5.3 and is not met.
8. That any component works because a specification says it should (SETTLEIQ-REQ-004, REQ-016).

### 7.3 Presentation rules

**SETTLEIQ-EMP-R08 (OWNER-DEFINED):** Intent and implementation are never presented in the same register. A specification, a roadmap, or this document states intent. A test result, a benchmark, or a recorded reproduction states implementation. A portfolio entry, a README, or an interview answer that carries both without distinguishing them is a defect and must be corrected before it counts as evidence.

**SETTLEIQ-EMP-R09 (OWNER-DEFINED):** No completion claim is made without executed test output. A described component without a recorded passing test is presented by its status line — "not started", "in progress" — never by an adjective.

**SETTLEIQ-EMP-R10 (PROPOSED):** Where a skill claim rests on an unratified decision — Q1 processor scope, Q2 language architecture, Q3 persistence, Q4 dashboard scope, Q5 role emphasis — it is presented as conditional on that ratification, with the condition named. A conditional skill is not presented as coverage.

**SETTLEIQ-EMP-R11 (PROPOSED):** The artifact is presented with its exclusions attached. The honest reading of SettleIQ by a hiring manager includes §6 of this document. Presenting the project without its "does not teach" list is the presentation defect that SETTLEIQ-REQ-004 exists to prevent.

---

## 8. Interview Preparation Map

The work prepares the candidate to answer, with evidence in hand:

1. "Walk me through how a payout becomes a set of charges." (M3 — bridge, attribution, residual, derivation records)
2. "Two errors cancel. How does your system notice?" (M3/M4 — compensating-error test)
3. "Why is floating-point money a defect?" (M1 — property tests and boundary rejections)
4. "How do you make a rule engine reproducible a year later?" (M4 — rule versioning, determinism matrix)
5. "Show me a decision your system refused to make." (M4 — fail-closed test, unresolvable break)
6. "Prove your audit log detects tampering." (M5 — tamper-injection suite)
7. "Define your automation rate so I can falsify it." (M6 — methodology in code, inline with the figure)
8. "How does a metric in a README become a lie?" (M6 — instrumentation and the prose-scan gate)
9. "What does 'reproducible' mean operationally?" (M9 — third-party clean-clone reproduction)
10. "What did you decide not to build?" (M8 deletion record, §6 of this document)
11. "What would you do differently with a year more?" (§6 — the gaps, named rather than hidden)
12. "How do you keep documentation from drifting ahead of code?" (REQ-004 — the two-register discipline and the claims check)

---

## 9. Explicit Statement of Status

Nothing in this document is implemented. No milestone has closed, no test has been executed, no benchmark has been run, no skill listed in §5 has been demonstrated, and no artifact named in §3 exists. Every role-emphasis statement is conditional on Q5, which is unratified. This document maps intended work to intended evidence and is subordinate to `SETTLEIQ-MASTER-SPEC-001`.
