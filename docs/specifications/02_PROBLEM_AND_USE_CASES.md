# 02 — Problem Statement and Use Cases

**Document ID:** SETTLEIQ-PROB-001
**Title:** SettleIQ Problem Statement, Actors, Use Cases, and Scope Boundaries
**Version:** 1.0.0
**Status:** PROPOSED — specification only; no implementation claimed
**Domain:** Problem framing, actors, use cases, scope boundaries
**Governing document:** `SETTLEIQ-MASTER-SPEC.md` (SETTLEIQ-MASTER-SPEC-001)
**Date:** 2026-10-28
**Canonical path:** `docs/specifications/02_PROBLEM_AND_USE_CASES.md`
**Owner:** Bukya Naresh (CN2)
**Traces to:** SETTLEIQ-MASTER-SPEC-001 §1, §2.2, §8 (row 02); master requirements SETTLEIQ-REQ-002 and SETTLEIQ-REQ-006 in particular

---

## Document Control

### Purpose

This document states the problem SettleIQ addresses, in terms a competent engineer with no payments background can follow; names the actors who interact with the system; enumerates the use cases the system must support; and fixes the in-scope and out-of-scope boundaries.

This is a **specification-only document**. It describes intended problem framing and intended use cases. It does not describe implemented software, and nothing in it is evidence that SettleIQ does anything. Where this document states a fact about payment processing, that fact is either general domain knowledge or is traced to a Class A source recorded in `SETTLEIQ-MASTER-SPEC-001` §1.2, in `12_DECISIONS_AND_OPEN_QUESTIONS.md` §Q1, or in `docs/research/02_verification_log.md`. No statistic is introduced here that does not appear in those sources.

### Relationship to the governing specification

The master specification is the sole authority for SettleIQ's scope and requirements. This document elaborates a subset of it — principally SETTLEIQ-REQ-002 (synthetic data only) and SETTLEIQ-REQ-006 (reconciliation at charge level, not payout level) — and supplies the named use cases that subordinate documents (the dashboard specification, the engine specification, the test specification) trace to. It introduces no new requirement.

---

## 1. Purpose and Scope

SettleIQ exists to demonstrate, on synthetic data a third party can inspect, the engineering involved in payment settlement reconciliation: decomposing a processor payout into the charges, fees, refunds, chargebacks, and adjustments that produced it; matching each constituent across the processor, bank, and ledger sides; classifying what does not match into a named type rather than a generic "mismatch"; carrying the evidence for every decision; and reporting the resulting auto-match rate with an explicitly documented measurement methodology.

The audience for the artifact is a hiring manager evaluating candidates for financial-systems, ledgering, or backend engineering roles. This framing was selected by the OWNER on 2026-10-27 and is recorded in `SETTLEIQ-MASTER-SPEC-001` §1.2. It is binding: **SETTLEIQ-REQ-000 and SETTLEIQ-REQ-001 prohibit any competitive, market-gap, pricing, or product-market-fit claim in any SettleIQ artifact.** Nothing in this document is a positioning statement.

The scope of this document is narrow: problem statement, actors, use cases, scope boundaries, and the failure modes of the approach SettleIQ rejects. The reconciliation algorithm, the discrepancy taxonomy, the data model, and the API are specified in `06`, `07`, `08`, and `09` respectively.

---

## 2. The Problem, Stated Precisely

This section is written for an engineer who has not worked in payments. It is deliberately concrete, because the requirements that follow (SETTLEIQ-REQ-005 through REQ-009) only make sense against a correct picture of what settlement actually is.

### 2.1 What a payment settlement is

When a customer pays a merchant by card, the merchant does not receive the funds at the moment of payment. The sequence is:

1. The merchant's payment processor obtains an **authorisation** from the issuing bank — a promise to pay, not a payment.
2. When the merchant ships or fulfils, the processor **captures** the authorised amount. Capture converts a promise into a claim.
3. The processor, acting for the merchant's acquiring bank, submits captured transactions into the card-network **settlement** cycle. The networks move funds to the acquirer, net of interchange and scheme fees.
4. The processor now owes the merchant money, but not the gross captured amount. It owes gross captured **less** its own processing fees **less** refunds it has already returned to customers **less** chargebacks and dispute fees **less** any tax it withholds **plus or minus** adjustments, **converted** into the merchant's payout currency if the charge currency differs.
5. The processor discharges that obligation by transferring a single sum to the merchant's bank account. That transfer is the **payout**.

Settlement, then, is the process by which a ledger of charges, fees, refunds, chargebacks, and adjustments is extinguished by a bank transfer. The merchant's obligation — and the work SettleIQ addresses — is to account for that extinguishment: every unit of money that entered the ledger, every unit that left it, and the exact net that arrived at the bank.

Two consequences follow immediately, and they are the whole reason this project is shaped the way it is:

* The payout amount is a **derived** figure. It is the arithmetic result of its constituents. It is not an independent observation.
* The payout record is a **net**, and in general it does not describe its own composition.

### 2.2 What a payout is, precisely

A payout record, as a processor exposes it, carries at minimum: an amount; an expected and/or actual arrival date; a destination bank account; a status; and a currency. Where the processor's API exposes the balance transactions a payout was derived from, those are the constituents. Where it does not, the payout is a number with no attested contents.

The verification record is explicit on both sides of that boundary, and the evidence is Class A:

* For **automatic** payouts, Stripe provides a payout reconciliation report. That report is available only for automatic payouts; its data follows a separate processing schedule and can lag the arrival of the payout itself; the itemised PDF is capped at 5,000 rows; and Dashboard reports whole days only (docs.stripe.com/reports/payout-reconciliation, Class A, recorded in `12_DECISIONS_AND_OPEN_QUESTIONS.md` §Q1).
* For **manual and instant** payouts, Stripe declines to identify the composition at all: "You control the timing and amount of instant payouts, so Stripe can't identify which transactions are included in each payout. You're responsible for reconciling instant payouts against your transaction history." (docs.stripe.com/payouts/reconciliation, Class A, recorded in `12_DECISIONS_AND_OPEN_QUESTIONS.md` §Q1.)

So the processor's own documentation places decomposition — the attribution of constituents to payouts — on the merchant. That is the engineering problem. Adyen's documentation makes the same point from a different direction: payouts are net of transaction costs, refunds, and chargebacks, so the merchant must bridge gross-to-net, and settlement is additionally subject to a 1–2 business-day initiation window, up to three further days for the bank to credit, and bank-holiday non-processing (docs.adyen.com/account/getting-paid, Class A). Braintree states that its own Dashboard and Settlement Batch Summary "should not be used for reconciliation purposes" (developer.paypal.com/braintree, Class A). A third-party general-ledger integration note states plainly: "You need to reconcile manual payouts manually." (support.stripe.com, Xero integration note, Class A).

The consistent picture across four independent vendors is that the summary figures a processor or a GL tool produces are not reconciliation-grade, and that the merchant owns the decomposition.

### 2.3 Why payout-level comparison is insufficient

Payout-level comparison asks one question: does the processor's net figure equal the bank's received figure? It returns one bit. That single bit cannot support any of the work that follows from a discrepancy, for five distinct reasons.

**First, detection is not classification.** "Not equal, by −$118.40" does not say what broke. The same difference is produced by a charge absent from the processor ledger, an unexpected refund, a fee computed at a different rate or a different rate tier, an FX conversion at a different rate, a chargeback, a reserve or rolling-hold movement, a partial refund netted in, a rounding residue spread across hundreds of constituents, a charge captured after the payout figure was computed, or a duplicate. SETTLEIQ-REQ-008 requires a named type; a net difference cannot supply one.

**Second, compensating errors cancel.** Because the payout is a derived sum, two errors of opposite sign in two different constituents produce a net difference of zero. Payout-level comparison passes them silently. This is the most dangerous property of the approach: it fails *closed-looking* — it reports success. Charge-level matching would surface both errors, because each is checked against its own evidence.

**Third, there is no localisation.** A discrepancy investigation needs a subject: the specific charge, fee, refund, or adjustment that is wrong, and the specific field that disagrees. Aggregate net figures aggregate away identity. A difference at net level cannot be aged, assigned, or resolved, because there is nothing to point at. NetSuite's own documentation defines the discrepancy it reports as records "present in NetSuite and not present at the processor, or present at the processor and not present in NetSuite" (docs.oracle.com NetSuite Pay Transaction Reconciliation FAQ, Class A, verified as V15) — a **set** relationship, not a **sum** relationship. Net totals cannot express presence or absence except where the difference is uncompensated.

**Fourth, fee and FX composition is invisible in the net.** A payout total says nothing about how fees were attributed across charges, whether tax was withheld before or after fees, or which exchange rate was applied to which constituent. The master specification's decision rationale names exactly these cases — fee decomposition, withheld tax, refunds and disputes arriving mid-payout, and fee-net-of-tax — as the substance of the core problem, and names an FX rounding carryover as one of the injected defects the demonstration must classify.

**Fifth, timing is confounded with amount.** Refunds and disputes arrive mid-payout and change the net after the fact; Adyen's settlement involves a multi-day lag and bank-holiday gaps. A payout-level comparison performed at a single instant cannot separate "the amount is wrong" from "the record had not arrived yet," and therefore cannot route the break to the right resolution path.

A sixth point applies to the naive approach as a design: **it is founded on sources the sources themselves disclaim.** Braintree states its Settlement Batch Summary should not be used for reconciliation purposes; the Xero integration note states manual payouts must be reconciled manually; and NetSuite documents that a manual edit to a payment record makes its auto-settlement fail "since the amounts don't match" (V16) — vendor-published confirmation that amount-level matching is the brittle mode, and that resolving the break requires field-level evidence rather than a total.

The master specification's governing requirement follows from all of this. **SETTLEIQ-REQ-006: reconciliation shall operate at charge level, not payout level.**

### 2.4 What charge-level decomposition means

Charge-level decomposition is the inverse of the netting the processor performed. Given a payout and the processor's ledger, the engine derives the complete, individually attested set of constituents that the payout is the net of, expresses them as an explicit gross-to-net bridge, and then matches each constituent against the corresponding record on the other side.

The constituents are:

| Constituent | What it is |
|---|---|
| Charge | A captured authorisation: a claim the merchant holds on a cardholder, with amount, currency, capture timestamp, and processor fee |
| Fee | The processor's charge for handling the charge: per-transaction processing fee, plus cross-border, currency-conversion, and other fee types |
| Refund | A return of funds to the cardholder, full or partial, possibly netting against the payout |
| Chargeback / dispute | A reversal initiated by the cardholder through the issuing bank, plus the dispute fee |
| Adjustment | A processor-initiated correction, correction of an error, or a reserve/rolling-hold movement |
| FX conversion | Where the charge currency differs from the payout currency, the conversion of that constituent at an applicable rate |

The gross-to-net bridge is the algebraic statement that the derivation closes. Illustratively — the authoritative rounding and residual convention is an open question (OQ-02) and is to be settled in `07_RECONCILIATION_ENGINE_SPEC.md`, not here:

```
payout = Σ charges        (in payout currency)
       − Σ refunds
       − Σ chargebacks
       − Σ dispute fees
       + Σ adjustments
       − Σ processor fees
       − Σ withheld tax
       ± Σ FX conversion differences
```

Two properties of this bridge are requirements, not preferences:

* **It must close exactly, in `decimal.Decimal`.** SETTLEIQ-REQ-005 forbids binary floating point on any amount, fee, balance, or rounding computation. A bridge that closes only to within a float epsilon has not closed.
* **Every term must be individually attested or individually inferred.** Where the processor attests the attachment of a constituent to a payout, the engine records that as attested evidence. Where it does not — manual and instant payouts being the documented case — the engine derives the attachment from evidence and records the derivation as an inference carrying a confidence class, never as fact. This is the direct consequence of SETTLEIQ-REQ-007 and SETTLEIQ-REQ-009: insufficient evidence produces an unresolvable break, not a guess.

Once the bridge closes and each constituent is attested, matching proceeds constituent by constituent. A payout is not reconciled; a payout is the container within which its constituents are reconciled.

---

## 3. Actors

Four actors interact with SettleIQ. Each is a role, not a user account; the first build carries no authentication or user management (see §5).

| Actor | Role in this system | What they need from it |
|---|---|---|
| **Reconciliation engineer** | Builds, configures, and operates the reconciliation. Defines and versions the matching rules, runs reconciliation over a dataset, and interprets the run outcome. The primary technical user. | A rule set that is explicit and versioned; a run whose inputs, rule version, and outcome are all identifiable and reproducible; instrumentation they can trust |
| **Investigator** | Works the discrepancy queue to root-cause and resolve a single break: establishes which record is wrong, which field disagrees, what the resolution is, and confirms or rejects a proposed match. | A queue ordered by type and age; for one discrepancy, the contributing records, the fields that supported or contradicted a match, the rule trace, and the decision trail |
| **Auditor / reviewer** | Independent verification. Checks that the published auto-match rate is computed as its methodology says, that a prior run reproduces, and that the audit journal is intact. Represents the third party of SETTLEIQ-REQ-003 and the hiring-manager audience of the artifact. | The measurement methodology stated as code, not prose; byte-identical reproduction on re-run; a hash chain whose digests are computed by the system and verified on read |
| **Automated engine** | Performs decomposition, matching, confidence classification, typed discrepancy classification, provenance recording, journal append, and metric instrumentation. Acts within the fail-closed rule. | — (it is the system under specification) |

The human-confirmation path runs through the Investigator, and SETTLEIQ-REQ-013 requires the published rate to state its treatment of human-confirmed matches explicitly.

---

## 4. Use Cases

Use case identifiers UC-1 through UC-5 are normative: `12_DECISIONS_AND_OPEN_QUESTIONS.md` §Q4 binds each of the five dashboard views to one of them by name. UC-6 and UC-7 are additional and carry no dashboard binding.

### UC-1 — Reproducible Run

| Field | Value |
|---|---|
| Actor | Reconciliation engineer |
| Trigger | The engineer has a settled dataset (processor records, bank records) and needs to reconcile it |
| Preconditions | A dataset is loaded and identified by an input digest; a rule version is selected; the durable store is provisioned and migrations applied |

**Main flow**

1. The engineer triggers a reconciliation run for a stated dataset and rule version.
2. The engine computes and records the input digest and the rule version for the run.
3. The engine decomposes each payout into its constituents (UC-6), matches each constituent, and classifies what does not match.
4. The engine records per-decision provenance, appends journal entries, and increments instrumented counts.
5. The engine reports outcome counts: matched, unmatched-by-type, and unresolvable.

**Postconditions**

* A run record exists holding run ID, input digest, rule version, and outcome counts.
* Every match decision carries a provenance record per SETTLEIQ-REQ-007.
* Every unmatched difference carries a named type per SETTLEIQ-REQ-008.
* Re-running the same dataset at the same rule version yields byte-identical output (SETTLEIQ-REQ-012).

**Failure modes**

* The run cannot execute (missing input, unmigrated schema) — reported as a failed run, never as a zero-discrepancy run.
* A constituent cannot be attributed to a payout on the available evidence — the engine records an unresolvable break (SETTLEIQ-REQ-009) rather than attributing it.
* Non-determinism observed — a defect; determinism is tested, not asserted.

**Traces to:** SETTLEIQ-REQ-003, SETTLEIQ-REQ-012; dashboard "Run list" view per `12` §Q4.

---

### UC-2 — Triage the Discrepancy Queue

| Field | Value |
|---|---|
| Actor | Investigator |
| Trigger | A reconciliation run has completed producing typed discrepancies |
| Preconditions | A completed run exists; discrepancies are classified into named types and aged |

**Main flow**

1. The investigator opens the queue, ordered by type, severity, and age.
2. The investigator filters by type, severity, and age band, and drills through to one item.
3. For each item, the queue shows its named type, age, contributing record count, and whether it is unresolvable.

**Postconditions**

* Every queued item carries a named type from the taxonomy; no item is labelled "mismatch".
* Unresolvable breaks are visibly distinguished from breaks awaiting investigation.
* Ageing is derived from recorded timestamps, not from display logic.

**Failure modes**

* A difference cannot be classified into an existing named type — this is a taxonomy gap and must be surfaced as such, not forced into the nearest type. Whether the taxonomy is closed or closed-with-explicit-unknown is open question OQ-03.
* A queue item cannot be traced to a specific record — the item has no subject and cannot be resolved; it is reported as an unresolvable break.

**Traces to:** SETTLEIQ-REQ-008; dashboard "Discrepancy queue" view per `12` §Q4.

---

### UC-3 — Investigate a Single Discrepancy

| Field | Value |
|---|---|
| Actor | Investigator |
| Trigger | The investigator selects one discrepancy from the queue |
| Preconditions | The discrepancy exists with provenance and a decision trail |

**Main flow**

1. The investigator opens the detail view for one discrepancy.
2. The system shows the contributing records, the fields that supported or contradicted each candidate match, the rule that produced each decision, the confidence class, and the determinism guarantee.
3. The system shows the decision trail: what was proposed, by which rule, what a human did in response, and what changed after any sign-off.
4. The investigator confirms a proposed match, rejects it, or records a resolution.
5. The confirmation or rejection is written to the append-only journal with its own provenance.

**Postconditions**

* Every field shown traces to a recorded provenance entry; nothing in the view is reconstructed from prose.
* A human-confirmed match is recorded distinctly from an automated match, so that SETTLEIQ-REQ-013's stated treatment of human-confirmed matches can be applied to the published rate.
* A rejection or resolution appends a journal entry; it does not modify a prior one (SETTLEIQ-REQ-010).

**Failure modes**

* Provenance is incomplete for a decision — the decision cannot be shown and must not be shown as if complete; it is reported as lacking evidence.
* Evidence is insufficient to determine a match — the engine does not choose; it reports an unresolvable break (SETTLEIQ-REQ-009).

**Traces to:** SETTLEIQ-REQ-007, SETTLEIQ-REQ-009, SETTLEIQ-REQ-010; dashboard "Investigation detail" view per `12` §Q4.

---

### UC-4 — Measure the Auto-Match Rate

| Field | Value |
|---|---|
| Actor | Auditor / reviewer |
| Trigger | A reconciliation run has completed and its performance must be reported |
| Preconditions | Instrumented counts exist for the run; a measurement methodology is defined in code |

**Main flow**

1. The reviewer requests the metrics for a run.
2. The system computes the auto-match rate from recorded instrumented counts.
3. The system displays, alongside the figure: the denominator definition (what counts as an eligible record), the population in scope, the time window, and the treatment of AI-assisted or human-confirmed matches.
4. The reviewer checks the figure against the displayed methodology.

**Postconditions**

* The rate is computed and reported by the system from instrumented counts.
* The methodology is presented inline with the figure, as part of the artifact.
* The same inputs reproduce the same figure across runs.
* The figure is not stated in prose anywhere in the repository (SETTLEIQ-REQ-014).

**Failure modes**

* Counts are not instrumented for a category the denominator includes — the rate cannot be computed and is reported as uncomputable, with the missing count named.
* The denominator definition is ambiguous for a record class — the record class is excluded and the exclusion is stated, not silently absorbed.

**Traces to:** SETTLEIQ-REQ-013, SETTLEIQ-REQ-014; dashboard "Metrics" view per `12` §Q4.

---

### UC-5 — Reproduce a Prior Run

| Field | Value |
|---|---|
| Actor | Auditor / reviewer |
| Trigger | A third party must verify a previously reported result |
| Preconditions | A prior run's input digest, rule version, and recorded output are available |

**Main flow**

1. The reviewer selects a prior run.
2. The system re-executes the recorded input digest under the recorded rule version.
3. The system diffs the new outcome against the originally recorded outcome.

**Postconditions**

* The diff is empty, or the difference is itself explained by a recorded rule-version change.
* The reproduction is byte-identical for identical inputs and identical rule version (SETTLEIQ-REQ-012).
* A non-empty diff with no rule-version change is reported as a determinism defect.

**Failure modes**

* The prior input cannot be reconstructed from its digest — reported as irreproducible, not approximated.
* A rule-version difference explains the diff — the diff is reported as expected divergence, explicitly attributed to the version change.

**Traces to:** SETTLEIQ-REQ-003, SETTLEIQ-REQ-012; dashboard "Run history" view per `12` §Q4.

---

### UC-6 — Decompose a Payout into Charge-Level Components

| Field | Value |
|---|---|
| Actor | Reconciliation engineer (the decomposition is performed by the automated engine) |
| Trigger | A payout record must be reconciled (invoked within UC-1) |
| Preconditions | The processor ledger, the bank record, and the payout are available; Decimal context and rounding mode are configured |

**Main flow**

1. The engine collects the candidate constituents for a payout: charges, fees, refunds, chargebacks and dispute fees, adjustments, and FX conversions.
2. The engine attributes constituents to the payout using attested processor evidence where it exists, and derived evidence where it does not, recording which of the two applies to each.
3. The engine constructs the gross-to-net bridge and closes it exactly in `decimal.Decimal`.
4. Where the bridge does not close exactly, the engine applies the documented residual rule (OQ-02) and records the residual explicitly.
5. Each constituent is handed to the matcher as a separate subject.

**Postconditions**

* The payout is represented as a set of individually identified constituents, not as a total.
* Attributed and inferred attributions are distinguishable in the record.
* Every monetary value in the derivation is a `decimal.Decimal` with explicit context and rounding mode; no binary floating point appears on the path (SETTLEIQ-REQ-005).

**Failure modes**

* Constituents cannot be attributed on the available evidence (documented for manual and instant payouts) — the decomposition is recorded as incomplete and the affected constituents are reported as unresolvable breaks, not attributed by assumption.
* The bridge closes only with an unexplained residual — reported; a residual silently absorbed is a defect.
* A rounding convention is undefined for a case that arises — the run reports the case as unhandled (OQ-02) rather than inventing a convention mid-run.

**Traces to:** SETTLEIQ-REQ-005, SETTLEIQ-REQ-006, SETTLEIQ-REQ-009.

---

### UC-7 — Verify Audit Journal Integrity

| Field | Value |
|---|---|
| Actor | Auditor / reviewer |
| Trigger | A journal must be shown to be intact, or a tamper is suspected |
| Preconditions | Journal entries exist with computed digests |

**Main flow**

1. The reviewer requests journal verification.
2. The system recomputes each entry's digest over the previous entry's digest and the current entry's canonical serialization.
3. The system compares the recomputed digest chain to the stored chain and reports the first divergence, if any.
4. The reviewer inspects the tamper-injection test evidence, which demonstrates that verification detects a modification.

**Postconditions**

* Verification is a computed check performed on read; digests are never authored or hand-written.
* A divergence is reported as tampering or corruption with the offending entry identified.
* An intact chain is reported as intact, with the verification run identified.

**Failure modes**

* A stored digest does not equal the recomputed digest — integrity failure reported; the journal is not silently repaired.
* Canonical serialization is ambiguous — the chain cannot be verified and is reported as unverifiable rather than assumed valid.

**Traces to:** SETTLEIQ-REQ-010, SETTLEIQ-REQ-011.

---

## 5. Scope

### 5.1 In scope

* Ingestion of **synthetic, generator-produced** data only: processor-shaped transaction records, bank-shaped deposit records, and optional ledger-shaped records. No real processor credentials, no real bank feeds, no real customer data (SETTLEIQ-REQ-002).
* Canonical typed data model for charge, payout, fee, refund, adjustment, bank deposit, and discrepancy, with `decimal.Decimal` money (SETTLEIQ-REQ-005).
* A frozen `SourceAdapter` interface, with a Stripe-shaped adapter, defined before either adapter is written so that Adyen is additive rather than a rewrite (`12` §Q1).
* **Stripe-only for the first build** — **RECOMMENDED, awaiting OWNER ratification** (rationale in `12` §Q1). This is not a ratified decision and nothing may be built against it until it is.
* Payout-to-constituent decomposition and gross-to-net bridging, with FX and fee attribution (SETTLEIQ-REQ-006).
* Deterministic, rule-based matching with confidence classification and ambiguous-case routing (SETTLEIQ-REQ-007, SETTLEIQ-REQ-012).
* A named, explicit, exhaustive discrepancy taxonomy with ageing and root-cause attribution (SETTLEIQ-REQ-008).
* Fail-closed behaviour: unresolvable breaks reported, never guessed (SETTLEIQ-REQ-009).
* An append-only, hash-chained audit journal with computed-and-verified digests (SETTLEIQ-REQ-010, SETTLEIQ-REQ-011).
* Instrumented counts and a methodology-defined auto-match rate, computed by the system (SETTLEIQ-REQ-013, SETTLEIQ-REQ-014).
* A **Python-only core** — **RECOMMENDED, awaiting ratification** (rationale and the conditional C++17 four-part gate in `12` §Q2). A C++17 component is justified only if all four conditions hold; none has been tested.
* **PostgreSQL provisioned via Docker Compose as the sole durable store**, with `numeric` amount columns — **RECOMMENDED, awaiting ratification** (rationale and required properties in `12` §Q3). Note that the exact `numeric` scale is **OPEN**: ISO minor-unit exponents vary by currency (JPY has 0, BHD has 3), so a single fixed scale cannot be assumed. Unconstrained `numeric` with per-currency exponent validation is the working position; the width decision is deferred to `06`.
* A REST + OpenAPI surface and a **five-view investigation dashboard**, one functional requirement per named use case, nothing decorative — **RECOMMENDED, awaiting ratification** (view-to-use-case binding in `12` §Q4).
* Tests: unit, property-based Decimal invariants, determinism, fault and tamper injection; plus a **conditional** benchmark of the hot path with stated honest limits — produced only if the four gating conditions in `12` §Q2 are satisfied, and otherwise produced not at all rather than produced empty.
* Role emphasis: **primary, financial systems and ledgering engineering; supporting frame, backend engineering** — **RECOMMENDED, awaiting ratification** (rationale in `12` §Q5). This one is load-bearing: **Q5 should be ratified before Q2, because Q2's conditional C++17 gate depends on it.**

### 5.2 Out of scope

The following are out of scope for the first build and are not to be reintroduced by a subordinate document:

1. **Live money movement.** No connection to any real payment rail, real bank account, or real transfer.
2. **Real customer data.** No real cardholder, merchant, or transaction data of any kind. Synthetic generator-produced data only.
3. **Multi-tenancy.** Single-tenant, single-workspace operation.
4. **Authentication UI, user management, authorization, and roles.**
5. **Adyen in the first build.** The adapter interface is designed to absorb it; the adapter is not built in the first build.
6. **A C++17 production component.** No C++17 in the first build. A C++17 hot-path benchmark is a conditional later milestone, gated on all four conditions in `12` §Q2, and is never a production dependency.
7. **Any competitive or commercial claim.** No claim about any named product or vendor, no market-gap claim, no market-size claim, no product-market-fit claim, no willingness-to-pay claim, no pricing recommendation, no go-to-market plan, no buyer-validation artifact (SETTLEIQ-REQ-000, SETTLEIQ-REQ-001).
8. **Real-data mode.** Excluded from the first build by SETTLEIQ-REQ-002. Whether it is ever desirable is open question OQ-05 and is deliberately unanswered.
9. **Real-time streaming, mobile layout, theming, component libraries, and design systems** until a functional requirement demands them.
10. **A Java service.** None. Recorded explicitly in `12` §Q2 as a deliberate exclusion.

---

## 6. Failure Modes of Naive Payout-Level Reconciliation

These are the failure modes of the approach SettleIQ rejects. Each is grounded either in the Class A verification record (`02_verification_log.md`, `12_DECISIONS_AND_OPEN_QUESTIONS.md` §Q1, `SETTLEIQ-MASTER-SPEC-001` §1.2) or in the arithmetic properties of §2.3. No statistic is asserted here; none exists in the sources.

| ID | Failure mode | Why it follows |
|---|---|---|
| FM-P1 | **Detection without classification.** A net difference yields one bit and no named type | The same difference is produced by at least ten distinct causes (§2.3). SETTLEIQ-REQ-008 requires a named type; the net cannot supply one |
| FM-P2 | **Compensating errors cancel silently.** Two errors of opposite sign in different constituents produce a net difference of zero, and the comparison reports success | The payout is a derived sum. This is the most dangerous mode because it fails closed-looking |
| FM-P3 | **No localisation.** An aggregate difference has no subject record, so it cannot be aged, assigned, or resolved | NetSuite's own published definition of its open-settlement break is a presence/absence relationship (V15, Class A) — a set difference, which a total cannot express |
| FM-P4 | **Fee, tax, and FX composition are invisible in the net** | The processor's fee structure (per-charge fee, cross-border, conversion, fee-net-of-tax, withheld tax) is not observable in a payout total; the master rationale names these as the substance of the core problem, and an FX rounding carryover as an injected defect to be classified |
| FM-P5 | **Rounding residue distributed across constituents.** A net difference that no single constituent explains | With exact-decimal arithmetic the residue is computable and attributable; at net level it is merely unexplained |
| FM-P6 | **Timing confounded with amount.** Refunds and disputes arrive mid-payout and change the net after the fact | Adyen documents a 1–2 business-day initiation window, up to three further days to bank credit, and bank-holiday non-processing (Class A). A single-instant comparison cannot separate "wrong amount" from "not yet arrived" |
| FM-P7 | **No attested composition exists to compare against.** For manual and instant payouts the processor explicitly declines to identify which transactions are in each payout | Stripe, Class A, `12` §Q1. A payout-level comparison has nothing to decompose, and the merchant is told to reconcile them itself against transaction history |
| FM-P8 | **The comparison is founded on sources their own vendors disclaim.** Braintree states its Settlement Batch Summary "should not be used for reconciliation purposes"; the Xero integration note states manual payouts must be reconciled manually; NetSuite documents that a manual edit breaks its amount-based auto-settlement | All Class A. Building on vendor summary totals builds on figures the vendors themselves say are not reconciliation-grade |
| FM-P9 | **Amount-level matching is the brittle mode.** NetSuite documents auto-settlement failing "since the amounts don't match" after a manual edit (V16) | A field-level evidence base resolves the break; a total does not |
| FM-P10 | **The integration path itself may be blocked.** Raw bank statement lines are not exposed by one major GL vendor's public API, for regulatory reasons | V9, V10 (Class A). Any design that assumes GL-mediated access to unreconciled statement lines cannot be built; this is a constraint on the design, not a weakness to exploit |

**What SettleIQ does instead:** it reconciles at charge level (SETTLEIQ-REQ-006), names every unmatched difference (SETTLEIQ-REQ-008), carries provenance for every decision (SETTLEIQ-REQ-007), closes the gross-to-net bridge exactly in Decimal (SETTLEIQ-REQ-005), and reports unresolvable rather than guessing (SETTLEIQ-REQ-009). Whether it does so is a matter for executed tests, not for this document.

---

## 7. Explicit Statement of Status

Nothing in this document is implemented. No use case above has been executed. No failure mode above has been observed in SettleIQ's own data. This document states intended problem framing and intended behaviour, and is subordinate to `SETTLEIQ-MASTER-SPEC-001`. Intent and implementation are never presented in the same register (SETTLEIQ-REQ-004).
