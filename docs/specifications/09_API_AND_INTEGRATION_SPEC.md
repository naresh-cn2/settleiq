# 09 — API and Integration Specification

**Document ID:** SETTLEIQ-API-001
**Title:** API and Source-Adapter Integration Specification
**Version:** 1.0.0
**Status:** PROPOSED — specification only; no implementation claimed
**Date:** 2026-10-28
**Canonical path:** `docs/specifications/09_API_AND_INTEGRATION_SPEC.md`
**Owner:** Bukya Naresh (CN2)
**Traces to:** SETTLEIQ-MASTER-SPEC-001 §2.1 (SETTLEIQ-REQ-003), §2.3 (SETTLEIQ-REQ-009…REQ-012), §8 row 09; SETTLEIQ-DEC-001 Q1, Q3, Q4

---

## Document Control

### Purpose

This document defines the REST API over the canonical model of `06_DATA_MODEL_AND_PERSISTENCE.md`, the OpenAPI contract discipline that governs it, the idempotency rules for every mutating endpoint, the error taxonomy including the fail-closed requirement in API terms, and — most importantly — the `SourceAdapter` interface that every processor source must satisfy.

### Status and classification convention

* **OWNER-DEFINED** — restated from a binding requirement of `SETTLEIQ-MASTER-SPEC-001` or `SETTLEIQ-DEC-001`.

**Classification note — RESOLVED DEFECT (added 2026-10-28):** requirements R05, R06, R12, and R13 restate master OWNER-DEFINED requirements and are correctly classified. **Requirements R08 and R09 (idempotency) and R14–R16 (adapter versioning and exclusions) are design decisions that do not restate a master requirement** and are therefore correctly classified **PROPOSED**, not OWNER-DEFINED. An earlier draft classified some design requirements as OWNER-DEFINED; that was flagged during review and is corrected here. If a requirement's classification is disputed, the tie-breaker is: *does the master specification or `04_REQUIREMENTS_AND_NON_GOALS.md` state it verbatim?* If not, it is PROPOSED.
* **PROPOSED** — recommended by this specification; not binding until ratified by the OWNER.

No endpoint, adapter, or contract test exists. Nothing here is implemented.

### Scope

* The API serves the dashboard of `10_DASHBOARD_SPEC.md` and third-party read access for investigation. It is a local, single-operator deployment: no authentication mechanism, no multi-tenancy, no rate limiting tier is specified for the first build (Section 7).
* The canonical types referenced here (`Charge`, `Fee`, `Refund`, `Adjustment`, `Payout`, `SettlementBatch`, `BankTransaction`, `MatchDecision`, `Discrepancy`, `AuditJournalEntry`) are defined in `06`. This document fixes their API representation, not their storage.
* The `SourceAdapter` interface is frozen at milestone M1, before any adapter is written (SETTLEIQ-DEC-001 Q1). Stripe is the only processor source in the first build; Adyen is additive behind the frozen interface.

### What this document does not claim

No OpenAPI document has been authored. No endpoint has been implemented or tested. No adapter has been written against this interface. No Stripe integration exists; all data in the first build is synthetic (SETTLEIQ-REQ-002).

---

## 1. API Conventions

### 1.1 Transport and versioning

**SETTLEIQ-API-R01 (PROPOSED):** The API is REST over HTTP/1.1, JSON request and response bodies, UTF-8 throughout. The contract is an OpenAPI 3.x document served at `GET /v1/openapi.yaml`. The API is versioned by URI major version (`/v1`); within a major version, changes are additive only — no field removal, no field rename, no semantics change. A breaking change is a new major version and requires an OWNER decision.

**SETTLEIQ-API-R02 (PROPOSED):** Money is serialized as a **JSON string carrying a decimal value** (for example `"amount": "1043.27"`), never as a JSON number. JSON numbers parse through binary floating point on common clients and would smuggle float onto the monetary path (SETTLEIQ-REQ-005; risk SR-03). Every money field is accompanied by a currency field, per DATA-R02.

**SETTLEIQ-API-R03 (PROPOSED):** Timestamps are RFC 3339 UTC at fixed precision. Dates are calendar dates without timezone. Identifiers are opaque strings — no client may parse an identifier's structure, and the server shall not change an identifier's format within `/v1`.

**SETTLEIQ-API-R04 (PROPOSED):** Collections are paginated with cursor pagination: `?limit=` (server-enforced maximum) and `?cursor=`, returning `{items, next_cursor}`. Filters are explicit query parameters; no implicit defaults that change the population of a result (see the metrics fail-closed rule, Section 5.3).

### 1.2 OpenAPI is the contract source of truth

**SETTLEIQ-API-R05 (OWNER-DEFINED):** The OpenAPI document is the sole contract. No endpoint shall be implemented before its path, operation, request schema, response schema, and error schemas exist in the OpenAPI document. An implementation whose behaviour is not described by the document is a defect, and a document change that is not covered by an implementation is equally a defect.

**SETTLEIQ-API-R06 (OWNER-DEFINED):** The API is not implemented without a contract test. Every endpoint shall have, in CI: (a) a test that validates a live response against the schema declared for that operation in the same OpenAPI document; (b) a test for each declared error response's shape and status code; (c) a determinism test that two identical requests (same idempotency key or identical read) return byte-identical payloads where the contract promises it (SETTLEIQ-REQ-012).

**SETTLEIQ-API-R07 (PROPOSED):** The TypeScript client types of `10_DASHBOARD_SPEC.md` shall be generated from the same OpenAPI document, so the client cannot drift from the contract. A hand-written client type that duplicates a contract field is a defect.

---

## 2. Resource Specifications

Field tables below give field names and types for the principal representations; the OpenAPI document holds the exhaustive schemas. Enum vocabularies are owned by `06` (canonical model) and `08` (discrepancy taxonomy).

### 2.1 `/runs`

| Operation | Summary |
|---|---|
| `POST /v1/runs` | Trigger a reconciliation run over an identified input set |
| `GET /v1/runs` | List runs, filterable |
| `GET /v1/runs/{runId}` | One run |
| `GET /v1/runs/{runId}/diff?against={otherRunId}` | Diff two runs (dashboard view 5) |

**`POST /v1/runs` request** (Idempotency-Key required, Section 4):

| Field | Type | Notes |
|---|---|---|
| `input` | object | `{kind: "fixture_manifest" \| "input_digest", id: string}` — a seeded fixture manifest, or the digest of a prior input set |
| `rule_version` | string | must be a registered rule version; omitted rejects as `invalid_request`, never silently defaulted |
| `schema_version` | integer, optional | must equal current if supplied; mismatch is `rule_version_mismatch` |

**Response `201` — Run:**

| Field | Type | Notes |
|---|---|---|
| `run_id` | string | deterministic derivation per DATA-R13 |
| `input_digest` | string | |
| `rule_version` | string | |
| `schema_version` | integer | |
| `generator_version` | string \| null | present for fixture inputs |
| `adapter_versions` | map<string,string> | |
| `status` | enum | `pending`, `running`, `completed`, `failed` |
| `started_at`, `completed_at` | string (date-time) \| null | |
| `outcome_counts` | object | instrumented counts; money-free integers |

**Error semantics.** `400 invalid_request` (unregistered rule version, malformed input), `409 rule_version_mismatch`, `409 idempotency_key_reuse`. A duplicate trigger carrying the same `(input_digest, rule_version, schema_version)` returns the existing run with HTTP `200` and header `Idempotency-Replayed: true` (Section 4) — a re-trigger never spawns a second execution of an identical run.

**`GET /v1/runs` filters.** `status`, `rule_version`, `schema_version`, `input_digest`, `started_after`/`started_before`, `limit`, `cursor`. Response is a page of Run summaries (no `outcome_counts` in the list; fetch the run for counts — the dashboard view 1 displays counts from the detail read).

**`GET /v1/runs/{runId}/diff`.** Response:

| Field | Type | Notes |
|---|---|---|
| `base_run_id`, `other_run_id` | string | |
| `identical` | boolean | true when both runs' output digests match (determinism, SETTLEIQ-REQ-012) |
| `decisions` | object | `{added, removed, changed}` — each an array of decision references |
| `discrepancies` | object | same shape |
| `outcome_counts` | object | per-base and per-other counts |

`404 not_found` for either run. `409 rule_version_mismatch` is **not** an error here — runs under different rule versions are comparable, and the response labels the difference rather than refusing it.

### 2.2 `/charges`

| Operation | Summary |
|---|---|
| `GET /v1/charges` | List charges |
| `GET /v1/charges/{chargeId}` | One charge |
| `GET /v1/charges/{chargeId}/constituents` | Fees, refunds, adjustments attached to this charge |

There is **no** `POST /charges`. Source records enter the system only through a `SourceAdapter` (Section 6); the API never fabricates or amends settled source data (DATA-R03, DATA-R07). The same read-only posture applies to `/payouts` and `/deposits`.

**`GET /v1/charges` filters.** `run_id`, `currency`, `status`, `captured_after`/`captured_before`, `limit`, `cursor`. Response items — Charge: `charge_id`, `source_adapter_id`, `processor_charge_id`, `run_id`, `amount` (decimal string), `currency`, `captured_amount`, `status`, `authorized_at`, `captured_at`, `supersedes`.

**`GET /v1/charges/{chargeId}/constituents`.** Returns `{charge_id, fees: Fee[], refunds: Refund[], adjustments: Adjustment[]}` — Fee: `fee_id`, `amount`, `currency`, `fee_type`, `tax_amount`, `amount_basis`, `charge_id`, `payout_id`; Refund: `refund_id`, `amount`, `currency`, `status`, `reason`, `created_at`; Adjustment: `adjustment_id`, `amount` (signed decimal string), `currency`, `type`, `effective_date`.

### 2.3 `/payouts`

| Operation | Summary |
|---|---|
| `GET /v1/payouts` | List payouts |
| `GET /v1/payouts/{payoutId}` | One payout |
| `GET /v1/payouts/{payoutId}/decomposition` | Charge-level decomposition (the core read) |

**`GET /v1/payouts/{payoutId}/decomposition`.** Returns `{payout_id, composition_disclosed: boolean, constituents: Constituent[], bridge: BridgeResult}` where each Constituent is `{kind: "charge"|"fee"|"refund"|"adjustment", ref, amount, currency, match_state, decision_ids}` and `match_state` is one of `matched`, `ambiguous`, `human_required`, `unmatched`, `unresolvable`. The engine never manufactures a `matched` state for a constituent it has not decided (SETTLEIQ-REQ-009); the enumeration is the API-level expression of fail-closed.

**`GET /v1/payouts` filters.** `run_id`, `currency`, `method`, `status`, `arrival_after`/`arrival_before`, `limit`, `cursor`.

### 2.4 `/deposits`

| Operation | Summary |
|---|---|
| `GET /v1/deposits` | List bank deposits |
| `GET /v1/deposits/{depositId}` | One bank deposit |

Response — Deposit: `bank_transaction_id`, `deposit_feed_id`, `bank_account_ref`, `amount` (decimal string), `currency`, `value_date`, `external_reference`, `remittance_information`, `matched_status`. Filters: `run_id`, `bank_account_ref`, `value_date_after`/`value_date_before`, `matched_status`, `limit`, `cursor`.

### 2.5 `/discrepancies`

| Operation | Summary |
|---|---|
| `GET /v1/discrepancies` | List discrepancies (the queue) |
| `GET /v1/discrepancies/{discrepancyId}` | Full investigation detail |
| `POST /v1/discrepancies/{discrepancyId}/transitions` | Workflow transition |
| `POST /v1/discrepancies/{discrepancyId}/resolution` | Resolve or declare unresolvable |

All list representations carry server-computed `age_days` — the client shall not compute age, because the client's clock is not the system's clock (SETTLEIQ-REQ-012 discipline).

**`GET /v1/discrepancies` filters.** `run_id`, `type`, `severity`, `status`, `raised_after`/`raised_before`, `min_age_days`, `sort` (`raised_at` \| `severity` \| `age`), `limit`, `cursor`. Response item — DiscrepancySummary: `discrepancy_id`, `run_id`, `type`, `severity`, `status`, `raised_at`, `age_days`.

**`GET /v1/discrepancies/{discrepancyId}` — investigation detail:**

| Field | Type | Notes |
|---|---|
| `discrepancy_id`, `run_id`, `type`, `severity`, `status` | — | typed taxonomy code; never free text |
| `raised_at`, `age_days` | — | |
| `source_refs` | array | contributing records (charge-level, both sides) |
| `contributing_decision_ids` | array | links into `/decisions` |
| `decisions` | array of Decision | full provenance per decision |
| `resolution_history` | array of DiscrepancyEvent | append-only event list |
| `audit_entry_ids` | array | journal entries covering this discrepancy |

**`POST .../transitions` request:** `{target_status: "acknowledged"|"investigating", note: string?}`. **Response `200`:** the updated discrepancy. **Errors:** `409 run_state_conflict` when the transition is invalid from current status (for example resolving an already-resolved discrepancy with a different resolution — the event history is append-only and does not overwrite); `400 invalid_request` for an unknown target.

**`POST .../resolution` request:** `{resolution_code: string, resolution_kind: "resolved"|"unresolvable", note: string, evidence_refs: string[]}`. **Response `200`:** updated discrepancy including the appended event. This endpoint is how a human records that evidence was insufficient — the unresolvable path is a first-class action, not an error (SETTLEIQ-REQ-009).

### 2.6 `/decisions`

| Operation | Summary |
|---|---|
| `GET /v1/decisions` | List match decisions |
| `GET /v1/decisions/{decisionId}` | One decision with full provenance |
| `POST /v1/decisions/{decisionId}/confirmations` | Human confirmation of an ambiguous decision |

Decision: `decision_id`, `run_id`, `rule_id`, `rule_version`, `left_ref`, `right_ref`, `matched_fields` (array of `{field, left_value, right_value}`; money values as decimal strings), `confidence_class`, `determinism_guarantee`, `decided_by`, `evidence_digest`, `supersedes`.

**Filters.** `run_id`, `determinism_guarantee`, `confidence_class`, `rule_id`, `rule_version`, `limit`, `cursor`.

**`POST .../confirmations` request:** `{confirmed: true, reviewer_note: string?}`. **Response `201`** with the confirmation record; a duplicate confirmation of the same decision is idempotent (Section 4) and returns the existing record replayed. Human confirmation never mutates the decision row (DATA-R09 immutability); it appends a confirmation record that the metrics methodology counts explicitly (Section 2.8, and `10` view 4).

### 2.7 `/audit-entries`

| Operation | Summary |
|---|---|
| `GET /v1/audit-entries` | List journal entries |
| `GET /v1/audit-entries/{entryId}` | One entry |
| `GET /v1/audit-chains/{chainId}/verification` | Computed chain verification report |

The journal is append-only (SETTLEIQ-REQ-010): there are deliberately no mutating operations on this resource. Any endpoint that could alter or delete a journal entry is a critical defect.

Audit entry: `entry_id`, `chain_id`, `sequence`, `prev_digest`, `entry_digest`, `canonical_payload`, `recorded_at`. Verification report: `{chain_id, verified: boolean, entry_count, first_divergence: {entry_id, expected_digest, recomputed_digest} | null, verified_at}`. An intact chain returns HTTP `200` with `verified: true`. A divergence returns HTTP `500 audit_verification_failed` carrying the same report body with `verified: false` and the first divergence position, because divergence is an integrity alarm rather than a query result (SETTLEIQ-REQ-011).

### 2.8 `/metrics`

| Operation | Summary |
|---|---|
| `GET /v1/metrics/auto-match` | The published rate with its methodology |

**Query parameters (all required; no silent defaults):** `window_start`, `window_end` (RFC 3339 UTC), `population_filter` (optional object: `rule_version`, `schema_version`, `generator_version` — when supplied it narrows the population and is echoed in the methodology record).

**Response:**

| Field | Type | Notes |
|---|---|---|
| `rate` | decimal string | computed by the system from the counts below; never a literal in any code path |
| `numerator` | integer | matched constituents per the denominator definition |
| `denominator` | integer | eligible constituents per the denominator definition |
| `confirmed_count` | integer | human-confirmed ambiguous decisions in population |
| `excluded` | array of `{code, count}` | categories excluded from the denominator, with counts |
| `methodology` | object | the full methodology record (below) |

**Methodology record** (each field is rendered by dashboard view 4, per `10`): `denominator_definition`, `population_description`, `window {start, end, timezone}`, `human_confirmation_treatment`, `rule_version`, `schema_version`, `generator_version`, `run_count`, `computed_at`, `rate_expression` (the computation as recorded rule id + version). The rate is computed by the system from instrumented counts and is never stated in prose anywhere in the repository (SETTLEIQ-REQ-013, REQ-014; ADR-004).

---

## 3. Resource-State Summary

| Resource | Created by | Mutated by | Read by |
|---|---|---|---|
| Charge / Fee / Refund / Adjustment | SourceAdapter only | nobody (append-only correction via supersede) | API reads |
| Payout / SettlementBatch | SourceAdapter only | nobody | API reads |
| BankTransaction | DepositFeedAdapter only | engine `matched_status` only | API reads |
| ReconciliationRun | `POST /v1/runs` | engine status transitions only | API reads |
| MatchDecision | engine | human confirmation appends a record; decision row never mutates | API reads |
| Discrepancy | engine | workflow transitions append events | API reads + dashboard |
| AuditJournalEntry | system | nobody, ever | API reads + verification |

---

## 4. Idempotency

**SETTLEIQ-API-R08 (OWNER-DEFINED):** Every mutating endpoint shall be idempotent by client-supplied key. The `Idempotency-Key` header is required on every `POST`. The server stores, per key: the request digest, the response snapshot, and the status code. A duplicate submission with the same key and the same payload returns the original response with HTTP status as originally returned and header `Idempotency-Replayed: true`. A duplicate submission never performs a second write.

**SETTLEIQ-API-R09 (OWNER-DEFINED):** The same key with a *different* payload is a conflict: `409 idempotency_key_reuse`. The same key submitted while the original is still in flight returns `409 idempotency_in_flight` (retryable). Idempotency records are persisted (table `idempotency_record`, `06` §2.3) so replay survives a process restart; the retention window of records is OPEN (N-08).

**SETTLEIQ-API-R10 (PROPOSED):** `POST /v1/runs` carries two layers of idempotency: the client key (R08) and the derived `run_id` (DATA-R13). Even without a key retry, re-triggering an identical `(input_digest, rule_version, schema_version)` tuple returns the existing run rather than re-executing it, because the run identity *is* the idempotency key at the domain level.

---

## 5. Error Taxonomy and Fail-Closed

### 5.1 Error envelope

**SETTLEIQ-API-R11 (PROPOSED):** Every error response uses one envelope:

```
{ "error": { "code": string, "message": string, "retryable": boolean, "details": object? } }
```

`code` is drawn from the closed taxonomy below; `message` is human-readable; `retryable` states whether an identical retry may succeed. No endpoint returns a bare string, a bare status, or an HTML error.

### 5.2 Code taxonomy

| Code | HTTP | Retryable | Meaning |
|---|---|---|---|
| `invalid_request` | 400 | false | Schema violation, unknown enum value, missing required measurement parameter |
| `idempotency_key_reuse` | 409 | false | Key replayed with a different payload |
| `idempotency_in_flight` | 409 | true | Same key currently processing |
| `not_found` | 404 | false | Referenced resource does not exist |
| `run_state_conflict` | 409 | false | Operation invalid for the resource's current state |
| `rule_version_mismatch` | 409 | false | Rule version unregistered or incompatible with `schema_version` |
| `audit_verification_failed` | 500 | false | Journal chain verification diverged — integrity alarm |
| `internal_error` | 500 | false | Unspecified server failure |

An unknown enum value on any request is `invalid_request`; it is never coerced to a default and never rounded into a nearest match.

### 5.3 Fail-closed in API terms

**SETTLEIQ-API-R12 (OWNER-DEFINED):** The API shall never return a confident answer where the engine is unresolved. Concretely:

1. Reads that expose a match return the decision's `determinism_guarantee` verbatim. An ambiguous or human-required decision is returned as such, with HTTP `200`; there is no field, header, or default presentation in which an unresolved decision appears resolved.
2. A discrepancy whose evidence is insufficient is returned with `status: "unresolvable"` and its typed code. No endpoint synthesizes an estimated amount, a probable cause, or a "likely match" for it.
3. Operations that depend on a resolution the engine has not produced return `409 run_state_conflict` — they do not proceed on an assumption.
4. The metrics endpoint refuses a request without explicit window parameters (`invalid_request`) rather than applying a default. A silently defaulted window is the mechanism by which an unqualified rate gets published; the refusal is the control.
5. Where a derived monetary value is exposed, its derivation reference (rule id and version) accompanies it (DATA-R04); a derived value with no derivation is a contract defect.

---

## 6. The SourceAdapter Interface

This section is the interface freeze of SETTLEIQ-DEC-001 Q1: the interface is defined and frozen at M1, **before either adapter is written**. The interface is the decision; the adapter count is not.

### 6.1 Interface definition

The interface is language-agnostic; the Python core implements it as an explicit protocol with runtime-checkable structural typing. `interface_version` is pinned to the value frozen at M1 and changes only by OWNER decision.

```
SourceAdapter
  interface_version   : string            # frozen at M1
  adapter_id          : string            # e.g. "stripe"; registry key
  adapter_version     : string (semver)   # the adapter's own version
  canonical_version   : string            # canonical model version it emits (ties to 06)

  capabilities() -> AdapterCapabilities
      # declares what this source can and cannot do; the engine adapts to the
      # declaration rather than assuming processor behaviour. Minimum fields:
      #   provides_payout_composition : bool   # false for sources that do not
      #                                        # identify payout constituents
      #   supports_instant_payouts    : bool
      #   provides_settlement_batches : bool
      #   fee_tax_disclosure          : enum {gross, net, per_fee_flag}
      #   deposit_feed                : bool   # whether this adapter also
      #                                        # supplies bank-side deposits

  fetch_charges(window)          -> Iterator[Charge]
  fetch_refunds(window)          -> Iterator[Refund]
  fetch_fees(window)             -> Iterator[Fee]
  fetch_adjustments(window)      -> Iterator[Adjustment]
  fetch_payouts(window)          -> Iterator[Payout]
  fetch_settlement_batches(window) -> Iterator[SettlementBatch]
  fetch_deposits(window)         -> Iterator[BankTransaction]   # if deposit_feed
```

Each returned object is the canonical type from `06` — no processor-specific type, field name, status string, or identifier crosses the boundary. `window` is an explicit inclusive/exclusive UTC interval; adapters that cannot answer a window precisely declare it in `capabilities()` rather than silently widening or narrowing.

### 6.2 The normalization contract

**SETTLEIQ-API-R13 (OWNER-DEFINED):** Canonical model in, no processor-specific leakage out. The contract has five parts:

1. **Output types.** An adapter returns only `06` types. A processor field with no canonical home is either mapped to an existing canonical field or dropped *after being recorded in the row's provenance*, never smuggled through under a processor name.
2. **Enumeration mapping.** Source enum values map to the canonical vocabularies of `06` §2. A source value with no canonical mapping is a normalization error: the ingestion fails closed (SETTLEIQ-REQ-009). A catch-all mapping is prohibited (DATA-R11).
3. **Money and time.** Money is parsed directly to `decimal.Decimal` with the declared context — never via a float, never via a JSON number (R02). Timestamps normalize to UTC instants or business dates per the `06` §2.1 convention; the adapter states which it used when a source is ambiguous.
4. **Opaque identifiers.** `processor_*_id` fields cross the boundary as opaque strings and are never parsed, compared, or interpreted by the engine. They exist for traceability to the source record, nothing else.
5. **Digest contribution.** The canonical serialization of everything an adapter returns contributes to `input_digest` (DATA-R14), together with `adapter_id`, `adapter_version`, and `canonical_version`. Two runs differ if any adapter version differs — this is what makes run identity stable across sources.

### 6.3 Adapter versioning

**SETTLEIQ-API-R14 (PROPOSED):** Adapters version independently of the interface. `interface_version` is frozen at M1; `adapter_version` is the adapter's own semver and is recorded in every run it contributes to. Rules:

* A new processor is a **new adapter**, not an engine change. Adding Adyen later must not touch the engine, the schema, or the dashboard.
* A change to the canonical model is an interface-level change: it requires a new `interface_version`, a `schema_version` migration per `06` §5, and an ADR.
* An adapter bug fix that alters canonical output changes `adapter_version` and therefore every affected `input_digest`; prior runs remain valid under their recorded tuple and must not be silently reinterpreted.

### 6.4 Test obligations

**SETTLEIQ-API-R15 (PROPOSED):** The frozen interface ships with:

* A **fake adapter** implementing the interface against the deterministic fixtures (`06` §7), so the engine, the API, the dashboard, and the full test suite run with no processor present. This is what keeps the Stripe-only first scope from blocking the rest of the system.
* A **golden-file test per real adapter**: a recorded synthetic processor payload in, canonical records out, byte-compared. A processor-shaped change that alters canonical output fails the build (M2 acceptance).
* A **capability test**: an engine path that depends on `provides_payout_composition` is exercised with both `true` and `false`, proving the engine does not assume disclosure.

### 6.5 Why freezing the interface first makes Stripe-only a safe first scope

1. **The interface forces the canonical model to be processor-independent.** If Stripe were built first without the frozen interface, Stripe's objects (payout, balance transaction, settlement batch) would become the de facto schema — their shapes, their disclosure behaviour, their identifiers. Every later processor would then require migration of a schema built around the first one.
2. **Additivity is structural, not aspirational.** With the interface frozen, "add Adyen later" is "write a new class", verifiable by the fact that the engine, schema, dashboard, and OpenAPI contract are untouched. Without it, that same claim is a rewrite.
3. **Heterogeneity is handled from day one.** The capability flags force the engine to ask what a source *can* do instead of assuming. Stripe itself is heterogeneous (payout composition is disclosed for automatic payouts and not for instant or manual ones); the engine that handles that handles Adyen's different heterogeneity without a new failure mode.
4. **The rest of the system is unblocked.** The fake adapter means tests, the API, the dashboard, and the demonstration contract all run from day one. Stripe-only scope cannot become an excuse for an untestable system (SETTLEIQ-REQ-003, REQ-016).
5. **Run identity is stable across sources.** Because adapters and their versions are inside the input digest, a future Adyen run and a Stripe run are comparable, diffable, and individually reproducible under the same identity scheme — the run history view (`10` view 5) does not have to be redesigned when the second source arrives.

---

## 7. Explicitly Out of Scope for the First Build

**SETTLEIQ-API-R16 (PROPOSED):** The following are excluded from the first build and shall not appear in the OpenAPI document:

1. **Webhooks.** No inbound event endpoints. Ingestion is pull-based through adapters over explicit windows.
2. **Streaming.** No WebSocket, SSE, or long-poll endpoint. The dashboard refreshes on user action or bounded interval polling.
3. **GraphQL.** REST only.
4. **Multi-tenancy.** No tenant identifier exists on any resource; the single-operator deployment of `10` §6 shares one dataset.
5. **Authentication and authorization mechanisms.** No API keys, OAuth, or sessions. The API binds to localhost in the Docker Compose deployment; this is a demonstration-environment constraint and is stated here so it is never mistaken for a designed auth boundary.
6. **Live money, live credentials, live customer data.** Adapters in the first build run against the synthetic generator (SETTLEIQ-REQ-002).

---

## 8. Not Specified Yet

| ID | Item | Why |
|---|---|---|
| N-08 | Idempotency record retention window | Depends on operational use; a finite window is correct but the duration needs the deployment model, which does not exist yet. |
| N-09 | Deposit-side interface details (`DepositFeedAdapter` beyond the shared normalization contract) | The bank feed is synthetic-only in the first build; a real feed's shapes would drive the rest, and inventing them would be speculation. The shared normalization contract and the frozen-interface posture are fixed now. |
| N-10 | Pagination maximum page size | Needs the measured response sizes at demo scale (OQ-04). |
| N-11 | Whether `GET /metrics/auto-match` accepts a stored-report identifier for reproducibility | Ties to the report design in the metrics work; does not block the endpoint contract above. |

---

## 9. Traceability

| Requirement(s) | Traces to |
|---|---|
| API-R01…R04, R07 | SETTLEIQ-REQ-003; `10_DASHBOARD_SPEC.md` §2 |
| API-R02 | SETTLEIQ-REQ-005; SR-03; ADR-001 |
| API-R05, R06 | SETTLEIQ-REQ-003, REQ-012, REQ-016; M7 |
| API-R08…R10 | SETTLEIQ-REQ-012; `06` §2.3 `idempotency_record` |
| API-R11, R12 | SETTLEIQ-REQ-009, REQ-013, REQ-014 |
| API-R13…R15 | SETTLEIQ-DEC-001 Q1 (interface frozen at M1); SETTLEIQ-REQ-IND-03; M2 |
| API-R16 | SETTLEIQ-REQ-001, REQ-002; `10` §6 |

Nothing in this document is implemented. No contract test has run. No adapter exists.
