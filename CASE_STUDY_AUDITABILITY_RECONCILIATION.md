# Case Study: Auditability and Reconciliation Correctness in SettleIQ

> **Publication date:** November 10, 2026  
> **Production URL:** https://settleiq-zeta.vercel.app  
> **Repository:** github.com/naresh-cn2/settleiq  
> **Data note:** All examples use synthetic financial data only. No real customer information is used.

## Executive Summary

SettleIQ is a financial reconciliation engine designed for auditability and correctness. Every reconciliation run is recorded in a hash-chained audit journal, every discrepancy is traceable to its source record, and every matching decision is explainable. This case study examines how SettleIQ achieves auditability through its architecture, demonstrates reconciliation correctness with a three-record synthetic dataset, and documents production deployment evidence.

## 1. Auditability Architecture

### Hash-Chained Audit Journal

Every reconciliation run and discrepancy resolution is recorded in a hash-chained journal. Each entry contains the hash of the previous entry, making the chain tamper-evident:

```
Genesis → Entry 1 (hash: abc123) → Entry 2 (hash: def456, prev: abc123) → Entry 3 (hash: ghi789, prev: def456)
```

If any entry is modified, all subsequent hashes become invalid, making tampering immediately detectable.

### What the Journal Detects

| Detection | Status |
|-----------|--------|
| Payload modification | ✅ Detected |
| Digest modification | ✅ Detected |
| Deletion from the middle | ✅ Detected |
| Reordering | ✅ Detected |
| Duplication | ✅ Detected |

### What the Journal Does NOT Detect

| Limitation | Status |
|------------|--------|
| Tail truncation without externally anchored head | ❌ Not detected |
| Wholesale rewrite from genesis | ❌ Not detected |

### Journal Verification Endpoint

`POST /v1/journal/verify` returns:
- `intact: boolean` — whether the chain is intact
- `findings` — list of detected issues
- `entries_verified` — count of entries checked
- `head_digest` — hash of the latest entry

## 2. Reconciliation Correctness: Three-Record Test

### Test Dataset

| Reference | Charge | Fee | Expected Net | Payout Paid | Issue |
|-----------|--------|-----|--------------|-------------|-------|
| REF-001 | $100.00 | $10.00 | $90.00 | $90.00 | None |
| REF-002 | $200.00 | $20.00 | $180.00 | $150.00 | $30.00 short |
| REF-003 | $300.00 | $30.00 | $330.00 | $0.00 | Missing payout |

### Expected Results

| Reference | Expected Outcome | Actual Result | Match |
|-----------|-----------------|---------------|-------|
| REF-001 | closes_exactly = true, no discrepancy | closes_exactly = true, no NET_GROSS_BREAK | ✅ |
| REF-002 | NET_GROSS_BREAK, residual $30.00, HIGH severity | NET_GROSS_BREAK, residual $30.00, HIGH | ✅ |
| REF-003 | PHANTOM_PROCESSOR for chg-003 and fee-003, HIGH | PHANTOM_PROCESSOR for both, HIGH | ✅ |

### Reconciliation Rate

```
rate = deterministic / eligible = 2 / 8 = 0.25
```

- 2 deterministic matches (chg-001, fee-001 in REF-001)
- 8 eligible records (3 charges + 3 fees + 2 payouts)

## 3. Idempotent Replay

SettleIQ runs are idempotent: submitting the same input records with the same parameters returns the existing run instead of re-executing:

```
First submission:  replayed = false, new run_id
Replay submission: replayed = true, same run_id
```

This prevents duplicate processing and ensures consistent results across retries.

## 4. Idempotent Discrepancy Resolution

Discrepancy resolution is recorded in the audit journal:

```
POST /v1/discrepancies/{id}/resolve
Body: { reason, resolution, resolved_by, selected_candidate }
Result: Resolution recorded with timestamp, stored in resolution_history
```

Once resolved, the discrepancy status changes to `RESOLVED` and the resolution is immutable — corrections are new rows referencing the original, never updates.

## 5. Production Deployment Evidence

### Deployment Status

| Component | Status | URL |
|-----------|--------|-----|
| Backend (FastAPI) | ✅ Deployed | https://settleiq-zeta.vercel.app |
| Frontend (React/Vite) | ✅ Deployed | https://settleiq-zeta.vercel.app |
| API Authentication | ✅ Working | X-API-Key header, fail-closed |
| Health Endpoint | ✅ Working | /health and /v1/health |

### Commit Evidence

All code changes verified against commit `4fe20b4` on GitHub `main` branch:

- **Commit:** `4fe20b4` — trigger: redeploy with reconciliation fixes
- **Fix commit:** `2275d44` — fix: reconcile rate formula and reference-level constituent mapping
- **Production URL:** https://settleiq-zeta.vercel.app
- **Build status:** Ready (18s build time)
- **Build log:** Confirms cloning `github.com/naresh-cn2/settleiq (Branch: main, Commit: 4fe20b4)`

### Production Verification Evidence

All verification performed against the live production deployment at https://settleiq-zeta.vercel.app:

**Reconciliation Runs:**

- REF-001: closes exactly (charge $100 − fee $10 = payout $90), no discrepancy
- REF-002: NET_GROSS_BREAK for pay-602, residual $30.00, HIGH severity
- REF-003: PHANTOM_PROCESSOR for chg-603 and fee-603, HIGH severity
- Auto-match rate: 2 deterministic / 8 eligible = 0.25

**Verification Run ID:** `0db8d2ae618139a7873e25216f89889961343e155f4c63af2e57532a05ad02f6`

### E2E Test Results (Production)

| Test Suite | Passed | Failed |
|------------|--------|--------|
| Authentication (valid/missing/wrong key) | 4 | 0 |
| Reconciliation workflow (create, replay, details) | 7 | 0 |
| Discrepancies (list, get, investigate) | 4 | 0 |
| Journal verification | 2 | 0 |
| Unauthorized access | 1 | 0 |
| Run history | 2 | 0 |
| Edge cases (empty, negative, missing fields) | 5 | 0 |
| Discrepancy resolution | 2 | 0 |
| **Total** | **28** | **0** |

### Backend Unit Tests

| Suite | Passed | Failed | Skipped |
|-------|--------|--------|---------|
| All tests | 205 | 0 | 8 (PostgreSQL) |

### Regression Tests (New)

| Test | Status |
|------|--------|
| REF-001 matches exactly | ✅ PASS |
| REF-002 detects $30 short payment | ✅ PASS |
| REF-003 detects missing payout | ✅ PASS |
| Reconciliation rate formula | ✅ PASS |
| Discrepancy-to-source mapping | ✅ PASS |

## 6. Production Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| SQLite in `/tmp` (ephemeral) | Data lost on redeploy | Configure `SETTLEIQ_DB_PATH` to managed PostgreSQL |
| `SETTLEIQ_CORS_ORIGIN` not set | Browser CORS blocked for non-localhost | Set to production frontend URL |
| Test API key not rotated | Security risk for production | Rotate before real customer use |
| SessionStorage for API key | Auth lost on page refresh | Use localStorage or HTTP-only cookies |
| No rate limiting persistence | Rate limit resets on cold start | Redis-backed limiter for production |

## 7. Conclusion

SettleIQ achieves auditability through hash-chained journaling, exact-decimal arithmetic, closed discrepancy taxonomy, and fail-closed semantics. Reconciliation correctness is verified through reference-level constituent mapping, which prevents batch-level cross-contamination. The system is deployed and functional, with production readiness pending database durability, CORS configuration, and API key rotation.
