# 06 — Data Model and Persistence

**Document ID:** SETTLEIQ-DATA-001
**Title:** Data Model and Persistence Specification
**Version:** 1.0.0
**Status:** PROPOSED — specification only; no implementation claimed
**Date:** 2026-10-28
**Canonical path:** `docs/specifications/06_DATA_MODEL_AND_PERSISTENCE.md`
**Owner:** Bukya Naresh (CN2)
**Traces to:** SETTLEIQ-MASTER-SPEC-001 §2.2 (SETTLEIQ-REQ-005, REQ-006), §2.3 (SETTLEIQ-REQ-009…REQ-012), §8 row 06; SETTLEIQ-DEC-001 Q3

---

## Document Control

### Classification note — RESOLVED DEFECT (added 2026-10-28)

Requirements `R01`–`R16` restate master OWNER-DEFINED requirements and are correctly classified OWNER-DEFINED.

Requirements `R17` onward are **schema-design requirements that presuppose the unratified Q3 decision** to use PostgreSQL via Docker Compose. They are therefore classified **PROPOSED**, not OWNER-DEFINED, and are read as such for that reason. If Q3 is ratified differently, those sections are rewritten and the rewrite recorded; the OWNER-DEFINED requirements above are unaffected.

An earlier draft of this document classified several schema requirements as OWNER-DEFINED while resting on an unratified decision. That classification was flagged during review and is corrected here. The requirement text itself is unchanged; only its classification is corrected.

### Purpose

This document defines the canonical domain model for SettleIQ, the persistence requirements for that model in PostgreSQL, the migration policy, the transaction boundaries around the audit journal and ledger writes, and the deterministic fixture-generation contract. It is the sole authority for how SettleIQ represents money, identity, and history.

### Status and classification convention

Requirements are classified:

* **OWNER-DEFINED** — restated from a binding requirement of `SETTLEIQ-MASTER-SPEC-001` or `SETTLEIQ-DEC-001`. These may only change by explicit OWNER decision.
* **PROPOSED** — recommended by this specification. Not binding until ratified by the OWNER.

Nothing in this document is implemented. No schema exists, no migration has run, no fixture has been generated, and no test has executed.

### Scope and authority

* The sole durable store is PostgreSQL, provisioned via Docker Compose (SETTLEIQ-DEC-001 Q3). SQLite is permitted only for ephemeral in-process test fixtures and shall never be used to validate properties that PostgreSQL enforces (constraints, locking, privileges).
* The canonical domain model defined here is the boundary of the `SourceAdapter` contract in `09_API_AND_INTEGRATION_SPEC.md`. The adapter interface is frozen at milestone M1 before any adapter is written; this model is therefore also frozen at M1.
* Decomposition, matching rules, the discrepancy taxonomy, and confidence classification are owned by `07_RECONCILIATION_ENGINE_SPEC.md` and `08_DISCREPANCY_AND_AUDIT_SPEC.md`. This document specifies how those concepts are persisted, not how they are computed.

### What this document does not claim

No schema has been created. No migration has been executed. No concurrency test has been run. No fixture manifest exists. No auto-match rate has been computed. Where a decision is unresolved, this document says so rather than inventing an answer.

---

## 1. Design Principles

The following principles are binding on every table, column, constraint, and query in SettleIQ. Each is restated as a SettleIQ-owned requirement; none is cited from an external governance source.

### 1.1 Decimal-only money

**SETTLEIQ-DATA-R01 (OWNER-DEFINED):** All monetary amounts shall be `decimal.Decimal` with an explicit context (precision) and an explicit rounding mode, declared once, reused everywhere, and recorded where a rounding event occurs. Binary floating point shall not appear on any monetary path — domain, persistence, serialization, or API boundary. Any use of binary float on a monetary value is a defect, including float introduced accidentally by JSON number parsing or a third-party dependency.

**SETTLEIQ-DATA-R02 (OWNER-DEFINED):** Every amount shall be stored and transported with its explicit currency. A bare numeric amount without a currency code is a schema defect. Money shall never be implicitly converted between currencies; an FX conversion result is derived money and is governed by R04.

### 1.2 Immutability of settled records

**SETTLEIQ-DATA-R03 (OWNER-DEFINED):** Records derived from a settled processor or bank source are immutable once committed. A correction is never an in-place update; it is a new record that supersedes the original via an explicit `supersedes` reference, with the original retained and readable. This applies to charges, fees, refunds, adjustments, payouts, settlement batches, and bank deposits. It is the persistence expression of the auditability requirement: history is reconstructable at any point in time.

### 1.3 No derived money without recorded derivation

**SETTLEIQ-DATA-R04 (OWNER-DEFINED):** No derived monetary value shall be persisted without a recorded derivation. A derivation record states which rule (identifier and version) produced the value, which input records contributed, what context precision and rounding mode were applied, and how any residual was allocated. Examples that require derivation records: payout gross-to-net bridge residuals, fee attribution across charges, refund or dispute aggregates, FX conversion results, and tax-on-fee computations. Aggregates that are not persisted (computed on read) are exempt from the storage requirement but not from the derivation requirement — the read path must be able to state the same rule, inputs, rounding, and residual handling.

### 1.4 Charge-level reconciliation unit

**SETTLEIQ-DATA-R05 (OWNER-DEFINED):** Reconciliation operates at charge level (SETTLEIQ-REQ-006). The schema shall represent a payout as a container of constituents — charges, fees, refunds, and adjustments — each individually identifiable and individually matchable. A payout's processor-asserted total shall be stored only as a bridge target for gross-to-net decomposition validation. No equivalence between payout totals shall ever constitute a match, and no column pair shall exist whose comparison would permit it.

### 1.5 Provenance and fail-closed persistence

**SETTLEIQ-DATA-R06 (OWNER-DEFINED):** Every match decision persisted shall carry its provenance: the fields used, the rule (identifier and version) that produced it, the confidence classification, and the determinism guarantee (deterministic / ambiguous / human-required) (SETTLEIQ-REQ-007).

**SETTLEIQ-DATA-R07 (OWNER-DEFINED):** Where evidence is insufficient, the engine reports an unresolvable break (SETTLEIQ-REQ-009). The persistence layer shall not offer any mechanism — nullable "best guess" columns, silent defaults, or absorbing adjustments — by which an unresolved state could be stored as or read back as a resolved one.

### 1.6 Computed digests, verified on read

**SETTLEIQ-DATA-R08 (OWNER-DEFINED):** Audit journal entry digests are computed by the system over the previous entry's digest and the current entry's canonical serialization, and are verified on read (SETTLEIQ-REQ-011). A hand-written, patterned, or placeholder digest is a critical defect and shall be treated as fabricated evidence.

### 1.7 Determinism and its scope

**SETTLEIQ-DATA-R09 (OWNER-DEFINED):** Given identical inputs and identical rule version, the engine shall produce byte-identical outputs (SETTLEIQ-REQ-012). Consequently:

1. No persisted identity may be derived from randomness, wall-clock time, or process-local counters. Run, decision, discrepancy, and journal identifiers are derived from recorded inputs or from deterministic sequence numbers.
2. Ambient clock readings (for example `recorded_at`, `started_at`) are persisted for operational use but are excluded from every digest preimage and from every output digest. The byte-identity contract covers canonical serializations and digest chains; ambient timestamps are outside it and this exclusion is explicit rather than incidental.

---

## 2. Canonical Domain Model

### 2.1 Modelling conventions

**SETTLEIQ-DATA-R10 (PROPOSED):** The entity set below is fixed at M1. Adding, renaming, or removing an entity requires an OWNER decision recorded in `12_DECISIONS_AND_OPEN_QUESTIONS.md`.

**SETTLEIQ-DATA-R11 (OWNER-DEFINED):** Enumerated values use a canonical vocabulary defined in this specification. A source value with no canonical mapping is a normalization failure: the adapter raises a normalization error and the ingestion fails closed. Silent mapping of an unmapped value to a catch-all (`other`, `unknown`, `miscellaneous`) is prohibited.

**SETTLEIQ-DATA-R12 (PROPOSED):** Instants are stored as UTC instants and serialized as RFC 3339 with fixed precision. Business dates (value date, arrival date, settlement period boundaries) are stored as calendar dates (`DATE`) without timezone, because the processor or bank defines them as business dates, not instants. The mapping from a source timestamp to instant-or-date is part of the adapter normalization contract in `09_API_AND_INTEGRATION_SPEC.md`.

### 2.2 Entities

For each entity: purpose, key fields with types, identity strategy, immutability rules. The field lists below fix the fields that carry requirements; the exhaustive column set is produced in the checked-in migration DDL under this specification and shall not add semantic content beyond what is recorded here.

#### 2.2.1 Charge

**Purpose.** A single authorized or captured card payment — the atomic unit on which reconciliation operates (R05).

**Key fields.**

| Field | Type | Notes |
|---|---|---|
| `charge_id` | surrogate, opaque string | internal identity |
| `source_adapter_id` | string | which adapter ingested it |
| `processor_charge_id` | string | processor's identifier, opaque, never interpreted |
| `run_id` | string | ingestion run that produced this record |
| `amount` | numeric | created amount |
| `currency` | char(3) | ISO 4217 alpha-3, FK to `currency` |
| `captured_amount` | numeric, nullable | only when the processor reports capture separately from authorization |
| `status` | enum | canonical vocabulary: `authorized`, `captured`, `failed`, `refunded`, `partially_refunded` |
| `authorized_at`, `captured_at` | timestamptz / date, nullable | provenance timestamps |
| `supersedes` | string, nullable | FK to `charge_id`; set on a correcting record |

**Identity.** Natural key `(source_adapter_id, processor_charge_id)`, unique per ingestion scope; `charge_id` is the durable surrogate used by foreign keys. Two records for the same natural key within one ingestion are a duplicate-detection failure, not an upsert.

**Immutability.** Immutable on commit (R03). A processor-side correction (amount revision, status change) produces a new row with `supersedes` set; the original row remains readable and is never updated.

#### 2.2.2 Fee

**Purpose.** A processor charge that reduces merchant proceeds — the fee constituent of a payout.

**Key fields.**

| Field | Type | Notes |
|---|---|---|
| `fee_id` | surrogate | internal identity |
| `processor_fee_id` | string | opaque processor identifier |
| `charge_id` | FK to `charge`, nullable | when the fee is attributable to a charge |
| `payout_id` | FK to `payout`, nullable | when the fee is payout-level and not attributable to a single charge |
| `amount` | numeric | fee amount |
| `currency` | char(3) | FK |
| `fee_type` | enum | canonical vocabulary: `processing`, `cross_border`, `fx_conversion`, `dispute`, `payout_transfer`, `tax_on_fee`, `other_named` — see OPEN item N-05 |
| `tax_amount` | numeric, nullable | tax levied on the fee, when disclosed |
| `amount_basis` | enum | `gross` or `net_of_tax` — states whether `amount` includes `tax_amount` |
| `supersedes` | string, nullable | correction chain |

**Identity.** Natural key `(source_adapter_id, processor_fee_id)`.

**Immutability.** Immutable on commit. The `amount_basis` column exists because processor fee disclosure varies (a fee may be reported gross or net of tax); leaving basis implicit would let the same column mean two different things, which is a Decimal-correctness defect. At least one of `charge_id` / `payout_id` shall be non-null (a database CHECK), and never both for the same row — a fee attaches to exactly one parent scope.

#### 2.2.3 Refund

**Purpose.** A return of funds to the cardholder, full or partial, possibly arriving after the payout that contained the original charge.

**Key fields.**

| Field | Type | Notes |
|---|---|---|
| `refund_id` | surrogate | internal identity |
| `processor_refund_id` | string | opaque |
| `charge_id` | FK to `charge` | the refunded charge |
| `amount` | numeric | refund amount |
| `currency` | char(3) | FK |
| `status` | enum | `pending`, `succeeded`, `failed`, `canceled` |
| `reason` | enum, nullable | canonical vocabulary, adapter-mapped |
| `created_at` | timestamptz | when the processor recorded it |

**Identity.** Natural key `(source_adapter_id, processor_refund_id)`.

**Immutability.** Immutable on commit.

#### 2.2.4 Adjustment

**Purpose.** A non-charge, non-fee, non-refund movement that changes merchant proceeds: reserves withheld or released, chargebacks, dispute lifecycle events, tax corrections, FX gains and losses.

**Key fields.**

| Field | Type | Notes |
|---|---|---|
| `adjustment_id` | surrogate | internal identity |
| `processor_adjustment_id` | string | opaque |
| `type` | enum | canonical vocabulary: `reserve_withheld`, `reserve_released`, `chargeback`, `dispute_reopened`, `dispute_won`, `tax_correction`, `fx_gain`, `fx_loss` — adapter-mapped, unmapped fails closed |
| `amount` | numeric | signed: negative reduces proceeds, positive increases |
| `currency` | char(3) | FK |
| `effective_date` | date | business date the processor applied it |
| `related_entity_type`, `related_entity_id` | string pair, nullable | optional link to a charge or payout |

**Identity.** Natural key `(source_adapter_id, processor_adjustment_id)`.

**Immutability.** Immutable on commit. Signed `amount` is required; encoding direction in a separate sign column is prohibited.

#### 2.2.5 Payout

**Purpose.** A single transfer of funds from the processor to the merchant's bank account. A container of constituents, never a reconciliation unit (R05).

**Key fields.**

| Field | Type | Notes |
|---|---|---|
| `payout_id` | surrogate | internal identity |
| `processor_payout_id` | string | opaque |
| `settlement_batch_id` | FK to `settlement_batch`, nullable | when the processor groups payouts into batches |
| `amount` | numeric | processor-asserted transferred amount; bridge target only |
| `currency` | char(3) | FK |
| `method` | enum | `standard`, `instant`, `manual` — see note below |
| `status` | enum | `pending`, `in_transit`, `paid`, `failed`, `canceled` |
| `expected_arrival_date`, `actual_arrival_date` | date, nullable | settlement timing |
| `composition_disclosed` | boolean | whether the processor disclosed this payout's constituent list |

**Identity.** Natural key `(source_adapter_id, processor_payout_id)`.

**Immutability.** Immutable on commit.

**Note on `composition_disclosed`.** Processor documentation establishes that payout composition is not always identifiable by the processor (for example, instant and manual payouts on Stripe). The column records that fact as data so the decomposer can treat a non-disclosed payout as requiring inference rather than assuming a constituent list exists. This is the persistence-level defence against baking one processor's disclosure behaviour into the engine.

#### 2.2.6 SettlementBatch

**Purpose.** A processor-side grouping of transactions that feeds one or more payouts. On Stripe this is the settlement batch; on Adyen the equivalent is a settlement batch reference. The batch is retained because processors net across batch boundaries and the batch is the natural scope of a processor-side assertion.

**Key fields.**

| Field | Type | Notes |
|---|---|---|
| `settlement_batch_id` | surrogate | internal identity |
| `processor_batch_id` | string | opaque |
| `settlement_date` | date | business date |
| `currency` | char(3) | FK |
| `processor_asserted_total` | numeric, nullable | processor's own figure for the batch, if disclosed |

**Identity.** Natural key `(source_adapter_id, processor_batch_id)`.

**Immutability.** Immutable on commit. `processor_asserted_total` is stored with the provenance "processor-asserted" and is never used as a reconciliation unit (R05); it is a bridge target.

#### 2.2.7 BankTransaction (deposit)

**Purpose.** The bank-side record: money actually arriving in the merchant account. The second side of reconciliation.

**Key fields.**

| Field | Type | Notes |
|---|---|---|
| `bank_transaction_id` | surrogate | internal identity |
| `deposit_feed_id` | string | which deposit feed ingested it |
| `bank_account_ref` | string | opaque account reference |
| `amount` | numeric | deposited amount |
| `currency` | char(3) | FK |
| `value_date` | date | business date |
| `external_reference` | string, nullable | bank-supplied reference, may be absent |
| `remittance_information` | string, nullable | free text as supplied |
| `matched_status` | enum | `unmatched`, `matched`, `partially_matched` — maintained by the engine |

**Identity.** Bank deposits frequently lack a stable natural key. Identity is a deterministic surrogate derived from the canonical serialization of the ingested record (see 2.1 conventions); duplicate detection across overlapping ingestion windows is a matching-engine concern, not a persistence upsert. No heuristic identity (amount + date + reference) is permitted, because a heuristic identity collides on legitimate repeat deposits and would merge two distinct events.

**Immutability.** Immutable on commit, except `matched_status`, which is engine-maintained state and is updated only through the engine's own transaction boundary (Section 6).

#### 2.2.8 ReconciliationRun

**Purpose.** One execution of the engine over one identified input set under one rule version. The unit of reproducibility.

**Key fields.**

| Field | Type | Notes |
|---|---|---|
| `run_id` | string | derived, see Section 3 |
| `input_digest` | string | SHA-256 over canonical serialized inputs |
| `rule_version` | string | rule set version |
| `schema_version` | integer | migration version at run time |
| `generator_version` | string, nullable | set when the input is a generated fixture |
| `adapter_versions` | string map | adapter id → version for every contributing source |
| `status` | enum | `pending`, `running`, `completed`, `failed` |
| `started_at`, `completed_at` | timestamptz | operational only, outside digest preimage (R09) |
| `outcome_counts` | counts, embedded | instrumented counts, see `07`/`08` |

**Identity.** See Section 3.

**Immutability.** Status transitions are engine state, not settled data. The run's identifying tuple `(run_id, input_digest, rule_version, schema_version)` is immutable after creation; `outcome_counts` are written only at completion, in the same transaction as the run's terminal status.

#### 2.2.9 MatchDecision

**Purpose.** The record of one match attempt's outcome between two charge-level records, carrying its provenance (R06).

**Key fields.**

| Field | Type | Notes |
|---|---|---|
| `decision_id` | string | deterministic within run |
| `run_id` | FK to run | the run that produced it |
| `rule_id`, `rule_version` | string | which rule produced it |
| `left_ref`, `right_ref` | entity-type/id pairs | the two sides matched (charge ↔ payout constituent, constituent ↔ deposit) |
| `matched_fields` | canonical JSON array | `{field, left_value, right_value}`; money values serialized as decimal strings |
| `confidence_class` | enum | owned by `07` |
| `determinism_guarantee` | enum | `deterministic`, `ambiguous`, `human_required` |
| `decided_by` | enum | `engine`, `human` |
| `evidence_digest` | string | SHA-256 over the canonical serialization of the decision payload; computed by the system |
| `supersedes` | string, nullable | a later decision replacing an earlier one |

**Identity.** Deterministic within the run from rule evaluation order (R09); unique per `(run_id, decision_id)`.

**Immutability.** Immutable on commit. A human confirmation does not mutate the decision; it appends a confirmation record (Section 2.2.10 note and `09` endpoint `POST /v1/decisions/{decisionId}/confirmations`). A re-evaluation supersedes via a new row.

#### 2.2.10 Discrepancy

**Purpose.** A named, typed break produced when reconciliation cannot establish a match or establishes a difference with a classified cause.

**Key fields.**

| Field | Type | Notes |
|---|---|---|
| `discrepancy_id` | string | deterministic within run |
| `run_id` | FK to run | |
| `type` | enum code | from the named taxonomy owned by `08`; not free text |
| `severity` | enum | owned by `08` |
| `status` | enum | `open`, `under_investigation`, `resolved`, `unresolvable` |
| `raised_at` | timestamptz | |
| `source_refs` | entity refs | contributing records |
| `contributing_decision_ids` | string array | the decisions this break derives from |

**Identity.** Deterministic within the run; unique per `(run_id, discrepancy_id)`.

**Immutability.** The identifying fields (`type`, `run_id`, `source_refs`, `raised_at`) are immutable. Status is engine- and human- workflow state; every transition is an event in `discrepancy_event` (below), so the resolution history required by the dashboard is reconstructable without the mutable row being the source of truth.

#### 2.2.11 DiscrepancyEvent (supporting entity)

**Purpose.** Append-only history of one discrepancy: status transitions, human confirmations, resolutions, unresolvable declarations. The dashboard's "resolution history" requirement reads this table; the mutable `status` column exists for query efficiency only.

**Key fields.**

| Field | Type | Notes |
|---|---|---|
| `event_id` | string | deterministic within discrepancy |
| `discrepancy_id` | FK | |
| `event_type` | enum | `raised`, `acknowledged`, `investigating`, `resolved`, `unresolvable`, `reopened`, `note_added` |
| `occurred_at` | timestamptz | operational timestamp |
| `actor` | enum | `engine`, `human` |
| `payload` | canonical JSON | resolution code, note, evidence references |

**Immutability.** Immutable on commit. No updates, no deletes.

#### 2.2.12 AuditJournalEntry

**Purpose.** The hash-chained append-only record of actions taken by the system (R08). The journal's computation and verification semantics are owned by `08`; this document fixes its persistence shape.

**Key fields.**

| Field | Type | Notes |
|---|---|---|
| `entry_id` | bigint sequence | monotonic within `chain_id`; deterministic |
| `chain_id` | string | the chain (per run, per store scope as defined in `08`) |
| `sequence` | bigint | position in chain, starts at 1 |
| `prev_digest` | string(64) | previous entry's digest; genesis is the recorded zero constant |
| `entry_digest` | string(64) | SHA-256 over the canonical preimage |
| `canonical_payload` | text | canonical serialization of the action, entity refs, actor |
| `recorded_at` | timestamptz | operational only, excluded from the preimage (R09) |

**Identity.** `(chain_id, sequence)` unique.

**Immutability.** Append-only, enforced at the database level: the application role holds `INSERT` and `SELECT` only; `UPDATE` and `DELETE` are revoked, and a `BEFORE UPDATE OR DELETE` trigger raises as defence-in-depth against a mis-granted role.

### 2.3 Supporting tables

| Table | Purpose |
|---|---|
| `currency` | ISO 4217 code (PK), minor-unit exponent (0, 2, 3, …), name. Drives per-currency scale validation (Section 4.1). Rows are reference data added by migration only. |
| `rule_version` | Registered rule sets: `rule_id`, `version`, `definition_digest`. A run may only reference a registered row (FK). |
| `derivation_record` | R04 enforcement: `derivation_id`, `rule_id`, `rule_version`, input refs, context precision, rounding mode, residual handling, produced-value reference. |
| `fixture_manifest` | Section 7: generator identity and the input digest of a seeded dataset. |
| `idempotency_record` | Section 4 of `09`: idempotency key → request digest, response snapshot, status. |

### 2.4 Relationships

* `charge` 1—N `fee`, `refund` (a fee or refund attaches to one charge or, for fees, one payout).
* `settlement_batch` 1—N `payout` (a batch may contain several payouts; a payout belongs to at most one batch).
* `payout` 1—N constituents (charges, fees, refunds, adjustments) via decomposition links held in the decomposition structures owned by `07`; the FK skeleton above is sufficient to express them.
* `bank_transaction` N—1 match to constituents via `match_decision` (never directly).
* `reconciliation_run` 1—N `match_decision`, `discrepancy`, `audit_journal_entry`.
* `discrepancy` 1—N `discrepancy_event`.
* `match_decision` 1—N human confirmations (separate table, owned by `09`/metrics).

---

## 3. Reconciliation Run Identity

A run is reproducible if and only if its identity tuple is fully recorded. The tuple is:

**`run_id` = `run-` + hex(SHA-256(canonical(input_digest ‖ rule_version ‖ schema_version))[0:24])`**

where `input_digest`, `rule_version`, and `schema_version` are defined below.

**SETTLEIQ-DATA-R13 (OWNER-DEFINED):** `run_id` shall be derived deterministically from the tuple above. It shall not be a random UUID, a client-supplied value, or a database sequence. Two triggers of the same input under the same rule and schema version produce the same `run_id`; the second is recognized as the same run, not a second run.

**SETTLEIQ-DATA-R14 (OWNER-DEFINED):** `input_digest` shall be the SHA-256 digest over the canonical serialization of the complete input set: every source record ingested (charges, fees, refunds, adjustments, payouts, batches, deposits), the fixture manifest when the input is generated, and the identity and version of every contributing adapter or generator. Changing any input byte changes the digest and therefore the run identity.

**SETTLEIQ-DATA-R15 (PROPOSED):** Canonical serialization shall be pinned: UTF-8 encoding, a fixed field order defined per record type, no insignificant whitespace, all monetary values serialized as decimal strings (never JSON numbers), all enumerations as their canonical names, all timestamps as RFC 3339 UTC at fixed precision. The digest algorithm and the serialization rules are themselves versioned; a change to either is a `schema_version`-level change.

**SETTLEIQ-DATA-R16 (OWNER-DEFINED):** `rule_version` identifies the rule set (registry row in `rule_version`), and `schema_version` identifies the migration level. Both are recorded on the run and referenced by every decision and discrepancy it produces. A result is reproducible only within the same tuple; the API shall refuse to present results across differing rule versions without labelling the difference (see `09`).

---

## 4. PostgreSQL Schema Requirements

### 4.1 Money columns

**SETTLEIQ-DATA-R17 (OWNER-DEFINED):** Amount columns shall be `numeric` — never `float8`, `double precision`, `real`, or integer-cents with implicit scaling. Each amount column shall carry a database CHECK rejecting non-finite values (`NaN`; PostgreSQL `numeric` is otherwise exact). The application role shall not hold privileges to alter or drop these constraints.

**Scale.** PostgreSQL `numeric(p, s)` rounds a value that exceeds the declared scale instead of failing. A fixed global scale would therefore silently round amounts from currencies with a finer minor unit (for example 3-decimal currencies) and would quietly violate R01. The correct scale is per-currency, driven by `currency.minor_unit_exponent`. The interim requirement is: unconstrained `numeric` for storage, application-enforced scale validation against the row's currency exponent, and the declared-width decision recorded as OPEN item N-01 (Section 8). Any future declared width shall be paired with a test proving that an out-of-scale insert raises rather than rounds.

**SETTLEIQ-DATA-R18 (OWNER-DEFINED):** Every amount column shall be accompanied by a currency column referencing `currency(code)`. The amount-and-currency pair is atomic: no row may carry an amount without its currency or a currency without its amount. The NOT NULL discipline of R19 makes each column individually non-null; a database CHECK on the row makes the pairing explicit so a future migration that relaxes nullability cannot produce a bare amount. No monetary column shall exist without its currency.

### 4.2 Currency columns

**SETTLEIQ-DATA-R18a (PROPOSED):** Currency codes shall be stored as `char(3)` with a CHECK enforcing the ISO 4217 alpha-3 pattern and a foreign key to `currency`. Free-text currency fields are prohibited.

### 4.3 NOT NULL discipline

**SETTLEIQ-DATA-R19 (OWNER-DEFINED):** Every column shall be `NOT NULL` unless its nullability is explicitly justified in the migration comment with the condition that produces the null. Nullable columns shall be limited to genuinely processor-absent facts (for example `captured_amount` where the source reports authorization only). No surrogate key, no `run_id`, no enum, and no money-or-currency pair shall be nullable.

### 4.4 Foreign keys and immutability enforcement

**SETTLEIQ-DATA-R20 (OWNER-DEFINED):** All relationships in Section 2.4 shall be declared as foreign keys with `ON DELETE RESTRICT`. Cascading deletes are prohibited on every table: a delete that would destroy settled records or journal entries cannot be expressed in the schema.

**SETTLEIQ-DATA-R21 (OWNER-DEFINED):** Append-only tables (`audit_journal_entry`, `discrepancy_event`, settled record tables) shall enforce immutability by privileges: the application role holds `INSERT`/`SELECT` only, and a trigger rejects `UPDATE`/`DELETE` as defence-in-depth. A migration that grants broader privileges on these tables is a defect.

### 4.5 Indexes justified by named query patterns

**SETTLEIQ-DATA-R22 (PROPOSED):** Every index shall cite the named query pattern it serves and the API endpoint or dashboard view that issues it. Speculative indexes are prohibited; the index set shall be reviewed against the measured query log at M7.

| Pattern | Issuer | Index |
|---|---|---|
| QP-01 Discrepancy queue by type and age within a run scope | `GET /v1/discrepancies`; dashboard view 2 | `(run_id, type, raised_at)` partial on `status IN ('open','under_investigation')` |
| QP-02 Investigation detail: load one discrepancy with its events | `GET /v1/discrepancies/{id}`; view 3 | `(discrepancy_id, sequence)` on `discrepancy_event` |
| QP-03 Journal chain verification read | `GET /v1/audit-chains/{chainId}/verification` | PK `(chain_id, sequence)` — sequential chain scan |
| QP-04 Run lookup by identity | `GET /v1/runs/{runId}`, re-run detection | unique `(input_digest, rule_version, schema_version)` |
| QP-05 Deposit matching window scan | matching engine; `GET /v1/deposits` | `(deposit_feed_id, value_date, currency)` |
| QP-06 Decisions by class within a run | `GET /v1/decisions`; metrics counts | `(run_id, determinism_guarantee)` |
| QP-07 Metrics counts by window and version | `GET /v1/metrics/auto-match` | `(rule_version, schema_version, started_at)` on run |
| QP-08 Charge constituent retrieval | `GET /v1/charges/{id}/constituents`; `GET /v1/payouts/{id}/decomposition` | `(charge_id)` / `(payout_id)` on constituent tables |

---

## 5. Migration Policy

**SETTLEIQ-DATA-R23 (OWNER-DEFINED):** Migrations shall be forward-only and versioned. `schema_version` is the highest applied migration number, monotonically increasing, recorded on every run (R16). There are no down-migrations.

**SETTLEIQ-DATA-R24 (OWNER-DEFINED):** No migration shall be destructive in any environment, including development. Prohibited: `DROP TABLE`, `DROP COLUMN`, `TRUNCATE`, and any data-deleting `UPDATE`/`DELETE` against stored rows. Superseded structures are deprecated (constraints relaxed, views renamed) and removed only by never removing them — an old column is retained, documented as deprecated, and ignored by the application; an old table is retained, documented as deprecated, and not written.

**SETTLEIQ-DATA-R25 (OWNER-DEFINED):** Reversibility means a new forward migration can restore prior state. Every migration that changes stored data shall ship with an inverse restore migration, and the pair shall be tested against a populated database: apply, restore, compare. A migration without a tested restore path does not merge.

**SETTLEIQ-DATA-R26 (PROPOSED):** Every migration shall apply cleanly to both an empty database and a database populated by the deterministic fixtures, in CI, with a checksum pinned so an edited migration fails the build. The migration tool is OPEN item N-03; the properties above are binding regardless of tool.

**SETTLEIQ-DATA-R27 (OWNER-DEFINED):** Fixtures are generated and pinned to a `schema_version`. The fixture loader shall refuse a manifest whose schema version does not match the current database version, rather than coercing it.

---

## 6. Transaction Boundaries and Concurrency

**SETTLEIQ-DATA-R28 (OWNER-DEFINED):** The audit journal append and the ledger write it records shall be atomic: one database transaction, committing both or neither. There shall be no code path that writes ledger state and appends the journal entry in separate transactions, and no compensating/rollback-by-undo logic — atomicity is structural, not corrective.

**SETTLEIQ-DATA-R29 (OWNER-DEFINED):** Journal appends to one chain shall be serialized by a chain-head lock: the append path locks the chain-head row (`SELECT … FOR UPDATE` on the chain head, or an equivalent advisory lock with a fixed acquisition order), reads the head sequence and digest, inserts the new entry with `sequence = head + 1` and `prev_digest = head digest`, then commits and releases. Lock acquisition order shall be fixed (chain head first, then any row locks) so deadlock is structurally excluded rather than retried away.

**SETTLEIQ-DATA-R30 (OWNER-DEFINED):** Concurrency shall be proven, not asserted. Test `T-DATA-CONC-01` ("concurrent journal append cannot interleave into an invalid chain") shall execute against PostgreSQL and assert:

1. Two sessions, synchronized by a barrier, each open a transaction and each attempt one append to the same chain. Exactly one acquires the chain-head lock first; the second blocks and then proceeds. Both commit.
2. After both commit, chain verification succeeds: sequences are contiguous from 1, every `prev_digest` equals the predecessor's `entry_digest`, and no entry other than genesis has a null or zero `prev_digest`.
3. The stress variant with eight concurrent appenders produces the same contiguous, linked chain; zero deadlock errors, zero serialization failures, and no append requires an application-level retry to succeed.
4. The abort variant: a session that inserts and then rolls back leaves no row; the head sequence is unchanged; the next append reuses the same sequence number — there is no gap.
5. The tamper variant: an `UPDATE` against a committed entry is rejected by privilege; chain verification on read recomputes every digest and reports the first divergence position (SETTLEIQ-REQ-011; detailed semantics in `08`).

**SETTLEIQ-DATA-R31 (OWNER-DEFINED):** Test `T-DATA-TX-01` ("journal append and ledger write are atomic") shall inject a fault between the ledger write and the journal commit (process termination or forced rollback at the commit boundary) and assert that no ledger row and no journal entry persist. The test is a fault-injection test; a mock that skips the real transaction does not satisfy it.

**SETTLEIQ-DATA-R32 (PROPOSED):** `T-DATA-CONC-01` and `T-DATA-TX-01` shall run against PostgreSQL in CI (Docker Compose). SQLite's locking semantics differ; running these tests on SQLite would prove nothing about PostgreSQL and is prohibited as evidence.

---

## 7. Deterministic Fixture Generation

**SETTLEIQ-DATA-R33 (OWNER-DEFINED):** Fixture generation shall use a fixed generator seed, a fixed generator version, and a fixed schema version. All three are recorded in the `fixture_manifest` row for the dataset. Changing any of the three produces a different dataset and a different `input_digest`.

**SETTLEIQ-DATA-R34 (OWNER-DEFINED):** A fixture dataset shall be identified by its input digest (R14). The manifest stores `generator_id`, `generator_version`, `seed`, `schema_version`, `input_digest`, and per-entity record counts. On load, the loader recomputes the dataset digest and refuses a manifest that does not match — the same verify-on-read discipline the journal follows (R08). A mutated fixture is detected, not silently accepted.

**SETTLEIQ-DATA-R35 (OWNER-DEFINED):** The generator shall support defect injection with known expected outcomes, because the demonstration contract (`SETTLEIQ-MASTER-SPEC-001` §4) requires a worked investigation over a dataset containing known injected defects — a phantom charge, an amount break, a fee misattribution, a mid-payout refund, and an FX rounding carryover. Each injected defect shall be recorded in the manifest with its expected discrepancy type; the classification assertions are owned by `07`/`08`, the injection contract by this document. A generator that cannot state what it injected cannot support an asserted expectation.

**SETTLEIQ-DATA-R36 (PROPOSED):** `docker compose up` shall provision PostgreSQL, apply migrations, and load the seed fixture manifest in one command, so that reproducibility is satisfied by the environment definition rather than by documentation (SETTLEIQ-REQ-003).

---

## 8. Explicitly Not Specified Yet

The following are deliberately unresolved. Each is listed with the reason it cannot be settled in this document.

| ID | Item | Why not specified here |
|---|---|---|
| N-01 | Exact declared precision/scale for `numeric` amount columns | Requires the domain limits (largest settlement amount, minimum currency subunit across in-scope currencies) and interacts with OQ-02 (fee-attribution residual allocation, owned by `07`). Declaring a width prematurely either silently rounds (Postgres rounds beyond scale) or over-constrains. The exactness guarantee is carried by R17 until the width is decided with tests. |
| N-02 | Surrogate identifier type (UUID vs bigint) for entity ids | A determinism-compatible choice exists either way; the trade-off (index locality, global uniqueness across re-ingestion, opaque-string size) should be settled with the measured query log, not speculatively. `run_id` derivation (R13) is fixed and does not depend on this. |
| N-03 | Migration tool | The policy (Section 5) is tool-independent. Tool selection requires evaluation against the repo's CI and Docker Compose workflow. |
| N-04 | Journal partitioning, retention, and archival | Depends on OQ-04 (performance scale target). Partitioning before a volume target exists would be speculative. |
| N-05 | Complete canonical enum vocabularies per entity | The vocabularies listed are the minimum required to express the demonstration contract; their finalization depends on the adapter normalization contract in `09` and the taxonomy in `08`. OQ-03 (closed vs open taxonomy) must be settled in `08` first. |
| N-06 | Tie-breaking between equally plausible matches (OQ-01) | Owned by `07`. This document only requires that the outcome be persisted with its determinism guarantee (R06). |
| N-07 | Business-date timezone convention boundary cases (value dates near midnight UTC) | Requires the adapter contract's timestamp normalization rules (`09`) before a single convention can be tested. |

---

## 9. Traceability

| Requirement(s) | Traces to |
|---|---|
| DATA-R01, R02 | SETTLEIQ-REQ-005; ADR-001; SR-03 |
| DATA-R03, R21 | SETTLEIQ-REQ-010 |
| DATA-R04 | SETTLEIQ-REQ-005, REQ-007 |
| DATA-R05 | SETTLEIQ-REQ-006 |
| DATA-R06 | SETTLEIQ-REQ-007 |
| DATA-R07 | SETTLEIQ-REQ-009 |
| DATA-R08, R30 | SETTLEIQ-REQ-011; ADR-003; M5 |
| DATA-R09, R13–R16, R33–R35 | SETTLEIQ-REQ-012; ADR-002; M1–M3 |
| DATA-R17, R18, R18a, R19, R20, R22–R27 | SETTLEIQ-DEC-001 Q3 required properties |
| DATA-R28–R32 | SETTLEIQ-REQ-010, REQ-011; SETTLEIQ-DEC-001 Q3 transaction-boundary properties; `07`, `08` |

Nothing in this document is implemented. Closure of the requirements above requires executed tests with recorded output, per SETTLEIQ-REQ-016.
