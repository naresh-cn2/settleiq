# 15 — Risks and Non-Goals

**Document ID:** SETTLEIQ-RISK-001
**Title:** SettleIQ Risk Register, Explicit Non-Goals, Known Open Questions, and Specification Defects Found While Writing
**Version:** 1.0.0
**Status:** PROPOSED — specification only; no implementation claimed
**Domain:** Risk register, non-goals, open questions, defect log
**Governing document:** `SETTLEIQ-MASTER-SPEC.md` (SETTLEIQ-MASTER-SPEC-001)
**Date:** 2026-10-28
**Canonical path:** `docs/specifications/15_RISKS_AND_NON_GOALS.md`
**Owner:** Bukya Naresh (CN2)
**Traces to:** SETTLEIQ-MASTER-SPEC-001 §1.3, §2.1–2.5, §4, §6, §8 row 15, §9; SETTLEIQ-DEC-001 OQ-01…OQ-05; SETTLEIQ-PROB-001 §5.2; SETTLEIQ-ROAD-001

---

## Document Control

### Purpose

This document does three things. It registers the risks that would make SettleIQ worthless as evidence, each with a mitigation that is verifiable rather than advisory. It states the project's non-goals explicitly, so that scope cannot be reintroduced by drift. It records the questions that remain open, and the contradictions and missing requirements found while authoring the roadmap and employment-evidence documents.

### Authority and classification convention

* **OWNER-DEFINED** — restated from a binding requirement of `SETTLEIQ-MASTER-SPEC-001` or `SETTLEIQ-DEC-001`.
* **PROPOSED** — recommended by this document; not binding until ratified.

### The rule that governs this register

**SETTLEIQ-RISK-R01 (OWNER-DEFINED):** A mitigation is not a mitigation unless it names a test, a gate, or a recorded check that **fails** when the mitigation fails. "Be careful", "review the code", "keep it in mind", and "the author will notice" are not mitigations and are recorded here as residual risk instead.

**SETTLEIQ-RISK-R02 (PROPOSED):** Every mitigation's verifying check shall produce recorded output when it runs and shall be wired into the M9 single-command path, so that a mitigation that stops running stops going unnoticed.

### Severity and likelihood scales

| Severity | Meaning |
|---|---|
| **Critical** | Invalidates the artifact as evidence if it occurs; the artifact becomes misleading |
| **High** | Requires substantial rework or invalidates a milestone's closure evidence |
| **Medium** | Degrades a claim or costs rework inside one milestone |
| **Low** | Cosmetic or recoverable inside a working session |

| Likelihood | Meaning |
|---|---|
| **High** | Expected to occur unless actively prevented |
| **Medium** | Plausible under normal working conditions |
| **Low** | Requires an unusual combination of circumstances |

---

## 1. Risk Register

### RSK-01 — Prose-vs-implementation drift

**Description.** Documentation, a README, or an interview answer describes a component as working when no test has executed. This is the specific defect the master specification names (SETTLEIQ-REQ-004, REQ-016) and the first row of its own risk register (SR-01). Drift is most likely exactly where a component feels finished and the last test has not yet been written.

**Severity: Critical. Likelihood: High.**

**Mitigation.** (a) Every document carries a status line, and no status line may contain an adjectival claim. (b) Milestone closure requires recorded executed output at a recorded path (SETTLEIQ-ROAD-R02). (c) Per-component "implemented" claims must name their evidence path (`13` §5.2). (d) A documentation-consistency check scans the repository for implementation claims and fails any claim that does not reference an existing artifact path. (e) The M9 reproduction path re-executes every closed milestone's evidence, so a claim with no runnable evidence breaks reproduction.

**Test or gate that proves the mitigation works.** The documentation-consistency check, run in the M9 single-command path, with a deliberately planted prose claim used as a negative fixture: the check must fail on the planted claim. A second negative fixture asserts that a claim naming an existing recorded artifact passes.

**Residual risk after mitigation.** None identified for claims inside the repository. Risk remains for statements made outside it — an interview, a message, a portfolio entry — where no gate can run. `14` §7.3 addresses this by rule, not by gate.

### RSK-02 — Fabricated or patterned hashes

**Description.** A journal digest is hand-written, patterned (repeating characters, sequential hex), copied from another entry, or otherwise not computed over the previous digest and the current canonical serialization. The master specification classifies this as a critical defect treated as fabricated evidence (SETTLEIQ-REQ-011, SR-02). The realistic failure mode is not malice but a test fixture or a transcript where a digest was typed rather than generated.

**Severity: Critical. Likelihood: Medium.**

**Mitigation.** (a) No code path accepts a caller-supplied digest; the digest column is not writable through any public interface. (b) Digests are computed only inside the append operation, over the previous digest plus the canonical serialization of the current entry. (c) Read-time verification recomputes the chain. (d) A digest-recomputation cross-check re-derives every digest in a recorded journal using a second, independent implementation of the digest function and asserts equality. (e) A static gate scans for hex-literal constants in the journal module and fails if any is not a documented test vector.

**Test or gate that proves the mitigation works.** The tamper-injection suite (RSK-16) proves detection. The digest-recomputation cross-check proves the stored chain is the computed chain. The hex-literal gate proves no digest was authored as a literal. A negative fixture asserting that an insert attempting to supply a digest is rejected proves the write path cannot be bypassed.

**Residual risk after mitigation.** A generator bug producing a *consistent* wrong digest would pass both the chain check and the recomputation cross-check if both used the same bug. This is not eliminated by the mitigations; it is reduced by the cross-check using an independently written digest function, and it is recorded as residual.

### RSK-03 — Float money entering through a dependency or a JSON boundary

**Description.** A binary floating-point value reaches a monetary path through JSON number parsing, an ORM or driver returning `float` for a `numeric` column, a third-party library, or a convenience cast. The master specification classifies any use of binary float on monetary values as a defect (SETTLEIQ-REQ-005, SR-03).

**Severity: High. Likelihood: High.**

**Mitigation.** (a) One declared Decimal context and rounding mode, reused everywhere, with a single constructor for money values. (b) A monetary-type wrapper that rejects `float` at construction and cannot be constructed from `float` implicitly. (c) JSON deserialization configured to parse numbers as strings, converted via `Decimal(str)` with a rejected-input path for anything that was a float literal. (d) A CI gate scanning monetary code paths for `float` usage, `float()` calls, and arithmetic against float-typed bindings. (e) Amount columns typed `numeric` with a database-level check, so the storage layer rejects non-decimal input independently of application code. (f) A pinned dependency manifest, with the pin's purpose recorded, so a silent dependency upgrade cannot change numeric behaviour.

**Test or gate that proves the mitigation works.** Property tests asserting exact value preservation across the domain, persistence, serialization, and API boundaries. Boundary tests feeding JSON containing a float literal and asserting rejection. A round-trip test through the database driver asserting the returned type is `Decimal`. The CI gate itself, exercised against a negative fixture that introduces a float on a monetary path.

**Residual risk after mitigation.** A dependency performing float arithmetic internally on a value it returns as a Decimal would not be caught by a type check. Detecting that requires value-level property tests over generated inputs, which the milestone set specifies; it is not fully eliminated.

### RSK-04 — Determinism broken by ambient clocks or unordered sequences

**Description.** Output that should be byte-identical across runs varies because of ambient time, timezone, dictionary or set iteration order, hash randomisation, unordered parallelism, floating-point summation order, or an auto-increment identifier. The master specification requires determinism to be tested, not asserted (SETTLEIQ-REQ-012).

**Severity: Critical. Likelihood: High.**

**Mitigation.** (a) No output path reads an ambient clock; all timestamps are inputs or are derived from recorded data. (b) Every RNG is explicitly seeded and its seed recorded in the run record. (c) All iteration is over totally ordered collections; no set or dict iteration reaches an output. (d) Either no parallelism, or parallelism whose reduction order is fixed and asserted. (e) All arithmetic is exact Decimal, so summation order cannot change a value. (f) The measurement methodology's time window is derived from recorded data timestamps, never from wall-clock readings (see OQ-07). (g) Run identity is content-addressed (input digest, rule version, schema version), not time-stamped.

**Test or gate that proves the mitigation works.** A determinism matrix: the same input and rule version executed twice in the same process, twice in separate processes, under a different `TZ`, under a different `PYTHONHASHSEED`, on a different host, and after a container restart, producing byte-identical output each time. A negative fixture that injects an ambient clock read or an unordered iteration into a copy of the pipeline and asserts the test detects the resulting divergence.

**Residual risk after mitigation.** Host-level differences not controlled by the matrix (for example, a library version difference) show up as the matrix failing, which is the intended behaviour. Library drift is bounded by the dependency pin from RSK-03.

### RSK-05 — Scope creep back toward commercial positioning

**Description.** An artifact acquires a market-gap claim, a pricing statement, a competitor comparison, or a go-to-market framing. The master specification makes these binding non-claims (SETTLEIQ-REQ-000, REQ-001, SR-04) and the research register records the standing constraints that produced them (`03` §5.3).

**Severity: High. Likelihood: Medium.**

**Mitigation.** (a) REQ-001 is binding and this register carries it. (b) A repository scan rejects claim vocabulary and framing patterns — competitor-capability assertions, market-size or gap language, pricing figures, willingness-to-pay, go-to-market — in any artifact, including READMEs and generated documentation. (c) New artifacts are added only through the specification hierarchy in master §8, each with a defined domain of authority; there is no slot for a positioning document. (d) Employment framing is asserted positively in `14`, so the slot that a commercial claim would otherwise fill is occupied.

**Test or gate that proves the mitigation works.** The claim-vocabulary scan run in the M9 path, with negative fixtures: a planted market-gap sentence, a planted pricing figure, and a planted "unlike [product]" sentence must each be rejected. The scan's patterns are themselves an artifact a reviewer can read, which is the point — the rule is inspectable rather than remembered.

**Residual risk after mitigation.** A claim made in conversation or in an external profile is not gated. `14` §7.2 addresses this by rule.

### RSK-06 — Abandonment mid-build

**Description.** A large partially-built codebase accumulates with no milestone closed and no demonstrable evidence, which is the failure mode the master specification names (SR-05). The realistic trigger is starting with the hardest component instead of the first one.

**Severity: High. Likelihood: Medium.**

**Mitigation.** (a) Milestones are ordered so that each produces recordable evidence before the next begins (`13` §3). (b) A milestone may not start while a dependency is unclosed (SETTLEIQ-ROAD-R04), which prevents the parallel half-built state. (c) Implementation is not authorized until Q1–Q5 are ratified (SETTLEIQ-ROAD-R05), which removes the most common cause of an abandoned first attempt — building against unratified decisions and then rebuilding. (d) The repository's milestone state is the single source for external reporting (SETTLEIQ-ROAD-R08), so progress is visible rather than private.

**Test or gate that proves the mitigation works.** A sequencing gate that reads the recorded milestone state and refuses to mark a milestone started or closed while a dependency is unclosed; the gate is itself tested with a state fixture that violates the ordering and must be rejected. This proves the ordering discipline holds. It does not prove abandonment will not occur, and no test can.

**Residual risk after mitigation.** Abandonment is a human risk. The mitigation bounds the blast radius to the milestones already closed and their evidence; the loss is time, not the artifact's integrity. Recorded as residual.

### RSK-07 — Over-claiming inside the measurement methodology itself

**Description.** The methodology defines its denominator, population, window, or human-confirmation treatment in a way that flatters the result: excluding the hardest record classes, counting human-confirmed matches inside the automated numerator, choosing a window that contains the easy runs, or defining "eligible" so narrowly that the population is trivial. The master specification requires the methodology to be stated explicitly and the rate to be computed by the system (SETTLEIQ-REQ-013, REQ-014).

**Severity: Critical. Likelihood: Medium.**

**Mitigation.** (a) The methodology is code, not prose; the denominator is a named predicate over the record model. (b) Denominator, population, window, and human-confirmation treatment are rendered inline with the figure, so the denominator cannot be separated from the number it produced. (c) Human-confirmed, automated, and unresolvable outcomes are separate instrumented counts; a human confirmation never enters the automated numerator. (d) Every excluded record class is enumerated in code and carried into the report with the reason for its exclusion. (e) The rate is never stated in prose anywhere in the repository (REQ-014), so there is no prose figure to adjust around. (f) An uncomputable rate is reported as uncomputable with the missing count named, and an ambiguous class is excluded with the exclusion stated.

**Test or gate that proves the mitigation works.** (a) A reconciliation test asserting the numerator, denominator, exclusions, and each instrumented category sum to the recorded journal entry totals with zero residual. (b) A cross-check test asserting the published figure equals a recomputation from the journal by a second code path. (c) A repository scan asserting the computed figure does not appear as prose. (d) A methodology-completeness test asserting that every record class in the model is classified by the denominator predicate as eligible or excluded-with-reason, with no class left unclassified.

**Residual risk after mitigation.** A methodology can be defensible and still be a choice among several defensible definitions. The mitigation makes the choice visible and the arithmetic auditable; it does not make the choice unique. Recorded as residual, and as the reason `14` §2 keeps the emphasis on falsifiability.

### RSK-08 — The measurement methodology being gamed by its own author

**Description.** A specific case of RSK-07 and harder: the author tunes the denominator, the exclusion list, or the window until the figure looks good, and the artifact then presents a laundered number. The research register records the standing rule that a vendor's failure to publish a methodology does not prove its software lacks auditability, and the corresponding rule runs against SettleIQ: SettleIQ must not characterise anyone else's practice, and must not launder its own (`03` §3, §4.3).

**Severity: Critical. Likelihood: Medium.**

**Mitigation.** (a) The methodology is versioned with the run record, so a definition change between two runs is visible as a rule-version difference, not as an improvement. (b) The rate is computed from journal-derived counts, which are produced by the decision path and are not editable after the fact; a denominator change cannot retroactively alter recorded counts. (c) Third-party reproduction (SETTLEIQ-REQ-003) means a stranger recomputes the figure from the journal under the recorded methodology version; a methodology tuned to flatter produces a figure the stranger can recompute and interrogate. (d) The methodology-completeness test (RSK-07) forces every unexcluded class to be declared. (e) Any change to the denominator predicate requires a rule-version increment and a recorded reason, and the report shows both versions when a comparison is drawn.

**Test or gate that proves the mitigation works.** A methodology-version test: two runs of the identical input under the identical methodology version produce the identical figure, and a run under a changed methodology version reports the change rather than a silently different number. A recomputation test by a stranger on a clean clone (M9) is the external half of this gate; the internal half is the journal-derived count reconciliation.

**Residual risk after mitigation.** Determination by the author is not eliminated by any mechanism inside the artifact. It is mitigated by making the definition, the version, the counts, and the arithmetic independently inspectable, and by `14` §7.2 forbidding the presentation of the figure without its methodology attached.

### RSK-09 — A difference forced into the nearest named type, or labelled generically

**Description.** The taxonomy is closed; a difference arrives that fits no class; the engine either labels it "mismatch" or forces it into the nearest type. Both violate SETTLEIQ-REQ-008. The master specification requires the taxonomy to be explicit, exhaustive, and tested, and `02` UC-2 names the taxonomy gap as a failure mode to surface rather than absorb.

**Severity: High. Likelihood: Medium.**

**Mitigation.** (a) The taxonomy decision — closed versus closed-with-explicit-unknown — is settled in `08` (OQ-03) with tests either way; the recommendation is closed-with-explicit-unknown. (b) An unclassifiable difference produces an explicit taxonomy-gap outcome, never a nearest-type assignment and never a generic label. (c) A repository scan asserts the string "mismatch" is not used as a classification label anywhere in code or output. (d) Fail-closed behaviour (REQ-009) applies to classification as well as matching.

**Test or gate that proves the mitigation works.** A taxonomy-gap test: a deliberately unclassifiable difference yields an explicit taxonomy-gap outcome and an unresolvable break, not a nearest type. A coverage test asserting every class in the taxonomy is exercised by the injected-defect suite (M4 acceptance). A scan asserting "mismatch" never appears as a label.

**Residual risk after mitigation.** If the explicit-unknown class is over-used, the taxonomy degrades in practice while passing its tests. This is visible in the published per-type counts, which is the honest defence rather than a gate.

### RSK-10 — A residual silently absorbed

**Description.** A fee split, a rounding remainder, or an FX carryover that does not divide evenly is quietly distributed so the bridge closes, with no record that a residual existed and no rule governing where it went. `02` §2.4 and §6 (FM-P5) name this failure mode, and OQ-02 records the decision as open.

**Severity: High. Likelihood: High.**

**Mitigation.** (a) OQ-02 is settled in `07` — residual allocation, largest-remainder versus deterministic last-item absorption — with tests either way, before M3 closes. (b) Every derived monetary value carries a derivation record: rule ID and version, contributing inputs, context precision, rounding mode, and residual handling (SETTLEIQ-DATA-R04). (c) The bridge must close exactly; a rule that closes it only by absorbing an unrecorded residual is rejected. (d) An undefined rounding convention at runtime is reported as an unhandled case, never invented mid-run (`02` UC-6).

**Test or gate that proves the mitigation works.** A non-dividing-split test: a payout whose fees do not divide exactly across charges produces an explicit residual record with the allocation rule and its version named, and the recorded bridge closes exactly. A negative fixture asserting that an absorbed-but-unrecorded residual fails the test.

**Residual risk after mitigation.** The allocation rule is a choice; the choice is recorded and versioned, which is the available mitigation.

### RSK-11 — Adyen (or any second source) introduced before the core is proven

**Description.** Scope widens mid-build: a second adapter is started, the decomposer is bent toward temporal reconciliation, and the first build loses the narrower problem it was scoped to demonstrate. The master §5 M2 row's wording and the Q1 recommendation are in tension here; see §4 item 2 of this document.

**Severity: High. Likelihood: Medium.**

**Mitigation.** (a) The `SourceAdapter` interface is frozen at M1 before either adapter is written (SETTLEIQ-DEC-001 §Q1, non-negotiable). (b) A gate asserts that adding a second adapter passes the M1 contract suite with zero diff in engine files; an adapter that requires engine changes is evidence the interface was wrong, and is recorded as a specification defect rather than absorbed. (c) Ratification of Q1 fixes the first build's processor scope; a scope change is an OWNER decision recorded in `12`, not a working decision.

**Test or gate that proves the mitigation works.** The zero-diff adapter gate, exercised with a second adapter as the test subject (a test adapter may be built even if Adyen itself is out of scope). The gate must fail when the second adapter's contract compliance is achieved by modifying engine code.

**Residual risk after mitigation.** A second *problem axis* (temporal reconciliation) can be introduced through rule design rather than through an adapter. That is a scope decision, gated by Q1 ratification rather than by this test.

### RSK-12 — External progress reporting drifting from repository state

**Description.** A roadmap, a status update, or a conversation reports progress that the repository does not support. The master specification makes the repository authoritative for external reporting and requires external reporting to match it (§7).

**Severity: Medium. Likelihood: Medium.**

**Mitigation.** (a) External progress statements are generated from the repository's milestone state, never authored independently. (b) The M9 reproduction path emits the current milestone state as part of its recorded output, so the state is itself an artifact with a recorded path. (c) The status lines are exactly the four permitted values (SETTLEIQ-ROAD-R10), so a generated statement cannot contain an adjective that the state does not support.

**Test or gate that proves the mitigation works.** The emitted milestone state in the M9 recorded output is the artifact; a consistency check asserts that any status statement in the repository matches the state file exactly.

**Residual risk after mitigation.** Statements made outside the repository in real time are not gated. Mitigated by rule (`13` ROAD-R08) and by keeping the state trivially easy to quote.

### RSK-13 — Research or third-party material promoted into a requirement or a claim

**Description.** A vendor's documented capability, a pricing figure, or a job-description phrase becomes a SettleIQ requirement or a comparative claim. The research register records the standing constraints that produced the non-claims (`03` §5.3) and the rule that research is evidence, never a requirement (`03` §4.2, §6).

**Severity: High. Likelihood: Medium.**

**Mitigation.** (a) No SettleIQ requirement may cite an external governance document as authority (SETTLEIQ-REQ-IND-04); every requirement is restated as SettleIQ's own and owned here. (b) The claim-vocabulary scan from RSK-05 covers comparative framing. (c) Evidence classes are carried with every claim that remains in the register, and class B/C entries are marked as non-load-bearing. (d) This document's register is a register of risk, not of evidence; it cites no external source.

**Test or gate that proves the mitigation works.** A requirement-provenance check asserting every requirement in the specification set carries either a SettleIQ-owned master requirement ID or an explicit OWNER decision reference, and that no requirement's justification field cites an external repository or governance document.

**Residual risk after mitigation.** Paraphrase of a competitor's capability in a favourable or unfavourable direction can pass a vocabulary scan. The structural defence is `14` §7.2's rule alongside REQ-001.

### RSK-14 — Real-data mode entering the artifact

**Description.** A real credential, a real bank export, or a real customer record reaches the engine — through a "just for testing" import, a sample file, or a convenience adapter. SETTLEIQ-REQ-002 forbids it, and `03` §5.4 records that no buyer or real data contact exists.

**Severity: High. Likelihood: Low.**

**Mitigation.** (a) Ingestion accepts only generator-produced input carrying a synthetic provenance marker; an input without it is refused. (b) No credential, bank-connection, or payment-rail code exists in the first build. (c) The demonstration dataset is fixed by input digest, and the digest is recorded. (d) OQ-05 keeps the question of a real-data mode open and unanswered rather than assumed.

**Test or gate that proves the mitigation works.** An ingestion test asserting that a hand-crafted input lacking the synthetic provenance marker is refused with a named error, and that every record in the demonstration dataset carries the marker. A repository scan asserting no connection or credential code exists outside the generator.

**Residual risk after mitigation.** If a real dataset were hand-edited to carry the marker, the test would not catch it. This is a trust boundary the artifact cannot enforce on itself; it is recorded as residual.

### RSK-15 — Benchmark theatre

**Description.** A benchmark is produced because a benchmark is expected, on work that is not compute-bound, and is then presented as a capability. `SETTLEIQ-DEC-001` §Q2 states the case directly: under those conditions a benchmark would demonstrate a number, not a capability, and would violate the spirit of SETTLEIQ-REQ-004.

**Severity: High. Likelihood: Medium.**

**Mitigation.** (a) M8 exists only if all four Q2 conditions hold, each with recorded evidence (SETTLEIQ-ROAD-R06). (b) A failed condition produces a recorded deletion naming the condition (SETTLEIQ-ROAD-R07); M8 is never silently dropped. (c) A benchmark cannot be claimed without an identified computation-dominated workload and a measured Python baseline, both recorded before the C++ work begins.

**Test or gate that proves the mitigation works.** The four-condition gate evidence itself: workload identification with a measurement showing computation dominance, the reproducible baseline, the correctness-equivalence test proving exact agreement including rounding, and a demonstration of benefit. Absent any one, the deletion record is the required output. A negative case: a synthetic "no compute-bound workload exists" determination must produce the deletion record and must prevent M9 from expecting a benchmark.

**Residual risk after mitigation.** Condition (d) — a meaningful benefit demonstrated — is a judgement. The recorded measurement and the stated caveats make the judgement inspectable.

### RSK-16 — A tamper test that only checks the tamper it expects

**Description.** The tamper-injection test mutates one field in one way, passes, and creates false confidence that the journal detects tampering. A different mutation — a reordering, a deletion, a truncation, a digest-only change — goes undetected while the suite reports success.

**Severity: Critical. Likelihood: Medium.**

**Mitigation.** (a) The tamper-injection suite is table-driven over mutation classes: payload field modification, stored-digest modification, entry reordering, entry deletion, chain truncation, entry insertion, and canonical-serialization ambiguity. (b) Each case asserts both detection and correct reporting of the first divergence with the offending entry identified. (c) The suite runs on a recorded journal with a recorded digest chain, so the mutation targets are reproducible. (d) Read-time verification recomputes every digest rather than checking a stored summary.

**Test or gate that proves the mitigation works.** The suite itself, recorded, with one asserted case per mutation class. A negative fixture asserting that a naive single-field check would pass on a reordering — demonstrating that the broader suite is necessary, not decorative.

**Residual risk after mitigation.** A mutation that preserves the chain's arithmetic (for example, a simultaneous rewrite of a payload and its digest with a correctly recomputed chain) is detection of *tampering that broke the chain*, not of rewriting the whole store. The artifact does not claim protection against wholesale reconstruction with a valid recomputed chain, and `14` §7.2 records that exclusion.

### RSK-17 — Chain corruption under concurrent append

**Description.** Two journal appends interleave and produce a chain in which an entry's "previous digest" does not exist, is duplicated, or was superseded, leaving a chain that validates locally and is globally invalid. `SETTLEIQ-DEC-001` §Q3 makes this a required property with a required test.

**Severity: High. Likelihood: Medium.**

**Mitigation.** (a) The append happens inside an explicit transaction boundary with the locking required to serialise chain extension. (b) The previous-digest link is resolved inside the transaction, not read beforehand. (c) The concurrency test runs against PostgreSQL, not SQLite, because `06` forbids using SQLite to validate properties PostgreSQL enforces.

**Test or gate that proves the mitigation works.** The concurrency test: two simultaneous appends cannot produce an invalid chain; the resulting chain validates on read; and the run record shows both entries present with distinct chain positions.

**Residual risk after mitigation.** The test proves the two-append case at the tested isolation level. Broader concurrency is out of scope (see `14` §6 item 2).

### RSK-18 — Destructive migration or schema drift

**Description.** A migration drops or rewrites data, or a schema change is applied by hand to one environment and not another, so the recorded evidence cannot be reproduced from a clean database. `SETTLEIQ-DEC-001` §Q3 requires forward-only, versioned, non-destructive migrations.

**Severity: High. Likelihood: Medium.**

**Mitigation.** (a) Forward-only versioned migrations; no down-migration that destroys data. (b) Schema version recorded in the run record, so a result is tied to the schema that produced it. (c) A clean-database reproduction path: migrations applied from scratch reach the declared version. (d) Deterministic seeding by generator version and fixed seeds, identified by input digest.

**Test or gate that proves the mitigation works.** A migration test applying every migration from scratch on a clean database and asserting the declared schema version and the declared constraint set, including the `numeric` scale constraint and the non-numeric rejection check. A migration-graph test asserting the graph is acyclic and append-only.

**Residual risk after mitigation.** Non-destructive migrations can still lose information by encoding a wrong assumption; that is a design risk, not a mechanical one.

### RSK-19 — Open questions closed by assertion

**Description.** OQ-01 through OQ-05, or any question raised later, is marked resolved because a document says so rather than because a design decision was made and tested. The master specification states that no question is marked resolved until the OWNER ratifies it, and `12` records the same convention.

**Severity: Medium. Likelihood: Medium.**

**Mitigation.** (a) Each open question has a named owning document (`12` records the owner for each). (b) The milestone that depends on an open question cannot close while it is open (SETTLEIQ-ROAD-R04's dependency rule, extended to questions). (c) A question is closed by a recorded decision plus a test either way, never by a status change alone.

**Test or gate that proves the mitigation works.** A gate reading the open-question register and the milestone state, asserting that no milestone marked closed depends on a question still marked open. Negative fixture: a state pair violating this must be rejected.

**Residual risk after mitigation.** A question can be closed by a decision that is wrong. That is not a documentation failure.

### RSK-20 — Specifications authored against unratified decisions, then rebuilt

**Description.** Subordinate specifications — or implementation — proceed as though Q1–Q5 were settled, so that ratification produces rework or an implementation that contradicts the ratified decision. One instance of this defect occurred and has been corrected: `02` §5.1 described the five decisions as "OWNER-verified" while `12` marks all five RECOMMENDED awaiting ratification. See §4 item 1 of this document for the record and its resolution.

**Severity: High. Likelihood: High.**

**Mitigation.** (a) The classification convention: any requirement resting on Q1–Q5 is PROPOSED, not OWNER-DEFINED. (b) Implementation is not authorized until Q1–Q5 are ratified (SETTLEIQ-ROAD-R05). (c) A consistency check asserts that no document describes a Q1–Q5-dependent decision as ratified or OWNER-verified while `12` records it as RECOMMENDED.

**Test or gate that proves the mitigation works.** The consistency check, with negative fixtures drawn from the existing `02` §5.1 wording, must reject the "OWNER-verified" phrasing while `12` records RECOMMENDED. This gate is what makes the defect in §4 item 1 detectable rather than merely noted.

**Residual risk after mitigation.** Wording that implies ratification without using the forbidden words can pass the check. The check's patterns are inspectable and extendable for exactly this reason.

### Register summary

| ID | Risk | Severity | Likelihood | Verifying gate or test |
|---|---|---|---|---|
| RSK-01 | Prose-vs-implementation drift | Critical | High | Documentation-consistency check with negative fixtures; M9 re-execution |
| RSK-02 | Fabricated or patterned hashes | Critical | Medium | Tamper-injection suite; digest recomputation cross-check; hex-literal gate |
| RSK-03 | Float money via dependency or JSON boundary | High | High | Boundary and round-trip tests; float-rejection fixtures; CI static gate |
| RSK-04 | Determinism broken by ambient clocks or unordered sequences | Critical | High | Determinism matrix across process, TZ, hash seed, host, restart |
| RSK-05 | Scope creep toward commercial claims | High | Medium | Claim-vocabulary scan with negative fixtures |
| RSK-06 | Abandonment mid-build | High | Medium | Sequencing gate with an ordering-violating state fixture |
| RSK-07 | Over-claiming inside the methodology | Critical | Medium | Count reconciliation; independent recomputation; prose scan; completeness test |
| RSK-08 | Methodology gamed by its author | Critical | Medium | Methodology-version test; third-party recomputation on clean clone |
| RSK-09 | Difference forced into nearest type or labelled generically | High | Medium | Taxonomy-gap test; class-coverage test; label scan |
| RSK-10 | Residual silently absorbed | High | High | Non-dividing-split test with explicit residual record |
| RSK-11 | Second source introduced before the core is proven | High | Medium | Zero-diff adapter gate with a second test adapter |
| RSK-12 | External reporting drifting from repository state | Medium | Medium | Emitted milestone state plus statement-consistency check |
| RSK-13 | Research or third-party material promoted to a requirement | High | Medium | Requirement-provenance check |
| RSK-14 | Real-data mode entering the artifact | High | Low | Ingestion refusal test; provenance-marker coverage; credential-code scan |
| RSK-15 | Benchmark theatre | High | Medium | Four-condition gate evidence, or the recorded deletion |
| RSK-16 | Tamper test that only checks the tamper it expects | Critical | Medium | Table-driven mutation-class suite; naive-check negative fixture |
| RSK-17 | Chain corruption under concurrent append | High | Medium | PostgreSQL concurrency test |
| RSK-18 | Destructive migration or schema drift | High | Medium | Clean-database migration test; migration-graph test |
| RSK-19 | Open questions closed by assertion | Medium | Medium | Milestone-vs-open-question gate |
| RSK-20 | Specification or implementation ahead of ratification | High | High | Ratification-consistency check with negative fixtures |

---

## 2. Non-Goals

Each entry states what will not be done and why. None of these is a goal deferred by oversight; each is a decision, and each is binding on subordinate documents.

**SETTLEIQ-RISK-R03 (OWNER-DEFINED):** The following are non-goals. A subordinate document that introduces one, or a milestone whose acceptance evidence requires one, is defective and must be corrected before it counts as deliverable evidence.

1. **No live money movement.** No connection to any real payment rail, bank account, or transfer. The artifact demonstrates engineering on data a third party can inspect; connecting to real money would make it uninspectable and would breach SETTLEIQ-REQ-002 and REQ-001(6). Reason: reproducibility and safety.
2. **No real customer data.** No real cardholder, merchant, or transaction data. Reason: SETTLEIQ-REQ-002 makes synthetic generator-produced data a binding scope condition, and no verification record exists that any real-data access would be permitted.
3. **No production multi-tenancy.** Single-tenant, single-workspace operation. Reason: tenancy isolation is a distinct engineering problem that the reconciliation core does not exercise, and adding it would dilute the demonstrated depth without adding evidence in the target frame.
4. **No authentication UI, user management, authorization, or roles in the first build.** Actors in `02` are roles, not accounts. Reason: an authentication surface is a security-engineering artifact, and the first build has no security claim to support it. The consequence — that journal entries cannot record an acting identity — is recorded as open question OQ-10 rather than solved by pretending an account exists.
5. **No C++ production component without the four Q2 conditions.** C++17 appears only inside the conditional M8 benchmark, which requires an identified computation-dominated workload, a measured Python baseline, an exact correctness-equivalence proof, and a demonstrated benefit. Reason: `SETTLEIQ-DEC-001` §Q2 — a benchmark on work that is not compute-bound demonstrates a number, not a capability. M8 is deleted, not deferred, if the conditions do not hold.
6. **No Java service.** Recorded explicitly in `SETTLEIQ-DEC-001` §Q2. Reason: Java is not introduced as decoration. If Java is an employment requirement, it is separate focused practice, not an architectural component here.
7. **No competitor benchmarking.** No comparison of SettleIQ's matching, accuracy, throughput, or cost against any named product. Reason: SETTLEIQ-REQ-001(1) and (4) make it binding, and the research register records that auditability, explainability, human-approval gating, and confidence scoring are documented capabilities of other products (`03` §4.2). No comparative claim is available.
8. **No pricing or go-to-market work.** No pricing recommendation, no packaging, no buyer-validation artifact, no market analysis. Reason: the commercial frame was closed on 2026-10-27; no buyer contact exists (`03` §5.4) and SETTLEIQ-REQ-001(2), (3), (5) are binding.
9. **No claim of commercial viability.** No statement that SettleIQ is commercially viable, saleable, or wanted. Reason: SETTLEIQ-REQ-001(3); no willingness-to-pay or buyer evidence exists.
10. **No machine-learning component.** Matching is deterministic and rule-based. Reason: the value demonstrated is deterministic, explainable reconciliation; a model would obscure it, and no claim of AI engineering is available (`14` §6 item 5).
11. **No real-time streaming, mobile layout, theming, component library, or design system in the first build.** Reason: `02` §5.2 item 9 and SETTLEIQ-UI-R04; a treatment no functional requirement demands is decoration and fails REQ-003.
12. **No GL-mediated integration assumed available.** No design may depend on pulling unreconciled bank statement lines through a general-ledger API. Reason: `02` §6 FM-P10 records the verified constraint that one major GL vendor does not expose that data via public API for regulatory reasons.
13. **No claim of production readiness, security, or scale.** Reason: the demonstration environment is Docker Compose on one host; no load, security, or operations evidence exists (`14` §6 items 7, 8, 9).
14. **No distributed-systems, high-concurrency, or low-latency claim.** Reason: the architecture is single-node and single-process; see `14` §6 items 1, 2, 4.
15. **No cross-repository implementation reuse.** No test coverage, benchmark result, or correctness property from another repository is cited as SettleIQ's evidence. Reason: SETTLEIQ-REQ-IND-03 and ADR-005.
16. **No completion claim without executed test output.** Reason: SETTLEIQ-REQ-016; "checkbox theater" is a named SettleIQ risk.

---

## 3. Known Open Questions

No open question below is closed by this document. Each carries the owner recorded in `SETTLEIQ-DEC-001` where one exists, and the roadmap consequence where one exists.

### 3.1 Carried from `12_DECISIONS_AND_OPEN_QUESTIONS.md`

| ID | Question | Status | Owner | Roadmap consequence |
|---|---|---|---|---|
| OQ-01 | Exact tie-breaking rule when two candidate matches are equally plausible | OPEN | `07_RECONCILIATION_ENGINE_SPEC.md` | Blocks M4's ambiguous-case acceptance evidence. Fail-closed suggests reporting ambiguous rather than choosing, but the rule set may legitimately define precedence |
| OQ-02 | Rounding convention for fee attribution when a payout's fees do not divide exactly across charges | OPEN | `07` | Blocks M3's bridge-closure acceptance evidence; largest-remainder versus deterministic last-item absorption, tested either way (RSK-10) |
| OQ-03 | Whether the discrepancy taxonomy is open or closed | OPEN | `08_DISCREPANCY_AND_AUDIT_SPEC.md` | Blocks M4's taxonomy acceptance evidence; recommendation is closed-with-explicit-unknown (RSK-09) |
| OQ-04 | Scale target for the performance work | OPEN | `11_TESTING_AND_PERFORMANCE_SPEC.md` | Without a stated records-per-run number, benchmarking is unfalsifiable; blocks M8's condition (a) and any performance claim |
| OQ-05 | Whether a real-data mode is ever in scope | OPEN | OWNER (deliberately unanswered in `12`) | Not in scope for the first build by SETTLEIQ-REQ-002; affects nothing in the current roadmap (RSK-14) |

### 3.2 New questions identified while authoring `13` and `14`

These are raised here, not resolved. Each states why it is open and where it belongs.

**OQ-06 — M2's generator scope.** The master §5 M2 row names "Stripe/Adyen-shaped generators"; `SETTLEIQ-DEC-001` §Q1 recommends Stripe-only for the first two milestones; `02` §5.2 item 5 excludes Adyen from the first build. Which of the three statements governs M2's deliverable? Belongs to the OWNER as part of Q1 ratification, and is recorded in §4 item 2 below.

**OQ-07 — Time window versus determinism.** SETTLEIQ-REQ-013 requires the published rate to state a time window; SETTLEIQ-REQ-012 requires byte-identical reproduction from identical inputs. A window derived from an ambient clock is an input that changes every run. Must the window be derived from recorded data timestamps only, or may run-scoped windows be used with the run record carrying the wall-clock reference? Belongs to `11` and to the metrics design in M6 (RSK-04).

**OQ-08 — What "AI-assisted" means for the methodology.** SETTLEIQ-REQ-013 requires the treatment of "AI-assisted or human-confirmed matches" to be stated, but the architecture contains no AI component and the matching engine is deterministic and rule-based. Does the methodology define a treatment for a category the system never produces, and is the outcome set two-bucket (automated, human-confirmed) or three? Belongs to `11` and M6 (RSK-07).

**OQ-09 — Backfilling pre-M5 runs.** M4 precedes M5 in the master ordering, so runs executed before the journal exists have no journal entries. When M5 lands, must prior runs be backfilled into the chain, or is the journal valid only from its first entry with earlier runs marked unaudited? Belongs to `08` and to `13` §3 M4's sequencing note.

**OQ-10 — Acting identity without authentication.** `02` defines actors as roles, not accounts, and the first build carries no authentication. UC-3 requires a human confirmation or rejection to be appended to the journal with its own provenance. With no account, what identifies the actor in a journal entry — a self-declared operator label, a run-scoped session, or nothing? Belongs to `08` and to Q4's scope decision.

**OQ-11 — A UI-triggered run versus determinism.** Q4's first view triggers a reconciliation run. A triggered run begins at an ambient moment. How is a run triggered through the dashboard reproducible under REQ-012 — by recording the trigger time as part of the run's inputs, or by refusing to treat a triggered run as reproducible — and what does the run record show? Belongs to `07`/`09` and M7.

**OQ-12 — M8's placement if its conditions are met late.** M8 sits between M7 and M9 in the master ordering, but its condition (a) requires a compute-bound workload identified from M3 or M4, and Q5 must be ratified before Q2. If the four conditions are only satisfied after M9 has closed, is M8 reopened after the project would otherwise be complete, or is it permanently deleted at that point? Belongs to the OWNER as part of the M8 gate (SETTLEIQ-ROAD-R06, R07).

**OQ-13 — Authority for the non-goal register.** Non-goals are stated in master §1.3 and §2, in `02` §5.2, in a planned `04_REQUIREMENTS_AND_NON_GOALS.md`, and in §2 of this document. Which document is authoritative for the non-goal set so the lists cannot drift apart? Recorded in §4 item 7 below.

**OQ-14 — Employer and vendor names in SettleIQ artifacts.** `12` §Q5 records employer and vendor names as the evidence behind its recommendation. This document and `14` avoid restating them. May employer or vendor names appear in SettleIQ artifacts at all, and under what verification discipline? Belongs to the OWNER.

---

## 4. Contradictions and Missing Requirements Found While Writing These Documents

These are recorded rather than resolved. Resolving any of them is an OWNER decision or an amendment to the governing document, not an edit made silently by a subordinate document.

1. **`02_PROBLEM_AND_USE_CASES.md` §5.1 described the five engineering decisions as "OWNER-verified", while `12_DECISIONS_AND_OPEN_QUESTIONS.md` marks all five RECOMMENDED awaiting ratification and its status convention records "RATIFIED — none yet".** **[RESOLVED 2026-10-28]** `02` §5.1 has been corrected: each of the five bullets now carries its Q-number, its RECOMMENDED-awaiting-ratification status, and the Q5-before-Q2 dependency note. The defect is recorded here rather than deleted because it is the exact case RSK-20's gate is designed to detect, and a reviewer should be able to see that it occurred and was corrected.

2. **Master §5's M2 row names "Stripe/Adyen-shaped generators" while Q1 recommends Stripe-only for the first two milestones and `02` §5.2 item 5 excludes Adyen from the first build.** Three statements conflict on M2's deliverable. `13` records the conflict and follows Q1 under the recommendation, without asserting that the master row is amended. Recommended handling: the OWNER decides at Q1 ratification, and the master §5 row is amended or annotated to match (OQ-06).

3. **Master §5's M7 target-role column reads "Backend, AI-eng", but no AI component exists anywhere in the proposed architecture** and SETTLEIQ-DEC-001 §Q2's reasoning is explicitly that the matching engine is deterministic and rule-based. The role evidence claimed for M7 is not produced by the milestone's stated deliverable. Recorded in `13` §3 M7. Recommended handling: the master §5 M7 row's role column is corrected to the roles the milestone actually evidences, or an AI-component requirement is added — which would be a scope change requiring its own decision, not a wording fix.

4. **SETTLEIQ-REQ-013's time-window requirement is in unresolved tension with SETTLEIQ-REQ-012's determinism requirement.** A window read from an ambient clock makes every run's inputs differ, which contradicts byte-identical reproduction from identical inputs. The master specification does not state which governs. Recorded as OQ-07 and as RSK-04's mitigation (g); the mitigation is PROPOSED until decided.

5. **SETTLEIQ-REQ-IND-03 in master §1.1 cites `11_DECISIONS_AND_OPEN_QUESTIONS.md` as the location for recording justifications, while the canonical decisions document is `12_DECISIONS_AND_OPEN_QUESTIONS.md` and master §8 assigns `11` to the testing and performance specification.** A reader following REQ-IND-03's citation would look for the decisions register under the wrong number, and a contributor writing `11` would find a conflicting authority claim. Recommended handling: a minor correction to the master specification's REQ-IND-03 text.

6. **`02` §5.1 lists "a benchmark of the hot path with stated honest limits" as in scope, while the master specification §4 item 5 and §5 row M8 make the benchmark explicitly conditional on the four Q2 gating conditions.** The scope list states an unconditional inclusion that the governing documents make conditional. Recommended handling: `02` §5.1's bullet is made conditional, mirroring the master's wording.

7. **No document currently claims authority for the non-goal register.** Non-goals appear in master §1.3 and §2, in `02` §5.2, in a planned `04`, and in §2 of this document. Without a stated authority, the lists can drift, and a drift in the non-goal list is the drift that matters most under SETTLEIQ-REQ-001. Recorded as OQ-13 and as §4 item 7 below.

8. **Missing: no stated relationship between the master's milestone set and the subordinate documents that do not yet exist.** `04`, `05`, `07`, `08`, and `11` are named in master §8 but not written, and `13` §5.1 lists them as preconditions for implementation authorization. That listing is this document's proposal; the master specification does not itself gate implementation on their authorship. Recorded as a gap rather than asserted as a requirement.

9. **Missing: no requirement states what happens to a closed milestone if a subsequent change alters a dependency's behaviour.** If a rule-version change alters matching outcomes, are M3's and M4's closure evidence still valid, or must they be re-executed under the new version? The reproducibility requirement (REQ-012) implies re-execution, but no requirement states it. Recorded as a gap.

No other contradictions were identified while writing `13_ROADMAP_AND_ACCEPTANCE.md`, `14_EMPLOYMENT_EVIDENCE.md`, and this document.

---

## 5. Explicit Statement of Status

Nothing in this document is implemented. No mitigation's verifying test has been executed, because no test exists. No risk has materialised, because nothing has been built. No non-goal has been tested against a real attempt to violate it. This document records intended controls, intended exclusions, and recorded specification defects, and is subordinate to `SETTLEIQ-MASTER-SPEC-001`.
