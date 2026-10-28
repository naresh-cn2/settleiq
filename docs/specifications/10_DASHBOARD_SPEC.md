# 10 — Dashboard Specification

**Document ID:** SETTLEIQ-UI-001
**Title:** Investigation Dashboard Specification
**Version:** 1.0.0
**Status:** PROPOSED — specification only; no implementation claimed
**Date:** 2026-10-28
**Canonical path:** `docs/specifications/10_DASHBOARD_SPEC.md`
**Owner:** Bukya Naresh (CN2)
**Traces to:** SETTLEIQ-MASTER-SPEC-001 §2.1 (SETTLEIQ-REQ-003), §2.4 (SETTLEIQ-REQ-013, REQ-014), §8 row 10; SETTLEIQ-DEC-001 Q4

---

## Document Control

### Purpose

This document defines the minimum complete investigation interface for SettleIQ: five functional views, each tied to a named use case, each specified by functional requirements, the API it consumes, the data it renders, the interactions it supports, and the acceptance criterion that closes it.

### Design principle

**SETTLEIQ-UI-R01 (OWNER-DEFINED):** The dashboard exists to make the end-to-end workflow visible: a typed discrepancy produced by the engine, investigated against its contributing records and provenance, and resolved or declared unresolvable with traceable evidence. It is the observation surface of the artifact, not decoration. A view that does not carry that workflow does not get built; a visual treatment that no functional requirement demands does not get built.

**SETTLEIQ-UI-R02 (PROPOSED):** The dashboard shall contain exactly five views. A sixth view requires a named use case and an OWNER decision recorded in `12_DECISIONS_AND_OPEN_QUESTIONS.md`, on the same terms as a new entity in `06` (DATA-R10). **[Classification corrected 2026-10-28: this requirement was previously labelled OWNER-DEFINED, but it rests on the unratified Q4 decision and is therefore PROPOSED.]**

### Status convention

* **OWNER-DEFINED** — restated from `SETTLEIQ-MASTER-SPEC-001` or `SETTLEIQ-DEC-001`.

**Classification note — RESOLVED DEFECT (added 2026-10-28):** requirements R12–R17 (metrics presentation and the measurement methodology) restate the master's OWNER-DEFINED measurement requirements REQ-013/014 and are correctly classified OWNER-DEFINED. **Requirement R02 ("exactly five views") is a design decision that rests on the unratified Q4 decision and is therefore PROPOSED**, not OWNER-DEFINED — the five-view scope is a recommendation awaiting ratification, and a sixth view is not currently an OWNER-decision matter. Requirements R01, R03, R04 and R22 restate master REQ-003/REQ-016 and are correctly classified.
* **PROPOSED** — recommended here; not binding until ratified.

Nothing in this document is implemented. No client, no view, no test exists.

### Use-case traceability

The five views map to the use cases defined in `02_PROBLEM_AND_USE_CASES.md` and bound to the dashboard views by `SETTLEIQ-DEC-001` Q4: UC-1 Reproducible Run, UC-2 Triage the Discrepancy Queue, UC-3 Investigate a Single Discrepancy, UC-4 Measure the Auto-Match Rate, UC-5 Reproduce a Prior Run. UC-6 (decompose a payout) and UC-7 (verify audit journal integrity) carry no dashboard binding and are served by the API alone.

---

## 1. Technology Constraints

**SETTLEIQ-UI-R03 (OWNER-DEFINED):** The client is a TypeScript application built **inside this repository** and served by this project's own API from the same origin. There is no separate front-end build service, no external hosting, and no third-party origin in the demonstration path. `docker compose up` plus the single reproduction command brings up engine, API, and client together (SETTLEIQ-REQ-003).

**SETTLEIQ-UI-R04 (OWNER-DEFINED):** No styling system, no component library, and no design tokens until a functional requirement demands them. A demand must be recorded: the requirement that generates it, the alternatives rejected, and the cost — the same discipline as `12_DECISIONS_AND_OPEN_QUESTIONS.md`. Browser-default rendering with project-controlled CSS is sufficient for every requirement in this document.

**SETTLEIQ-UI-R05 (PROPOSED):** Client types for API payloads shall be generated from the OpenAPI document of `09_API_AND_INTEGRATION_SPEC.md` (API-R07). The client shall not hand-maintain a parallel copy of a contract type.

**SETTLEIQ-UI-R06 (PROPOSED):** The client shall not recompute published figures. Every count, rate, age, and amount rendered in any view is read verbatim from an API response. Client-side arithmetic on displayed values — summing counts, computing age from a timestamp, deriving a rate — is a defect, because it defeats the single-source-of-truth discipline that SETTLEIQ-REQ-014 exists to enforce.

**SETTLEIQ-UI-R07 (PROPOSED):** Every view's state shall be URL-addressable (filters, selection, and view identity in the query string), so that an investigation state can be shared, reloaded, and reproduced by a third party. A view whose state cannot be reconstructed from its URL cannot serve REQ-003.

**SETTLEIQ-UI-R08 (PROPOSED):** All interactions shall be keyboard-operable with a visible focus indicator. This is a functional requirement of triage speed, not an accessibility decoration, and it does not authorize a styling system (R04).

---

## 2. View 1 — Run List (UC-1 Reproducible run)

**Functional requirement SETTLEIQ-UI-R09 (PROPOSED):** The view shall let an operator trigger a reconciliation run over an identified input and observe the resulting run record. It shall display, for each run: `run_id`, `input_digest`, `rule_version`, `schema_version`, `status`, and outcome counts. `input_digest` shall be displayed in full (truncation is permitted only when the full value remains available to the reader, for example on focus or copy). No run shall be displayed without its `input_digest` and `rule_version` on the same row — a run record that cannot be tied to its inputs is not a run record.

**API consumed.** `POST /v1/runs` (trigger; `input.kind` ∈ {`fixture_manifest`, `input_digest`}, `rule_version` required); `GET /v1/runs` (list); `GET /v1/runs/{runId}` (counts).

**Data rendered.** `run_id`, `input_digest`, `rule_version`, `schema_version`, `generator_version` (nullable), `status`, `started_at`, `completed_at`, `outcome_counts` (integers from the API, never recomputed — UI-R06).

**Interactions.** Select an input (fixture manifest or prior `input_digest`), supply `rule_version`, submit; observe the new run in the list and its status transition to a terminal state; drill into a run to open the discrepancy queue scoped to it; re-trigger an existing tuple and observe the API returning the same `run_id` rather than a second run (API-R10).

**Acceptance criterion.** A test shall trigger a run from a seeded fixture manifest and assert that the rendered row equals the API's run record field-for-field, that the terminal status is reachable through the UI without a page reload, and that re-submitting the same tuple returns the same `run_id`. The client's rendered `outcome_counts` shall equal the API payload byte-for-byte; any client-side transformation of a count fails the test.

---

## 3. View 2 — Discrepancy Queue (UC-2 Triage)

**Functional requirement SETTLEIQ-UI-R10 (PROPOSED):** The view shall list discrepancies by named type and age, filterable by type, severity, and status, with drill-through to the investigation detail. `age_days` is server-computed and rendered verbatim; the client shall not compute age (UI-R06). Every row shall show its named type code — a row without a type is a defect, because an untyped break is precisely what the taxonomy exists to eliminate (SETTLEIQ-REQ-008).

**API consumed.** `GET /v1/discrepancies` (filters: `run_id`, `type`, `severity`, `status`, `raised_after`/`raised_before`, `min_age_days`, `sort`).

**Data rendered.** `discrepancy_id`, `run_id`, `type`, `severity`, `status`, `raised_at`, `age_days` — all from the response; plus the response's own counts for the current filter, when provided.

**Interactions.** Filter by type, severity, status, and minimum age with the filter combination reflected in the URL (UI-R07); sort by age, severity, or raised-at; select a row to drill into the investigation detail for that discrepancy; change run scope to the queue. Pagination follows the API cursor.

**Acceptance criterion.** Against the seeded dataset with known injected defects (`06` §7, DATA-R35), the queue shall display exactly the injected set: one row per injected defect, each with its expected named type and a non-negative integer age. A filter test shall compose type + severity + status + age and assert the result set equals the API's answer for the same parameters. Drill-through shall open the investigation detail for the selected `discrepancy_id` with no intermediate fetch the API did not sanction.

---

## 4. View 3 — Investigation Detail (UC-3 Investigate)

**Functional requirement SETTLEIQ-UI-R11 (PROPOSED):** For one discrepancy, the view shall render the complete evidence set: contributing records on both sides, matched fields per decision, full provenance (rule id and version, confidence class, determinism guarantee), the decision trail including superseded decisions, and the resolution history. Where the engine is unresolved, the view shall render that state explicitly; it shall not render a summary that reads as a conclusion.

**API consumed.** `GET /v1/discrepancies/{discrepancyId}` (investigation detail); `GET /v1/decisions/{decisionId}` (decision provenance drill); `GET /v1/payouts/{payoutId}/decomposition` (constituent context); `GET /v1/charges/{chargeId}/constituents` (fee/refund/adjustment context); `POST /v1/discrepancies/{discrepancyId}/transitions`; `POST /v1/discrepancies/{discrepancyId}/resolution`; `POST /v1/decisions/{decisionId}/confirmations`.

**Data rendered.** `source_refs` (both sides, charge-level); per-decision `matched_fields` (`field`, `left_value`, `right_value` — money as decimal strings, never reformatted client-side beyond display truncation that preserves the full value on demand); `rule_id`, `rule_version`, `confidence_class`, `determinism_guarantee`, `decided_by`, `evidence_digest`; `resolution_history` (append-only event list); `audit_entry_ids`.

**Interactions.** Walk the decision trail; inspect each decision's provenance; submit a workflow transition (`acknowledged`, `investigating`); submit a resolution (`resolved` with a resolution code, note, and evidence refs — or `unresolvable`, the explicit insufficient-evidence outcome, SETTLEIQ-REQ-009); confirm an ambiguous decision (`human_required` class) so it is counted by the metrics methodology; navigate back to the queue and to the contributing run.

**Acceptance criterion.** A UI test shall assert that every provenance field rendered exists verbatim in the API response for the referenced decision or event — the client adds nothing. A second test shall render a discrepancy in `unresolvable` state and assert that no element in the view presents a resolution, an estimated value, or a probable cause. A third shall submit a resolution and assert the new event appears at the end of `resolution_history` and that a referenced `audit_entry_id` is retrievable and verifies. Where the engine reports `determinism_guarantee: ambiguous`, the view shall display that label adjacent to the match, never a bare "match".

---

## 5. View 4 — Metrics (UC-4 Measure): the centrepiece

**Functional requirement SETTLEIQ-UI-R12 (OWNER-DEFINED):** The view shall present the auto-match rate with its measurement methodology inline: denominator definition, population, time window, and human-confirmation treatment, computed from instrumented counts and read from the API. The rate shall never be presented in a form from which these can be separated.

This view carries the project's central measurement claim (SETTLEIQ-REQ-013, REQ-014). Its specification is therefore the most detailed in this document.

**API consumed.** `GET /v1/metrics/auto-match` (`window_start`, `window_end` required; optional `population_filter` of `rule_version`, `schema_version`, `generator_version`).

**Data rendered.** `rate` (decimal string), `numerator`, `denominator`, `confirmed_count`, `excluded[]` (`code`, `count`), and the full `methodology` record: `denominator_definition`, `population_description`, `window {start, end, timezone}`, `human_confirmation_treatment`, `rule_version`, `schema_version`, `generator_version`, `run_count`, `computed_at`, `rate_expression`.

### 5.1 The presentation contract

These requirements exist so that a reader cannot mistake the figure for an unqualified accuracy claim.

**SETTLEIQ-UI-R13 (OWNER-DEFINED):** The rate shall never be rendered without `numerator` and `denominator` visible in the same viewport. A percentage without its counts is a headline; a percentage with its counts is a measurement.

**SETTLEIQ-UI-R14 (OWNER-DEFINED):** The methodology block shall render every field of the `methodology` record returned by the API. The rendering shall be driven by the record's fields, not by a hardcoded field list, so that a methodology field added at the API cannot be silently dropped at the client. A completeness test enumerating the record's fields against the rendered fields enforces this.

**SETTLEIQ-UI-R15 (OWNER-DEFINED):** The client source shall contain no numeric literal for any published figure. The rate, numerator, denominator, confirmed count, excluded counts, window bounds, and population counts are read from the API response. Static explanatory text may describe the method but shall contain no numbers. A lint gate enforcing "no numeric literals outside declared test fixtures and layout constants" closes this; the point is that the figure cannot have been authored.

**SETTLEIQ-UI-R16 (OWNER-DEFINED):** The human-confirmation treatment shall be displayed as a labelled quantity: the count of human-confirmed ambiguous decisions in the population (`confirmed_count`) and the text of `human_confirmation_treatment`, adjacent to the rate. The reader shall be able to see, without leaving the view, how human confirmations enter the figure.

**SETTLEIQ-UI-R17 (OWNER-DEFINED):** The effective window shall be displayed as an explicit UTC interval with its timezone, echoed from the methodology record rather than restated by the client. The request's window parameters shall be required; the client shall not supply a default and shall not render a figure until the window is explicit (mirroring API-R12 §5.3.4).

**SETTLEIQ-UI-R18 (PROPOSED):** Every excluded category shall be rendered with its count. Exclusion without a visible count is a silent exclusion.

**SETTLEIQ-UI-R19 (PROPOSED):** The figure shall be labelled with the `rule_version`, `schema_version`, and `generator_version` it was computed under, so a reader can see that the number is scoped to a rule set and a synthetic population rather than asserted generally. The view shall additionally state, in number-free prose, that the population is generator-produced (SETTLEIQ-REQ-002) and that the figure describes that population under that rule version — nothing more.

**SETTLEIQ-UI-R20 (PROPOSED):** The methodology text shall be generic and number-free, and shall say what the figure is *not*: not an accuracy claim across processor data at large, not a claim about any other system, and not a figure that survives a change of rule version or window. The words carry the scope; the numbers come only from the API (R15).

**Interactions.** Set the window (required, explicit UTC bounds); optionally narrow by `rule_version`, `schema_version`, or `generator_version`; read the figure with its methodology; change the window and observe both the figure and every methodology field change together.

**Acceptance criterion.** A contract test shall assert that the rendered `rate` equals the API's `rate` string exactly, and that `numerator`, `denominator`, and `confirmed_count` render as the API returned them. A methodology-completeness test shall enumerate the record's fields and fail if any is unrendered (R14). A source gate shall fail if any numeric literal for a published figure exists in client source (R15). A window test shall change the bounds and assert the methodology block's window, counts, and figure all change consistently. A scope test shall assert the rule-version, schema-version, and generator-version labels render on every display of the figure.

---

## 6. View 5 — Run History and Diff (UC-5 Reproduce)

**Functional requirement SETTLEIQ-UI-R21 (PROPOSED):** The view shall list prior runs with their identity tuples, allow re-running a prior input, and diff the re-run against the original: added, removed, and changed decisions and discrepancies, and outcome-count differences. Determinism is the property under observation: re-running an identical input under an identical rule version shall produce an identical result, and the diff shall show it.

**API consumed.** `GET /v1/runs`; `POST /v1/runs` (re-run with `input.kind: "input_digest"`); `GET /v1/runs/{runId}/diff?against={otherRunId}`.

**Data rendered.** Run list rows (`run_id`, `input_digest`, `rule_version`, `schema_version`, `status`); the diff's `identical` flag, `decisions {added, removed, changed}`, `discrepancies {added, removed, changed}`, and `outcome_counts` for both sides.

**Interactions.** Select a prior run; re-run its input under the same or a different `rule_version`; view the diff; drill from a diff entry into the affected decision or discrepancy; observe the `identical` flag and understand its meaning from an inline, number-free explanation.

**Acceptance criterion.** A determinism test shall re-run an identical `(input_digest, rule_version, schema_version)` tuple and assert `identical: true` with empty added/removed/changed sets and equal outcome counts. A second test shall re-run under a different `rule_version` and assert the diff reports the changed entries, each individually retrievable. A third shall assert the client renders no diff count it computed itself (UI-R06).

---

## 7. Non-Goals

**SETTLEIQ-UI-R22 (OWNER-DEFINED):** The following are excluded from the first build and shall not be built, stubbed, or half-built:

1. **Authentication UI.** No login, no session management, no user records.
2. **Multi-tenancy.** No tenant switcher, no tenant scoping, no tenant administration.
3. **Theming.** No theme system, no dark mode, no design tokens (R04).
4. **Mobile layout.** No responsive phone layout; the interface targets a desktop viewport and states so rather than pretending otherwise.
5. **Real-time streaming.** No WebSocket or server-push; refresh is user-initiated or bounded interval polling, and views shall say when they last refreshed.

**SETTLEIQ-UI-R23 (PROPOSED):** Also excluded: user management of any kind, export/report generation from the client (the API serves investigation reads; recorded output comes from the reproduction command, not from the browser), and any chart or visualization not demanded by a functional requirement above. The metrics view renders its quantities as labelled values and tables; no chart library is authorized by any requirement in this document.

---

## 8. Not Specified Yet

| ID | Item | Why |
|---|---|---|
| N-12 | Client framework (or framework-free) choice | The requirements above constrain the client (TypeScript, generated types, no component library) without dictating a framework. The choice needs evaluation against repo CI and the single-command reproduction path; recording it now would decide ahead of evidence. |
| N-13 | Poll interval for run status and queue freshness | Needs the measured engine run duration at demo scale (OQ-04). Any value chosen now would be decoration. |
| N-14 | Visual density and layout details | Deliberately unspecified: R04 forbids design decisions that no functional requirement demands. Layout is whatever renders the required data legibly. |

---

## 9. Traceability

| Requirement(s) | Traces to |
|---|---|
| UI-R01, R02 | SETTLEIQ-DEC-001 Q4; SETTLEIQ-REQ-003 |
| UI-R03 | SETTLEIQ-DEC-001 Q4; SETTLEIQ-REQ-003 |
| UI-R04 | SETTLEIQ-DEC-001 Q4 (technology constraint) |
| UI-R05 | API-R07 (`09`) |
| UI-R06 | SETTLEIQ-REQ-013, REQ-014; ADR-004 |
| UI-R07, R08 | SETTLEIQ-REQ-003 |
| UI-R09 | UC-1; SETTLEIQ-DEC-001 Q4 row 1 |
| UI-R10 | UC-2; SETTLEIQ-REQ-008 |
| UI-R11 | UC-3; SETTLEIQ-REQ-007, REQ-009 |
| UI-R12…R20 | UC-4; SETTLEIQ-REQ-013, REQ-014; `09` §2.8 |
| UI-R21 | UC-5; SETTLEIQ-REQ-012 |
| UI-R22 | SETTLEIQ-DEC-001 Q4 (explicitly out of scope); SETTLEIQ-REQ-001, REQ-002 |

Nothing in this document is implemented. No client exists. No view has been rendered. No acceptance test has run.
