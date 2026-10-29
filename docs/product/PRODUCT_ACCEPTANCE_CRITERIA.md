# SettleIQ — Product Acceptance Criteria & Quality Gates

**Document ID:** SETTLEIQ-PRD-004  
**Status:** ACTIVE  

---

## 1. Verifiable Acceptance Gates

To transition any capability from `IN_DEVELOPMENT` to `VERIFIED`, every criterion in the relevant gate must pass with reproducible automated proof:

### Gate 1: Money-Safety & AST Static Analysis Gate
- [x] **AC-G1.1:** Parsing of source code via Python AST scanner identifies 0 usages of binary `float()` or float literal arithmetic on monetary paths (`python -m settleiq.cli gate`).
- [x] **AC-G1.2:** Instantiating `Money(10.50, "USD")` with a Python float raises `FloatProhibited`.
- [x] **AC-G1.3:** Cross-currency operations (e.g. `Money("10.00", "USD") + Money("10.00", "EUR")`) raise `CurrencyMismatch`.
- [x] **AC-G1.4:** Exponent validation enforces standard ISO 4217 scales (JPY: 0 digits, USD: 2 digits, BHD: 3 digits) and raises `CurrencyPrecisionExceeded` on fractional violations.

### Gate 2: Deterministic Matching & Decomposition Gate
- [x] **AC-G2.1:** Rerunning the reconciliation engine on identical input records and parameters yields byte-for-byte identical `RunIdentity` hashes across execution runs and restarts.
- [x] **AC-G2.2:** Payout decomposition verifies that gross charges minus fees minus refunds minus adjustments equal net paid. Shortfalls are emitted as typed `NET_GROSS_BREAK` discrepancies with explicit residual accounting.
- [x] **AC-G2.3:** Candidates matching multiple rules without clear precedence are preserved whole in `ambiguous_set` rather than arbitrary tie-breaking.
- [x] **AC-G2.4:** Unmodeled record types are classified strictly as `UNKNOWN`, never coerced into known categories.

### Gate 3: Cryptographic Audit Trail & Tamper Detection Gate
- [x] **AC-G3.1:** Each audit journal entry contains `sequence`, `prev_digest`, `entry_digest`, `payload`, and `recorded_at`.
- [x] **AC-G3.2:** `entry_digest` is computed as $\text{SHA256}(\text{prev\_digest} \parallel \text{canonical}(\text{payload}))$.
- [x] **AC-G3.3:** Modifying any payload, digest, or deleting/reordering any entry in the database causes `journal.verify()` to fail immediately and report the specific `TamperType`.

### Gate 4: Security Hardening Gate
- [x] **AC-G4.1:** All mutating API endpoints (`POST /v1/*`) reject unauthenticated requests with HTTP 401 using constant-time comparison (`hmac.compare_digest`).
- [x] **AC-G4.2:** Sliding-window rate limiter triggers HTTP 429 when client IP request thresholds are breached.
- [x] **AC-G4.3:** Payloads exceeding 10 MB are rejected with HTTP 413.
- [x] **AC-G4.4:** Payloads containing numeric JSON floats on monetary paths are rejected with HTTP 422 Unprocessable Entity.

### Gate 5: Performance & Scale Gate
- [x] **AC-G5.1:** Workload of 1,000 records completes ingestion + reconciliation in $<1.0$ second.
- [x] **AC-G5.2:** Workload of 10,000 records completes ingestion + reconciliation in $<15.0$ seconds.
- [x] **AC-G5.3:** Workload of 100,000 records completes ingestion + reconciliation in $<45.0$ seconds with peak heap memory $<250$ MB RAM.
- [x] **AC-G5.4:** Candidate matching scaling complexity is sub-quadratic ($O(N)$ batch pre-indexing).

### Gate 6: End-to-End Acceptance Workflow Gate
- [x] **AC-G6.1:** Complete 18-step acceptance suite (`tests/integration/test_acceptance_workflow.py`) executes and passes in CI without mocks or stubbed outcomes.

