# SettleIQ — User Personas & Journey Maps

**Document ID:** SETTLEIQ-PRD-003  
**Status:** ACTIVE  

---

## 1. Primary Personas

### Persona A: Sarah — Payment Operations Lead
- **Role:** Leads payment reconciliation for a high-volume marketplace ($50M+ GMV, 400k transactions/month).
- **Core Pain Point:** Every month-end, the finance team faces a $12,000 to $45,000 discrepancy between Stripe payout totals and Chase bank statement deposits. Tracking individual missing fees or delayed refunds takes 3 full days of manual Excel vlookups.
- **Goal in SettleIQ:** Needs one-click constituent-level settlement decomposition that flags breaks immediately, identifies the exact missing fee or charge ID, and proves mathematical closure.

### Persona B: David — Fintech Backend / Platform Engineer
- **Role:** Senior engineer building ledgering infrastructure and payment integrations.
- **Core Pain Point:** Existing reconciliation tools are vendor black boxes with brittle web scrapers, float rounding errors, and opaque matching heuristics that cannot be verified or unit-tested.
- **Goal in SettleIQ:** Wants a clean, modular Python/FastAPI service with strict Decimal arithmetic, idempotent API contracts, versioned PostgreSQL migrations, and transparent $O(N)$ matching algorithms that can be embedded into an existing transactional pipeline.

### Persona C: Marcus — External Financial Auditor (SOX 404 / SOC 1)
- **Role:** Big-4 IT audit manager auditing a fintech platform's internal financial controls.
- **Core Pain Point:** Reconciliation spreadsheets can be tampered with after month-end signoff without detection. Traditional databases allow administrators to update rows in place without preserving cryptographic proof.
- **Goal in SettleIQ:** Demands an append-only, cryptographic hash-chained audit ledger that mathematically proves historical run results, discrepancy classifications, and investigator resolutions have not been edited or altered since execution.

### Persona D: Elena — Quantitative Developer / Recruiter Evaluating Engineering Depth
- **Role:** Tech lead / hiring manager reviewing an applicant's portfolio project for a senior financial systems engineering role.
- **Core Pain Point:** Weary of trivial CRUD apps, generic todo lists, and simple wrapper projects around third-party AI APIs.
- **Goal in SettleIQ:** Inspects AST-level float safety gates, $O(N)$ candidate pre-indexing, deterministic SHA-256 preimages, 100k-record benchmark methodologies, and reproducible Docker container setups.

---

## 2. Key User Journey: 60-Second Investigation Walkthrough

```mermaid
journey
    title 60-Second Discrepancy Investigation Journey
    section Ingestion & Run
      Open SettleIQ Dashboard: 5: Sarah, David
      Load Synthetic Multi-Source Scenario: 5: Sarah, David
      Click Execute Reconciliation: 5: Sarah, David
    section Triage & Detection
      Review Auto-Match Rate (e.g. 76%): 4: Sarah
      Inspect 7 Closed Discrepancy Types: 5: Sarah, Marcus
      Filter by High Severity (NET_GROSS_BREAK): 5: Sarah
    section Investigation & Trace
      Open Discrepancy Detail: 5: Sarah
      Review Visual Monetary Trace: 5: Sarah
      Inspect AI-Generated Ranked Hypotheses: 5: Sarah, David
      Verify Supporting vs Contradicting Evidence: 5: Sarah, Marcus
    section Resolution & Audit
      Review Recommended Resolution Draft: 5: Sarah
      Approve & Enter Justification Reason: 5: Sarah
      Verify Resolution Stored in PostgreSQL: 5: David
      Verify Cryptographic Event Appended to Journal: 5: Marcus
```

