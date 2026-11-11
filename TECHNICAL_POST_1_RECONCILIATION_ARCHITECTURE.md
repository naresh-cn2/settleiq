# SettleIQ Reconciliation Architecture

> **Publication date:** November 10, 2026  
> **Production URL:** https://settleiq-zeta.vercel.app  
> **Repository:** github.com/naresh-cn2/settleiq  
> **Data note:** All examples use synthetic financial data only. No real customer information is used.

## Overview

SettleIQ is a deterministic, exact-decimal financial reconciliation engine. Every input is validated, matched against declared rules, and journaled in a tamper-evident audit chain. The system fails closed: any record the engine cannot confidently resolve is surfaced as a typed discrepancy, never silently dropped or force-matched.

## Core Design Principles

### 1. Constituent-Level Decomposition (SETTLEIQ-REQ-006)

A payout is **never** reconciled by comparing payout totals. Instead, each payout is decomposed into its constituents — the individual charges, fees, refunds, and adjustments that compose it. Each constituent is matched independently.

```
Payout $90.00
├── Charge $100.00 (REF-001, +1)
└── Fee $10.00 (REF-001, -1)
    Net expected: $90.00
    Net paid: $90.00
    Residual: $0.00 → closes exactly
```

### 2. Exact-Decimal Arithmetic

All monetary values use Python's `Decimal` type, never `float`. This eliminates floating-point rounding errors that could create false discrepancies or mask real ones in financial data.

### 3. Closed Discrepancy Taxonomy (SETTLEIQ-REQ-013)

Every break is classified into a closed taxonomy with an explicit `UNKNOWN` category. Breaks that cannot be named are surfaced as `UNKNOWN`, never forced into the nearest type.

**Types:** PHANTOM_PROCESSOR, PHANTOM_BANK, PHANTOM_LEDGER, LOST, SIDE_MISMATCH, AMOUNT_BREAK, ROUNDING_RESIDUAL, CURRENCY_BREAK, FEE_MISATTRIBUTION, FEE_MISSING, NET_GROSS_BREAK, TIMING_BREAK, SETTLEMENT_LAG_BREAK, AMBIGUOUS_MATCH, INSUFFICIENT_EVIDENCE, RULE_CONFLICT, UNKNOWN.

### 4. Fail-Closed Semantics (SETTLEIQ-REQ-009)

If `SETTLEIQ_API_KEY` is not configured, all `/v1/*` endpoints return 401. If a record cannot be matched by any rule, it is classified as `INSUFFICIENT_EVIDENCE`, not ignored.

## Reconciliation Pipeline

```
Input Records
    │
    ▼
┌─────────────────┐
│ Validation      │ ← Schema validation, monetary fields as strings
│ (validate_records)│
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Decomposition   │ ← Payout → constituents (charges, fees, etc.)
│ (decompose)     │     Each constituent tracked with source_id
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Rule Evaluation │ ← Matched against declared rules
│ (evaluate)      │     DETERMINISTIC / AMBIGUOUS / RULE_CONFLICT / INSUFFICIENT
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Discrepancy     │ ← Typed breaks with severity classification
│ Classification  │     PHANTOM_PROCESSOR, NET_GROSS_BREAK, etc.
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Audit Journal   │ ← Hash-chained, tamper-evident
│ (Journal)       │     Every run and resolution recorded
└─────────────────┘
```

## Auto-Match Rate

The auto-match rate is computed as:

```
rate = deterministic / eligible
```

- **Eligible:** Every charge/fee/refund/adjustment/payout/deposit record presented to the matching engine
- **Deterministic:** Records matched by exactly one rule (no ambiguity, no conflict, no insufficient evidence)

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/health` | GET | Liveness check |
| `/v1/runs` | POST | Create reconciliation run (idempotent) |
| `/v1/runs` | GET | List all runs |
| `/v1/runs/{id}` | GET | Get run details + discrepancy count |
| `/v1/runs/{id}/discrepancies` | GET | List discrepancies for a run |
| `/v1/runs/{id}/discrepancies/{id}/investigate` | GET | AI-backed investigation trace |
| `/v1/runs/{id}/metrics` | GET | Auto-match rate and counts |
| `/v1/runs/{id}/export` | GET | JSON export of run + discrepancies |
| `/v1/discrepancies` | GET | Top-level discrepancy query |
| `/v1/discrepancies/{id}` | GET | Discrepancy detail |
| `/v1/discrepancies/{id}/resolve` | POST | Record resolution in audit journal |
| `/v1/journal/verify` | POST | Verify audit chain integrity |
| `/v1/demo/seed` | POST | One-click synthetic demo data |

## Production Status

| Component | Status | Details |
|-----------|--------|---------|
| Backend (FastAPI) | ✅ Deployed | Vercel Python runtime (`@vercel/python@6.50.0`) |
| Frontend (React/Vite) | ✅ Deployed | Vite + React dashboard |
| Database | ⚠️ Ephemeral | SQLite in `/tmp` — managed PostgreSQL required for production durability |
| Authentication | ✅ Fail-closed | API key via `X-API-Key` header |
| Public URL | ✅ Live | https://settleiq-zeta.vercel.app |
| Health Endpoint | ✅ Working | `/health` and `/v1/health` return 200 OK |

### Verification Evidence

- **Backend tests:** 205 passed, 0 failed (8 PostgreSQL tests skipped)
- **Regression tests:** 5 passed, 0 failed (REF-001 exact match, REF-002 short payment, REF-003 missing payout, rate formula, discrepancy mapping)
- **E2E production tests:** 28 passed, 0 failed against live deployment
- **All examples use synthetic data only** — no real customer financial information
