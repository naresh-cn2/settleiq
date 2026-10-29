# SettleIQ — Product Requirements Specification

**Document ID:** SETTLEIQ-PRD-002  
**Status:** ACTIVE  
**Reference:** Aligns with `SETTLEIQ-MASTER-SPEC.md`

---

## 1. Functional Requirements (FR)

### FR-01: Universal Source Normalization
- The system must provide source adapters that normalize heterogenous transaction payloads into canonical entities (`Charge`, `Fee`, `Refund`, `Adjustment`, `Payout`, `SettlementBatch`, `BankDeposit`).
- The canonical protocol must enforce strict synthetic data isolation (`DataProvenance.SYNTHETIC`) unless authorized credentials are explicitly supplied.
- Minor currency units (e.g. Stripe cents) must convert directly into decimal strings without floating-point intermediate values.

### FR-02: Fail-Closed Ingestion & Quarantine
- Payloads missing mandatory fields, specifying invalid ISO 4217 currencies, or presenting malformed numeric strings must be partitioned into an isolated Quarantine stream.
- Quarantined records must not enter matching engine pools or inflate match rate denominators.
- Each quarantined record must preserve an inspectable error classification (`MISSING_FIELD`, `INVALID_AMOUNT`, `UNSUPPORTED_CURRENCY`, `MALFORMED_RECORD`).

### FR-03: Constituent-Level Decomposition
- For each payout batch, the system must retrieve all associated charges, fees, refunds, and adjustments.
- The system must compute:
  $$\text{Net Expected} = (\text{Gross Charges} - \text{Fees}) - \text{Refunds} - \text{Adjustments}$$
  $$\text{Residual} = \text{Net Expected} - \text{Net Paid}$$
- If $\text{Residual} = 0.00$, the decomposition closes exactly. If $\text{Residual} \neq 0.00$, a `NET_GROSS_BREAK` discrepancy is emitted.

### FR-04: Deterministic Matching Rules & Settlement Windows
- The matching engine must support precedence-ordered rules (`R-EXACT-REFERENCE`, `R-EXACT-AMOUNT`).
- Payout-to-deposit timing must enforce declared observation window parameters ($\Delta t \le \text{declared days}$).
- Discrepancies must strictly adhere to the closed taxonomy:
  - `NET_GROSS_BREAK`: Batch arithmetic shortfall.
  - `AMOUNT_BREAK`: Payout amount differs from bank settlement.
  - `TIMING_BREAK`: Settlement posted outside declared allowable window.
  - `PHANTOM_PROCESSOR`: Processor constituent present without a parent payout batch.
  - `PHANTOM_BANK`: Bank deposit reference absent on processor side.
  - `AMBIGUOUS_MATCH`: Multiple surviving candidates without tie-breaking preference.
  - `UNKNOWN`: Unmodeled source record kind surfaced explicitly.

### FR-05: Evidence-Backed AI Investigation
- Given any discrepancy ID, the investigation system must reconstruct the full transaction journey.
- The investigator must evaluate hypotheses against source records and output confidence scores, supporting records, contradicting evidence, and actionable resolution recommendations.
- When evidence is inconclusive, the investigator must explicitly declare `INSUFFICIENT_EVIDENCE`.

### FR-06: Human-in-the-Loop Discrepancy Resolution
- The system must allow authorized investigators to review findings and apply resolution actions (`WRITEOFF`, `ADJUST_FEE`, `FLAG_DISPUTE`, `FORCE_MATCH`, `ACCEPT_RESIDUAL`).
- Resolutions must be atomic: updating the discrepancy status to `RESOLVED`, recording the investigator ID and justification in `discrepancy_resolution`, and appending a tamper-evident audit journal event.

### FR-07: Dual Persistence & Versioned Migrations
- The persistence abstraction must provide seamless execution on both SQLite (local development / testing) and PostgreSQL 16 (production).
- Database migrations must be versioned, idempotent, and transactional.

### FR-08: 5-View Financial Workspace
- The web dashboard must provide:
  1. **Run History View:** Run status, input digest, auto-match rates, discrepancy counts.
  2. **Run Detail View:** Breakdown of matched constituents, fee analysis, break distribution.
  3. **Discrepancy Investigation View:** Triage queue filterable by status, severity, and type.
  4. **Investigation Detail & Trace View:** Visual monetary journey, evidence inspector, AI hypothesis card, resolution action dialog.
  5. **Run Comparison View:** Side-by-side run delta analysis.

---

## 2. Non-Functional Requirements (NFR)

### NFR-01: Performance & Scale
- The engine must sustain $\ge 3,500$ records/sec reconciliation throughput on standard 4-core hardware.
- 100,000 complete financial records must reconcile in $<45$ seconds.
- Peak memory for 100,000 records must remain below 250 MB RAM.

### NFR-02: Security & Threat Mitigation
- Mutating endpoints (`POST /v1/*`) must enforce constant-time authentication comparison (`hmac.compare_digest`).
- The API must implement IP-based sliding-window rate limiting.
- Request payload sizes must be capped at 10 MB (HTTP 413).
- HTTP responses must deliver strict security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, strict CSP).

### NFR-03: Zero Floating-Point Precision Loss
- Zero binary floating-point types (`float`, `double`) are permitted on monetary processing paths.
- AST analysis gate (`python -m settleiq.cli gate`) must pass with 0 infractions across all packages.

