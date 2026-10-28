# 16 — Decision Register and Technical Resolutions

**Document ID:** SETTLEIQ-DECR-001
**Title:** Architecture Decision Baseline Register and Resolution of Outstanding Engineering Questions
**Version:** 1.0.0
**Status:** PROPOSED — no decision in this document is ratified
**Domain:** Decisions
**Governing document:** `SETTLEIQ-MASTER-SPEC.md` (SETTLEIQ-MASTER-SPEC-001)
**Date:** 2026-10-28
**Canonical path:** `docs/specifications/16_DECISION_REGISTER_AND_RESOLUTIONS.md`
**Owner:** Bukya Naresh (CN2)
**Traces to:** SETTLEIQ-MASTER-SPEC-001 §9; `12_DECISIONS_AND_OPEN_QUESTIONS.md`

---

## Document Control

This document records (Part A) the OWNER's proposed architecture baseline and (Part B) a resolution analysis for every outstanding engineering question, in the required seven-part form.

**SETTLEIQ-DECR-R01 (OWNER-DEFINED):** No decision in this document is ratified. The word "ratified" is reserved for an explicit OWNER approval recorded in `12_DECISIONS_AND_OPEN_QUESTIONS.md`. A recommendation, however strong its evidence, is a recommendation.

**SETTLEIQ-DECR-R02 (OWNER-DEFINED):** Where this document resolves a question by recommendation, the resolution is **binding on specification authoring** (so subordinate documents are consistent and implementable) but **not binding on implementation** (so nothing may be built against it). Implementation authorization is a separate, explicit act.

---

# PART A — Architecture Decision Baseline

## A.1 Status of the five decisions

All five are **OWNER-PROPOSED — awaiting explicit ratification.** The OWNER stated the baseline and said ratification would happen together on agreement. No explicit ratification has been recorded.

| ID | Decision | OWNER's proposed choice | Current status | Evidence basis |
|---|---|---|---|---|
| Q1 | Processor scope | Stripe only | **PROPOSED — awaiting ratification** | Stripe alone contains the full core problem; Adyen adds a temporal axis; adapter interface is frozen at M1 so scope is decoupled from the decision |
| Q2 | Language architecture | Python core; **no C++ production component initially**; C++ only if a measured workload justifies it | **PROPOSED — awaiting ratification** | No identified compute-bound workload; four-part gate in `12` §Q2 |
| Q3 | Persistence | PostgreSQL with Docker Compose | **PROPOSED — awaiting ratification** | Native `numeric`; transaction boundaries; SQL as demonstrable evidence; reproduction by construction |
| Q4 | Dashboard | Five functional views | **PROPOSED — awaiting ratification** | Each bound to a named use case in `02` |
| Q5 | Employment direction | Financial systems / ledgering primary; backend supporting; data infrastructure secondary | **PROPOSED — awaiting ratification** | Project centre of gravity; ledger domain is the rarest differentiator |

**SETTLEIQ-DECR-R03 (OWNER-DEFINED):** Every requirement in the specification set that depends on Q1–Q5 is classified **PROPOSED**. Requirements that restate master OWNER-DEFINED requirements remain OWNER-DEFINED. The tie-breaker is: *does the master specification or `04` state it verbatim?* If not, it is PROPOSED.

**SETTLEIQ-DECR-R04 (OWNER-DEFINED):** Ratification order is **Q5 before Q2**, because Q2's conditional C++17 gate depends on the target-role decision. Ratifying Q2 first would mean ratifying a decision whose precondition is still open.

## A.2 Java and C++ — explicit non-inclusion

| Language | Position | Rationale |
|---|---|---|
| **Python** | Core implementation language | Sole production language for the engine, persistence access, and API |
| **SQL** | Required practical mastery | PostgreSQL is the durable store |
| **TypeScript** | Dashboard client | Bound to the five views |
| **Java** | **Not in SettleIQ.** Separate focused learning track | No requirement justifies it; inserting it would be technology-count inflation, which the OWNER explicitly rejected |
| **C++** | **Not in SettleIQ.** Advanced systems practice, or a benchmarked component only if the four Q2 conditions hold | Introducing it without a measured workload would demonstrate a stopwatch, not a capability |

**SETTLEIQ-DECR-R05 (OWNER-DEFINED):** No Java or C++ component, service, module, or build target shall exist in the SettleIQ repository unless the four Q2 gating conditions are satisfied and recorded, or the OWNER explicitly authorises inclusion with a stated justification.

---

# PART B — Resolution of Outstanding Engineering Questions

Each question is resolved in the required seven-part form. Every resolution carries a recommendation, testable acceptance criteria, and a statement of remaining uncertainty. **No resolution invents a financial rule silently.**

---

## B.1 Ambiguous-match handling

**Options.**

| # | Option | Failure mode |
|---|---|---|
| 1 | First candidate wins (iteration order) | Non-deterministic under reordering; a guess presented as a match |
| 2 | Deterministic tie-break by a declared key (e.g. lowest identifier) | Deterministic, but assigns money to the wrong record when the tie is real |
| 3 | Numeric confidence scoring, highest wins | Prohibited — creates a false ordering among indistinguishable candidates |
| 4 | Emit `AMBIGUOUS` with the full candidate set; raise a typed break; require explicit human resolution | Correct answer is "the engine cannot know"; resolution is recorded and attributable |

**Evidence.** Master REQ-009 (fail-closed) and REQ-007 (provenance) govern. Verified research record (V8, Class A) shows a vendor publishes its own historical match patterns but still requires human confirmation; it does not claim automated disambiguation. No source examined describes an engine that resolves genuine ties automatically — and a genuine tie is by definition unresolvable without additional evidence.

**Financial correctness implications.** Option 2 assigns a charge to a payout that may not have contained it. That is a factual error in a ledger — the exact class of error the engine exists to prevent. Options 1 and 3 additionally make the error irreproducible.

**Implementation complexity.** Option 4 requires: an `AMBIGUOUS` classification, a candidate-set payload on the decision record, a typed discrepancy, and a resolution workflow with recorded actor and reason. All four are already required by `08`. Marginal cost is low because the taxonomy and journal already exist.

**Recommended decision.** **Option 4.** Sub-provisions:
* The candidate set is stored complete, with no member marked "selected".
* A *presentation key* may order the set for display stability, but the presentation key carries **no semantic weight** and must be documented as such wherever it appears.
* Resolution requires an explicit recorded action naming the selected candidate, the actor, and the reason. It never mutates the original decision; it appends a superseding resolution record.
* The correct engineering response to a *recurring* ambiguity is to add a rule, bump the rule version, and re-run — not to tie-break.

**Testable acceptance criteria.**
* AC-B1-01: a fixture with two equally-plausible candidates asserts `AMBIGUOUS`, with exactly two candidates present in the decision's evidence and none selected.
* AC-B1-02: a typed break of type `AMBIGUOUS_MATCH` is raised, carrying the decision reference.
* AC-B1-03: determinism — the candidate set's presentation order is byte-identical across re-runs.
* AC-B1-04: a resolution records actor, reason, selected candidate, and a record timestamp drawn from the run's declared clock (not ambient time).
* AC-B1-05: the original decision record is unmodified after resolution (append-only).

**Remaining uncertainty.** Whether a legitimate *rule* could reduce a tie to a deterministic match in some cases. That depends on the rule set designed at M3 and is resolved there — not by weakening this decision.

---

## B.2 Residual allocation (non-dividing fees)

**Options.**

| # | Option | Failure mode |
|---|---|---|
| 1 | Largest-remainder allocation | Standard in tax rounding; fabricates fee attribution to specific charges |
| 2 | Last-item absorption | Puts an arbitrary amount onto whichever item sorts last |
| 3 | Explicit residual constituent, never allocated | Residual is visible and traceable; attribution is not invented |
| 4 | Round fees to a fixed scale and let the difference fall out | Silent precision loss; contradicts REQ-005 |

**Evidence.** Master REQ-005 (exact decimal, explicit rounding) and REQ-009 (fail-closed). `07` ARCH-R07 requires a residual to be explicit and never silently discarded.

**Financial correctness implications.** Options 1, 2, and 4 all assign or destroy money in a way the source data does not support. In a reconciliation system, an unexplained 0.01 attributed to the wrong charge is worse than an explained 0.01 attributed to nowhere — because the latter is a *known unknown* the discrepancy engine can act on.

**Implementation complexity.** Option 3 is the simplest of the four: the residual is a first-class constituent with its own type, amount, currency, and the rule id + version that produced it.

**Recommended decision.** **Option 3 — explicit residual constituent.** Sub-provisions:
* `RESIDUAL` is a constituent type in the canonical model, carrying amount, currency, allocation-rule id, and rule version.
* The decomposition invariant becomes: `Σ(allocated constituents) + Σ(RESIDUAL constituents) = payout amount`, exactly, in Decimal.
* A residual is a countable, ageable, investigable object — it can be a discrepancy input, not an absorption bucket.
* If a future requirement demands per-charge fee allocation, it is a new specification with its own allocation rule and its own tests. It is not added by quietly changing this behaviour.

**Testable acceptance criteria.**
* AC-B2-01: a payout whose fees do not divide exactly over its charges produces a `RESIDUAL` constituent with the exact remainder.
* AC-B2-02: the invariant `Σ(allocated) + Σ(RESIDUAL) = payout.amount` holds exactly in Decimal, over a property test with generated non-dividing cases.
* AC-B2-03: no charge's stored amount is modified by the allocation.
* AC-B2-04: the residual carries `allocation_rule_id` and `rule_version`.

**Remaining uncertainty.** Whether downstream consumers (a GL posting, if ever built) will require per-charge fee attribution. Unknown; recorded as a possible v2 driver rather than a design assumption.

---

## B.3 Currency-specific exponent validation

**Options.**

| # | Option | Failure mode |
|---|---|---|
| 1 | Fixed 2 decimal places for all currencies | Rejects valid JPY (0 dp); silently accepts invalid precision elsewhere |
| 2 | Fixed 4 decimal places | Loses the exponent check entirely; permits float-integer confusion |
| 3 | Per-currency exponent declared in an in-repo currency table; validate on ingest and at computation boundaries; **raise** on excess precision | Correct; fails closed on unknown currency |
| 4 | Unconstrained `numeric`, no validation | No money-safety at the boundary |

**Evidence.** Master REQ-005. Verified: ISO 4217 minor-unit exponents genuinely vary — JPY = 0, USD = EUR = 2, BHD = KWD = OMR = 3. This is not hypothetical; the earlier assumption of a single fixed `numeric(p,s)` scale was corrected in `06` precisely because Postgres rounds beyond the declared scale and would silently corrupt JPY or BHD amounts.

**Financial correctness implications.** Option 1 corrupts JPY. Option 2 permits false precision. Option 4 permits anything. Option 3 is the only option that neither rejects valid data nor accepts invalid data.

**Implementation complexity.** Moderate and front-loaded: a declared currency table (a code-level constant, versioned with the data model), a validator invoked at ingest and at computation boundaries, and a typed error. Low thereafter.

**Recommended decision.** **Option 3.** Sub-provisions:
* An in-repo declared table of supported currencies and their minor-unit exponents, versioned and part of the schema/data-model version.
* Supported set for the first build: USD, EUR, GBP, JPY, INR, BHD, KWD — with an explicit, documented extension procedure.
* An **unknown currency is a hard error** (`CURRENCY_NOT_SUPPORTED`), never a default to 2.
* Validation raises `CURRENCY_PRECISION_EXCEEDED`; it never rounds, truncates, or coerces.
* The database stores unconstrained `numeric` (never `float8`, never integer-cents), and a database CHECK rejects non-finite values. The exponent rule is enforced in the application layer at ingest, not by a column width.

**Testable acceptance criteria.**
* AC-B3-01: `"100.5"` in JPY is rejected with `CURRENCY_PRECISION_EXCEEDED`.
* AC-B3-02: `"1043.275"` in USD is rejected (3 dp exceeds 2).
* AC-B3-03: `"1043.275"` in BHD is accepted.
* AC-B3-04: an unknown currency code is rejected with `CURRENCY_NOT_SUPPORTED`.
* AC-B3-05: a property test asserts no code path converts a monetary Decimal to a binary float.
* AC-B3-06: no monetary DB column is `float8` or integer-cents (schema assertion).

**Remaining uncertainty.** Whether to embed the full ISO table rather than a declared subset. Recommendation is a declared subset with documented extension — embedding 180 currencies nobody tests is coverage theatre, not safety.

---

## B.4 Discrepancy taxonomy (closing OQ-03)

**Options.**

| # | Option | Failure mode |
|---|---|---|
| 1 | Open taxonomy, new types added as discovered | Unmodelled breaks appear handled; exhaustiveness is untestable |
| 2 | Closed taxonomy with an explicit `UNKNOWN` class | Exhaustive and testable; `UNKNOWN` is itself a countable outcome |
| 3 | Single generic `MISMATCH` type | Prohibited by REQ-008 |

**Evidence.** `08` §2 already specifies the full taxonomy (presence/absence, amount, fee/composition, timing, ambiguity/sufficiency) plus `UNKNOWN`. Verified Class A source (V15): a processor vendor itself publishes a two-sided presence/absence definition — "present in NetSuite and not present at the processor, or present at the processor and not present in NetSuite" — corroborating that this distinction is the industry's central break shape, not an invented one.

**Recommended decision.** **Option 2 — closed with `UNKNOWN`.** Sub-provisions:
* Exhaustiveness is enforced structurally: a test iterates every engine exit path and asserts it maps to a declared type or `UNKNOWN`. A new code path producing an untyped break fails the test.
* `UNKNOWN` is countable, ageable, and reportable. It is never absorbed.
* Extending the taxonomy is a specification change with new acceptance criteria, not a code change.

**Testable acceptance criteria.** AC-B4-01 through AC-B4-03 mirror `08` AC-01/02/05: every injected defect class classified correctly; no path produces an unclassified break; `UNKNOWN` is reachable and countable.

**Remaining uncertainty.** Whether Adyen-shaped data (excluded from the first build by Q1) would require additional types. Deferred, not assumed.

---

## B.5 Rule precedence and evaluation order

This is the highest-consequence unresolved item: it governs whether a result can be reproduced after a rule change.

**Options.**

| # | Option | Failure mode |
|---|---|---|
| 1 | Implicit precedence (whatever the data structure does) | Non-deterministic; result changes on refactor with no rule change |
| 2 | Strict sequential: first rule that *fires* decides, even if it yields `AMBIGUOUS` | Deterministic, but a weak early rule blocks a strong later rule |
| 3 | **All rules evaluated; determinism beats ambiguity; lowest rank wins among deterministic; disagreeing deterministic outcomes are a typed break** | Deterministic, fail-closed, and makes rule conflict visible instead of hidden |
| 4 | Rule priority by numeric score | Prohibited — false precision |

**Evidence.** Master REQ-012 (byte-identical output for identical input and rule version) and REQ-009. Verified research (V5, Class A): a vendor documents a deterministic *core* with a rules-priority sequence and human override — consistent with Option 3's structure. `05` ARCH-R12 already requires declared order, explicit rank, and no later-rule override.

**Financial correctness implications.** Option 2 can silently discard a correct deterministic match because an earlier rule raised ambiguity. Option 1 makes results irreproducible across code changes.

**Implementation complexity.** Option 3 requires evaluating all applicable rules per record rather than short-circuiting. At demonstration scale (tens of thousands of records, a small rule set) this is immaterial. The complexity is in the conflict reporting, not the evaluation.

**Recommended decision.** **Option 3.** Sub-provisions:
* Rule registry is an explicit ordered structure; each rule declares `id`, `version`, `precedence_rank`, `consumed_fields`, `preconditions`, and its candidate predicate. **Duplicate ranks are rejected at registry load.**
* `precedence_rank` is part of the rule version, which is part of run identity. Changing precedence changes rule version and therefore invalidates comparison against prior runs.
* Evaluation semantics, in order:
  1. Evaluate all applicable rules.
  2. Exactly one deterministic result → use it.
  3. Two or more deterministic results that **agree** → use it; record the agreement.
  4. Two or more deterministic results that **disagree** → raise a typed `RULE_CONFLICT` break. **Do not choose.**
  5. Otherwise, any `AMBIGUOUS` results → emit `AMBIGUOUS` with the full candidate set.
  6. No applicable rule → `INSUFFICIENT_EVIDENCE`.
* Rule changes are made by adding a rule version and re-running, never by editing a prior version.

**Testable acceptance criteria.**
* AC-B5-01: a rule registry containing duplicate precedence ranks is rejected at load.
* AC-B5-02: changing precedence produces a different `rule_version`, and two runs differing only in `rule_version` do not compare equal.
* AC-B5-03: two deterministic rules that disagree produce `RULE_CONFLICT`, carrying both outcomes.
* AC-B5-04: one deterministic plus one ambiguous result → the deterministic result is used and the ambiguity is still recorded in provenance.
* AC-B5-05: changing precedence with identical input yields a decision that differs *only* where the rule conflict/output changed — recorded, not silent.

**Remaining uncertainty.** Evaluating all rules is O(rules × records). Fine at demonstration scale; a performance consideration only if the B.7 target is raised. Not a blocker.

---

## B.6 Discrepancy severity derivation

**Options.**

| # | Option | Failure mode |
|---|---|---|
| 1 | Manual severity assigned by investigator | Not reproducible; a judgement recorded as data |
| 2 | Severity by type only | Ignores materiality — a ₹1 phantom and a ₹10,00,000 phantom behave identically |
| 3 | Declared matrix over (type, amount-at-stake band) | Reproducible; materiality-aware; declarable and versioned |
| 4 | Severity from a model or heuristic | Unjustifiable opacity in a financial control |

**Evidence.** Master REQ-012 requires reproducibility. Verified research (V6, Class A) shows a vendor that requires "materiality thresholds configurable by account type and applied automatically," i.e. severity/auto-submission from declared thresholds rather than judgement — corroborating Option 3's shape.

**Recommended decision.** **Option 3.** Sub-provisions:
* Declared matrix `severity_matrix(type, band) → severity`, held as data in the rule version, not as scattered code branches.
* Amount bands are declared (e.g. `≤ tolerance`, `≤ materiality`, `> materiality`) with explicit boundaries; boundary-inclusive semantics declared once.
* An unknown `(type, band)` **raises** rather than defaulting to LOW.
* Manual judgement is never stored as severity; it is recorded in `resolution_history` where it is visible and attributable.

**Testable acceptance criteria.**
* AC-B6-01: severity for a given `(type, amount)` is byte-identical across runs.
* AC-B6-02: the matrix is loaded from a versioned declaration and the version is part of run identity.
* AC-B6-03: an unknown `(type, band)` pair raises rather than defaulting.
* AC-B6-04: a materiality change is visible as a rule-version change, not a silent reclassification.

**Remaining uncertainty.** The band boundaries themselves are a business judgement. Recommendation is that they are declared with conservative values and documented; the OWNER may set them differently, and any change is a versioned change.

---

## B.7 Performance target and benchmark methodology

**Options for the target.**

| # | Option | Failure mode |
|---|---|---|
| 1 | No target; "it should be fast" | Unfalsifiable; a benchmark becomes decoration |
| 2 | Absolute throughput claim (e.g. "1M records/minute") | Meaningless without declared hardware, input, and methodology |
| 3 | Declared reference workload with a stated time budget on a stated machine | Falsifiable, reproducible, and honest about what it measures |

**Options for the benchmark.**

| # | Option | Failure mode |
|---|---|---|
| A | Single timing run | Variance unknown; a number that means nothing |
| B | Median of N runs after warm-up, with variance, input digest, environment recorded | Reproducible and honest |

**Recommended decision — target (Option 3).**
* **Declared reference workload:** 50,000 charges, 5,000 payouts, 5,000 bank deposits, all synthetic, from the versioned generator with a recorded seed.
* **Stated time budget:** full reconciliation run in ≤ 60 seconds on a declared reference machine, single-threaded Python, PostgreSQL local.
* The workload, budget, and reference machine are **declared inputs recorded with the benchmark output** — not a marketing claim.
* Missing the budget is a recorded finding, not a hidden one.

**Recommended decision — methodology (Option B).**
* Median of 5 runs after 2 warm-up runs; report min, median, max, variance.
* Record: input digest, generator version, rule version, schema version, Python version, PostgreSQL version, OS, CPU, RAM.
* Report the **honest limits**: that this measures a synthetic single-node workload and says nothing about another workload.

**C++17 gate evaluation.** The four conditions must be assessed *after* a measured baseline exists. The expected honest outcome is that the workload is **database-bound**, in which case C++ is not justified and M8 is **deleted with the deletion recorded**, as `11` T-ST-R17 requires. This is a legitimate and valuable result, not a failure.

**Testable acceptance criteria.**
* AC-B7-01: the benchmark harness runs and emits the full environment record.
* AC-B7-02: two runs of identical declared input produce timings within a declared variance bound, or the variance is reported as exceeding it.
* AC-B7-03: the gate evaluation outcome is recorded explicitly as either "conditions satisfied — benchmark" or "conditions not satisfied — M8 deleted", with the measurement that decided it.

**Remaining uncertainty.** Whether 60s is achievable. It is a target, not a claim; missing it is reportable. The reference machine must be declared before the benchmark runs.

---

## B.8 Synthetic versus real-data scope

**Options.**

| # | Option | Failure mode |
|---|---|---|
| 1 | Synthetic only, permanently | The adapter contract never has to accommodate real data |
| 2 | Synthetic for the artifact, with a declared policy so a real-data mode is additive | Safe now, and does not require rearchitecting to add real data later |
| 3 | Real data with anonymisation | Requires security review, data-governance policy, and authorisation the OWNER has not given |

**Evidence.** Master REQ-002 (synthetic only) and REQ-001.6 (not connected to live money or real customer data). No authorisation exists for real financial data.

**Recommended decision.** **Option 2.** Sub-provisions:
* The canonical model carries a `DataProvenance` field with values `SYNTHETIC | AUTHORIZED_REAL`.
* Every run records its provenance in run identity. **Engine behaviour is identical for both** — provenance is metadata, never a branch.
* `AUTHORIZED_REAL` cannot be set by any code path without an explicit authorization record; the first build's generator produces only `SYNTHETIC`.
* A future real-data mode is a separate specification requiring: data-governance policy, retention/deletion rules, access control, and explicit OWNER authorisation. It is not enabled by configuration.

**Testable acceptance criteria.**
* AC-B8-01: the first-build generator emits only `SYNTHETIC`.
* AC-B8-02: a test runs a real-shaped dataset labelled `AUTHORIZED_REAL` and asserts outputs identical to the same dataset labelled `SYNTHETIC`.
* AC-B8-03: a check asserts no production code path can set `AUTHORIZED_REAL` without an authorization record present.

**Remaining uncertainty.** None blocking for M1. The future real-data policy is a deliberate later decision.

---

## Part B.9 — Summary of resolutions

| Question | Recommended resolution | Blocks M1? |
|---|---|---|
| Ambiguous matches | Emit `AMBIGUOUS`, never tie-break; explicit recorded resolution | **Yes** — data model must carry candidate sets |
| Residual allocation | Explicit `RESIDUAL` constituent, never allocated | **Yes** — constituent type in the model |
| Currency exponents | Per-currency declared table; raise, never round | **Yes** — validator in M1 |
| Discrepancy taxonomy | Closed with `UNKNOWN`, enforced structurally | No — `08` already specifies; blocks M4 |
| Rule precedence | All rules evaluated; determinism beats ambiguity; conflict is a typed break | No — blocks M3 |
| Severity derivation | Declared versioned matrix over (type, band) | No — blocks M4 |
| Performance target | Declared reference workload + median-of-N methodology; gate evaluated after baseline | No — blocks M8 |
| Real-data scope | Synthetic only; `DataProvenance` in the model; real mode is a later spec | **Yes** — field in the model |

**Three resolutions block M1 and are therefore part of the M1 plan**: candidate sets on decisions, `RESIDUAL` as a constituent type, and the currency validator. `DataProvenance` also lands in M1.
