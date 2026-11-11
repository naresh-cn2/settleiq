# SettleIQ — Portfolio Handoff for CN2.DEV

## Product Overview

**Product Name:** SettleIQ  
**Product Type:** Financial reconciliation engine (B2B SaaS / licensed software)  
**Production URL:** `https://settleiq-zeta.vercel.app`  
**Repository:** `github.com/naresh-cn2/settleiq`  
**Current Status:** Deployed and operational — reconciliation workflow verified end-to-end  
**Latest Commit:** `4fe20b4` (main branch)  
**Fix Commit:** `2275d44` — reconcile rate formula and reference-level constituent mapping

## Product Description

SettleIQ is a deterministic, exact-decimal payment settlement reconciliation and discrepancy investigation engine. It decomposes payouts into their constituent charges, fees, and adjustments; matches them against declared rules; classifies any breaks into a closed taxonomy; and records everything in a hash-chained audit journal.

## Capabilities

| Capability | Description |
|------------|-------------|
| Constituent-level decomposition | Payouts broken into charges, fees, refunds, adjustments; each matched independently |
| Reference-level matching | Settlement reference used as primary matching key; prevents batch cross-contamination |
| Exact-decimal arithmetic | Python `Decimal` for all monetary values; no floating-point errors |
| Closed discrepancy taxonomy | PHANTOM_PROCESSOR, NET_GROSS_BREAK, AMOUNT_BREAK, INSUFFICIENT_EVIDENCE, UNKNOWN, and more |
| Severity classification | Declared matrix: HIGH/MEDIUM based on discrepancy type |
| Hash-chained audit journal | Tamper-evident record of all runs and resolutions |
| Idempotent runs | Same inputs → same run_id; no duplicate processing |
| AI-backed investigation | Transaction traces, hypotheses with confidence scores, recommended actions |
| Discrepancy resolution workflow | Resolve discrepancies with reason, candidate selection, and immutable journaling |
| Auto-match rate | `deterministic / eligible` with full count breakdown |
| API-first | All functionality via REST API with X-API-Key authentication (fail-closed) |

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI (Python 3.12), `@vercel/python@6.50.0` runtime |
| Frontend | React + Vite + TypeScript |
| Database | SQLite (ephemeral, `/tmp`) — production requires managed PostgreSQL |
| Authentication | API key via `X-API-Key` header |
| Deployment | Vercel Services (backend + frontend) |
| Testing | pytest (213 backend tests), vitest (frontend) |

## Verified Implementation Evidence

### Test Results

| Suite | Passed | Failed | Skipped |
|-------|--------|--------|---------|
| Backend (pytest) | 205 | 0 | 8 (PostgreSQL) |
| Regression (new) | 5 | 0 | 0 |
| E2E (production) | 28 | 0 | 0 |

### Regression Test Coverage

| Test | Verifies |
|------|----------|
| REF-001 exact match | Charge $100 − Fee $10 = Payout $90 closes exactly |
| REF-002 short payment | Charge $200 − Fee $20 = Expected $180 vs Paid $150 → NET_GROSS_BREAK, $30 residual |
| REF-003 missing payout | Charge $300 + Fee $30, no payout → PHANTOM_PROCESSOR for both |
| Rate formula | `rate = deterministic / eligible` = 2/8 = 0.25 |
| Discrepancy mapping | All discrepancies map to valid source record IDs |

### Key Bug Fix

**Root cause:** `decompose()` filtered constituents by batch only, causing payouts sharing a batch to claim each other's records.

**Fix:** Added reference-level filtering — when a payout carries a settlement reference, only constituents with matching references are included.

**Files changed:**
- `src/settleiq/engine/decompose.py` — reference filtering (lines 130-150)
- `src/settleiq/engine/reconcile.py` — rate formula addition (lines 387-393)
- `tests/test_reconciliation_correctness.py` — 5 new regression tests

**Commit:** `4fe20b4` on `main` branch, pushed to GitHub

## Current Status

### What Works
- Authentication (valid/missing/wrong API key)
- Reconciliation run creation and idempotent replay
- Run details, discrepancy listing, and investigation
- Discrepancy resolution with audit journaling
- Auto-match rate calculation and metrics
- JSON export of runs and discrepancies
- Audit chain verification
- Frontend dashboard (Runs, Discrepancies, Metrics, History pages)
- Public health endpoint (`/health`, `/v1/health`)

### Limitations (Production Blockers)

| Limitation | Impact | Required Action |
|------------|--------|-----------------|
| SQLite in `/tmp` | Data lost on redeploy | Configure `SETTLEIQ_DB_PATH` to managed PostgreSQL |
| `SETTLEIQ_CORS_ORIGIN` not set | Browser CORS blocked for non-localhost domains | Set to production frontend URL |
| Test API key not rotated | Security risk | Rotate before real customer use |
| SessionStorage for API key | Auth lost on page refresh | Use localStorage or HTTP-only cookies |
| No rate limiting persistence | Rate limit resets on cold start | Redis-backed limiter for production |
| Production deployment | Verified live | Promoted to production via Vercel alias |

### Deployment Status

- Code committed to GitHub at `4fe20b4`
- Vercel auto-deployed from GitHub push
- Production URL `https://settleiq-zeta.vercel.app` — verified live with corrected code
- Production alias points to deployment `settleiq-2m0sovwhp-naresh-cn2s-projects.vercel.app` (commit `4fe20b4`)

### Production Verification Evidence

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Health endpoint | 200 OK | 200 OK | ✅ |
| Valid API key | Accepted | 200 OK | ✅ |
| Old API key | Rejected | 401 | ✅ |
| REF-001 exact match | closes exactly | closes exactly | ✅ |
| REF-002 $30 short | NET_GROSS_BREAK, $30 residual | NET_GROSS_BREAK, $30 residual | ✅ |
| REF-003 missing payout | PHANTOM_PROCESSOR ×2 | PHANTOM_PROCESSOR ×2 | ✅ |
| Rate formula | 2/8 = 0.25 | 0.25 | ✅ |
| E2E production tests | 28 passed | 28 passed | ✅ |

## Commercial Positioning

**Target Market:** B2B financial services, payment processors, fintech platforms, e-commerce marketplaces, payroll providers

**Value Proposition:**
- Deterministic, auditable reconciliation with no silent failures
- Exact-decimal arithmetic for financial accuracy
- Tamper-evident audit journal for compliance
- Reference-level matching that prevents costly cross-contamination errors
- API-first architecture for easy integration

**Differentiators:**
- Closed discrepancy taxonomy (never force-matches unknown breaks)
- Fail-closed authentication (no unauthenticated access)
- Idempotent runs (no duplicate processing)
- AI-backed investigation with confidence scores

## Contact

Repository: `github.com/naresh-cn2/settleiq`  
Production: `https://settleiq-zeta.vercel.app`  
Documentation: This file + `TECHNICAL_POST_*.md` + `CASE_STUDY_*.md`
