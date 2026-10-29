# SettleIQ — Open Source Repository Audit & Technical Analysis

**Document ID:** SETTLEIQ-RES-003  
**Status:** ACTIVE  

---

## 1. Audited Open Source Projects

We conducted a technical evaluation of relevant open-source reconciliation, ledgering, and financial tools.

### 1. Reconify (`ReconifyHQ/reconify`)
- **Language / Stack:** TypeScript / Node.js
- **Scope:** Financial reconciliation engine supporting multiple sources, grouped settlements, and exception reporting.
- **Key Findings & Lessons:**
  - Strong grouped settlement model where multiple payment processor rows map to a single bank deposit.
  - Relies on JavaScript native numbers in parts of the codebase, which introduces potential IEEE 754 precision risks for large or high-scale multi-currency sums unless custom BigNumber abstractions are strictly maintained.
- **SettleIQ Adaptation:** SettleIQ enforces Python's standard `decimal.Decimal` with AST enforcement, preventing any floating-point arithmetic errors.

### 2. Reconcile (`nepounds/reconcile`)
- **Language / Stack:** Python
- **Scope:** Event-sourced accounting, double-entry bookkeeping, explainable bank reconciliation, rebuildable projections.
- **Key Findings & Lessons:**
  - Excellent event-sourced architecture where account balances are projections of an immutable event ledger.
  - Good emphasis on explainability: every reconciliation event links back to the underlying journal transaction.
- **SettleIQ Adaptation:** SettleIQ incorporates this explainability by requiring provenance digests on all `MatchDecision` records and storing resolutions directly into a hash-chained audit journal.

### 3. Settler (`Hardonian/Settler`)
- **Language / Stack:** Go / Python
- **Scope:** Reconciliation engine with integrations and settlement workflow management.
- **Key Findings & Lessons:**
  - Clear separation between source normalization and matching rules.
  - Lacks strict settlement timing windows (can inadvertently match transactions months apart if references coincide).
- **SettleIQ Adaptation:** SettleIQ implements declared observation windows (`DEFAULT_SETTLEMENT_WINDOW_DAYS`) and classifies late settlements as explicit `TIMING_BREAK` discrepancies.

---

## 2. Licensing & Reusability Matrix

| Project | License | Permitted for SettleIQ | Attribution Requirement | Code Borrowed |
|:---|:---|:---|:---|:---|
| **Reconify** | MIT | Yes | Standard MIT copyright notice | 0 lines (Architectural review only) |
| **Reconcile** | Apache 2.0 | Yes | Apache 2.0 attribution | 0 lines (Pattern study only) |
| **Settler** | MIT | Yes | Standard MIT copyright notice | 0 lines (Pattern study only) |

**Conclusion:** SettleIQ maintains **100% original implementation**, ensuring zero licensing ambiguity, unencumbered intellectual property, and clean attribution.

