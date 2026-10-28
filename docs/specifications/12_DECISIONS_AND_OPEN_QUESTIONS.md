# 12 — Decisions, Recommendations, and Open Questions

**Document ID:** SETTLEIQ-DEC-001
**Title:** Engineering Decisions and Open Questions
**Version:** 1.0.0
**Status:** PROPOSED — recommendations only. No decision below is ratified.
**Date:** 2026-10-28
**Canonical path:** `docs/specifications/12_DECISIONS_AND_OPEN_QUESTIONS.md`
**Traces to:** SETTLEIQ-MASTER-SPEC-001 §9

---

## Status Convention for This Document

Every entry carries one of:

* **RECOMMENDED** — evidence-based recommendation; requires OWNER ratification.
* **RATIFIED** — approved by the OWNER. **None yet.**
* **OPEN** — insufficient evidence to recommend; the gap is stated.
* **RESOLVED BY RECOMMENDATION** — analysed with competing options, evidence, acceptance criteria, and a recommendation recorded in `16_DECISION_REGISTER_AND_RESOLUTIONS.md` Part B. Binding on specification authoring, not on implementation. Requires OWNER ratification to become an implementation decision.

**SETTLEIQ-DEC-R10 (OWNER-DEFINED):** Where any subordinate document still describes OQ-01…OQ-05 as open, unresolved, or "must be settled", **`16` governs** and that wording is stale. Subordinate documents cite `16` §B.<n>.

Nothing in this document is an implementation decision unless marked RATIFIED. A recommendation is not an approval.

---

## Q1 — Processor Scope

### Question
Stripe-only, or Stripe plus Adyen?

### Verified evidence bearing on the choice

| Fact | Class | Source |
|---|---|---|
| Stripe: "You control the timing and amount of instant payouts, so Stripe can't identify which transactions are included in each payout. You're responsible for reconciling instant payouts against your transaction history." | A | docs.stripe.com/payouts/reconciliation |
| Stripe: payout reconciliation report available only for **automatic** payouts; report data follows a separate processing schedule and can lag payout arrival; itemized PDF capped at 5,000 rows; Dashboard reports whole days only | A | docs.stripe.com/reports/payout-reconciliation |
| Adyen: payouts are **net** of transaction costs/refunds/chargebacks, so the merchant must bridge gross-to-net; payout initiation takes 1–2 business days and banks may take up to 3 more; payouts do not process on bank holidays | A | docs.adyen.com/account/getting-paid |
| Adyen: Settlement Detail Report provides per-transaction cost, exchange rate, payout reference, batch number, bank account | A | docs.adyen.com/reporting/settlement-reconciliation |
| Xero (third-party GL): "You need to reconcile manual payouts manually." | A | support.stripe.com (Xero integration note) |
| Braintree: its own Dashboard and Settlement Batch Summary "should not be used for reconciliation purposes" | A | developer.paypal.com/braintree |

### Recommendation — RECOMMENDED

**Stripe-only for the first two milestones, with the adapter abstraction designed so Adyen is additive rather than a rewrite.**

Rationale:
1. Stripe alone contains the full core problem: fee decomposition, withheld tax, refunds and disputes arriving mid-payout, fee-net-of-tax, and a payout composition that the processor explicitly declines to identify for manual and instant payouts. That is charge-level reconciliation in its hardest documented form.
2. Adyen's principal additions are **temporal** (multi-day settlement lag, bank-holiday gaps, netting across batches), not structural. Temporal reconciliation is a genuine and interesting dimension, but it is a second axis, not a deeper version of the first.
3. The instruction for this decision is explicit: recommend the smallest scope that still demonstrates substantial financial systems engineering. Two adapters with the second adding a different problem axis does not meet that test for a first build.
4. The cost of choosing wrong is low and asymmetric. If Adyen is later added and proves essential, the adapter interface absorbs it. If Adyen is built first and Stripe proves essential, the temporal work is not reusable.

Non-negotiable condition: the `SourceAdapter` interface in `09_API_AND_INTEGRATION_SPEC.md` must be defined and frozen at M1, before either adapter is written. The interface is the decision; the adapter count is not.

---

## Q2 — Language Architecture

### Question
Python core, and is a C++17 component justified?

### Recommendation — RECOMMENDED

**Python-only core. No C++17 in the first build. A C++17 hot-path benchmark is a conditional later milestone, gated on Q5 and on an identified workload.**

Reasoning:
1. **There is currently no defensible C++ workload.** At demonstration scale, a reconciliation engine over synthetic data is dominated by ingestion, database access, and Python-level orchestration. A C++ port would benchmark interpreter overhead on work that is not compute-bound. Producing a benchmark under those conditions would demonstrate a number, not a capability, and would violate the spirit of SETTLEIQ-REQ-004.
2. **The stated objective is skill depth, not language count.** A second language in the architecture without a measured need is exactly the pattern to avoid.
3. **Java: not introduced.** No Java service. If Java is an employment requirement, it is separate focused practice, not an architectural component of this project. Recording it as such is honest; embedding it here would be decoration.

**Conditional C++17 gate — all four must hold before C++ is justified:**
* A specific, identified workload exists whose measured runtime is dominated by computation rather than I/O.
* A Python baseline has been measured on that workload with reproducible benchmarks.
* A correctness-equivalence test exists that proves the two implementations agree exactly on Decimal results, including rounding.
* A meaningful performance or systems-engineering benefit is demonstrated, not asserted.

If and only if all four hold, a C++17 hot-path benchmark becomes a milestone. Otherwise it does not.

### Coupling warning

**Q2 cannot be finalised before Q5.** If the target role resolves to quantitative development or low-latency systems, the calculus changes and C++ becomes defensible as a deliberate skill demonstration even without a production need — provided the four conditions above still hold. Ratify Q5 first.

---

## Q3 — Persistence

### Question
PostgreSQL, and how is reproducibility satisfied?

### Recommendation — RECOMMENDED

**PostgreSQL, provisioned via Docker Compose, as the sole durable store. SQLite permitted only for ephemeral in-process test fixtures.**

Justification:
1. **Exact decimal is native.** Postgres `numeric` preserves exact decimal arithmetic, directly supporting SETTLEIQ-REQ-005. Storing money as `float8` or as integer cents with implicit scaling would both weaken the guarantee the project is built to demonstrate.
2. **Transaction boundaries are expressible.** The append-only hash-chained journal (REQ-010/011) and the ledger write must be atomic. Postgres gives real transactional semantics to specify and test.
3. **SQL depth is employment evidence.** Relational schema design, migration discipline, and optimised queries are directly relevant to the target roles. This is a skill the project can *demonstrate*, not merely claim.
4. **Reproduction is satisfied by construction.** `docker compose up` provisions the database, runs migrations, and seeds deterministic fixtures in one command. REQ-003 is met by the environment definition, not by documentation.

Required properties, to be specified in `06_DATA_MODEL_AND_PERSISTENCE.md`:
* Forward-only, versioned migrations; no destructive migrations in any environment.
* Deterministic seed fixtures: fixed seeds, fixed generator version, fixed schema version. A run is identified by its input digest.
* Amount columns typed `numeric` with an explicit scale constraint and a database-level check rejecting non-numeric input.
* Explicit transaction boundaries around journal append and ledger write.
* A concurrency test proving that two simultaneous journal appends cannot interleave into an invalid chain.

---

## Q4 — Dashboard Scope

### Question
What is the smallest complete interface?

### Recommendation — RECOMMENDED

**Five views, each with a functional requirement tied to a named use case in `02_PROBLEM_AND_USE_CASES.md`. Nothing decorative.**

| View | Functional requirement | Use case served |
|---|---|---|
| Run list | Trigger a reconciliation run; show run ID, input digest, rule version, outcome counts | UC-1 Reproducible run |
| Discrepancy queue | List discrepancies by type and age; filter by type, severity, age; drill through | UC-2 Triage |
| Investigation detail | For one discrepancy: contributing records, matched fields, provenance, rule trace, decision trail, resolution history | UC-3 Investigate |
| Metrics | Auto-match rate computed from instrumented counts, with the denominator, population, window, and human-confirmation treatment displayed inline | UC-4 Measure |
| Run history | Re-run a prior input and diff the outcome against the original | UC-5 Reproduce |

Technology: a small TypeScript client built **within this repository**, served by the project's own API. No styling system, no component library, no design tokens until a functional requirement demands them.

Explicitly out of scope for the first build: authentication UI, multi-tenancy, user management, theming, mobile layout, real-time streaming.

Rationale: the dashboard earns its place by making the end-to-end workflow visible — a typed discrepancy produced, investigated, and resolved with traceable evidence. A polished interface that does not carry that workflow is decoration and fails REQ-003.

---

## Q5 — Target Employment Role and Skill Emphasis

### Question
Which role does the architecture serve first?

### Evidence from the completed employment research (M4)

* Job descriptions examined include Block's "Recon & Ledgering" role and Citi/SmartStream TLM reconciliation engineering. Both describe settlement reconciliation, discrepancy investigation, and ledgering as the work itself.
* The reconciliation domain was found to span all six target roles investigated.
* **Ledger / ledgering domain was identified as the rarest differentiator** among the candidates.
* Open-source presence was explicitly listed as a plus in at least one target JD.
* Data-infrastructure and backend roles value pipeline, SQL, and testing depth.

### Recommendation — RECOMMENDED

**Primary emphasis: financial systems and ledgering engineering. Supporting frame: backend engineering. Secondary, not simultaneous: data infrastructure.**

Rationale:
1. SettleIQ's core work — charge-level settlement decomposition, typed discrepancy investigation, exact-decimal ledgering, hash-chained audit — is precisely the work those JDs describe. The project's centre of gravity already sits here; choosing another emphasis would mean building away from the strongest evidence.
2. Ledger domain is the rarest capability in the candidate pool. Depth here is worth more than breadth across a more common skill.
3. Backend engineering is the natural supporting frame: API contracts, persistence, testing, and deployment are all required by the primary emphasis anyway.
4. Quantitative development / low-latency systems is a legitimate target but a different centre of gravity. Pursuing it *in addition* splits focus. If the OWNER wants it, it should replace rather than supplement the primary emphasis — and that decision reopens Q2.

Consequence for this document: **ratify Q5 before Q2, because Q2's conditional gate depends on it.**

---

## Architectural Decisions Recorded (ADRs)

These are recommendations too, recorded for traceability.

**ADR-001 — Money is `Decimal`, never binary float.**
Basis: SETTLEIQ-REQ-005. Enforced by type discipline, property tests, and a CI gate that rejects float on any monetary code path.

**ADR-002 — Deterministic core, measured before anything is automated.**
Basis: SETTLEIQ-REQ-012. Reproducibility is a testable property, established before any performance or intelligence work.

**ADR-003 — Hash digests are computed and verified, never authored.**
Basis: SETTLEIQ-REQ-011. A tamper-injection test must detect modification. This is the direct defence against the fabrication defect found repeatedly in prior repositories.

**ADR-004 — The measurement methodology is part of the artifact.**
Basis: SETTLEIQ-REQ-013/014. The denominator, population, window, and human-confirmation treatment are code, not prose.

**ADR-005 — No cross-repository implementation reuse.**
Basis: SETTLEIQ-REQ-IND-03. Every component is built and tested here.

---

## Open Questions That Remain Open

| ID | Question | Status | Why unresolved |
|---|---|---|---|
| OQ-01 | Tie-breaking when two candidate matches are equally plausible | **RESOLVED BY RECOMMENDATION** | Emit `AMBIGUOUS` with the full candidate set; never tie-break; explicit recorded resolution. `16` §B.1 |
| OQ-02 | Residual allocation when fees do not divide exactly across charges | **RESOLVED BY RECOMMENDATION** | Explicit `RESIDUAL` constituent, never allocated. `16` §B.2 |
| OQ-03 | Discrepancy taxonomy open or closed | **RESOLVED BY RECOMMENDATION** | Closed with explicit `UNKNOWN`, enforced structurally. `16` §B.4 |
| OQ-04 | Scale target for the performance work | **RESOLVED BY RECOMMENDATION** | Declared reference workload (50k charges / 5k payouts / 5k deposits, ≤60s) + median-of-5 methodology. `16` §B.7 |
| OQ-05 | Whether a real-data mode is ever in scope | **RESOLVED BY RECOMMENDATION** | Synthetic only for the artifact; `DataProvenance` on the model; real mode is a later spec requiring authorisation. `16` §B.8 |

### Resolved by recommendation in `16`, awaiting OWNER ratification

| ID | Question | Status | Resolution |
|---|---|---|---|
| OQ-07 | Rule precedence evaluation order | **RESOLVED BY RECOMMENDATION** | All applicable rules evaluated; determinism beats ambiguity; disagreeing deterministic outcomes raise `RULE_CONFLICT`. `16` §B.5 |
| OQ-08 | Discrepancy severity derivation | **RESOLVED BY RECOMMENDATION** | Declared versioned matrix over (type, amount band); an unknown pair raises rather than defaulting. `16` §B.6 |

### Still genuinely open — not resolvable by the specification author

| ID | Question | Status | Why open |
|---|---|---|---|
| OQ-09 | Whether pre-M5 runs must be backfilled into the journal once it exists | OPEN | A sequencing question; recorded in `15` §4 and `17` F-06 |
| OQ-10 | Amount-band boundaries for the severity matrix | OPEN | A business judgement the OWNER should set; any value is a versioned change |
| OQ-11 | Reference machine declaration for the benchmark | OPEN | Must be declared before any benchmark runs; `16` §B.7 |
| OQ-12 | Whether a journal entry's stored timestamp is excluded from its digest preimage | OPEN | Implied by `06` DATA-R09 but not stated in `08`; must be stated explicitly in the M5 specification |

---

## What This Document Does Not Claim

No decision here is ratified. No implementation exists. No benchmark has been run. No component has been built. No competitor is asserted to lack any capability.
