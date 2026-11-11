# 🚀 SettleIQ v0.1.0 — Initial Public Release

**SettleIQ** is now open source under the MIT License.

## What is SettleIQ?

A deterministic, exact-decimal payment settlement reconciliation engine built with FastAPI and React. It matches Stripe charges, fees, refunds, and payouts with zero floating-point drift, classifies discrepancies via a closed break taxonomy, and maintains a hash-chained audit journal for tamper-evident record-keeping.

## Key Features

- **Exact-decimal arithmetic** — AST-enforced `Decimal` operations; zero float violations
- **Deterministic matching** — Precedence rules with configurable time windows
- **7 break types** — `AMOUNT_MISMATCH`, `DATE_MISMATCH`, `MISSING_PAYOUT`, `MISSING_CHARGE`, `FEE_DISCREPANCY`, `REFUND_MISMATCH`, `ORPHANED_RECORD`
- **Hash-chained audit journal** — SHA-256 chained ledger entries (SOX 404 alignment)
- **FastAPI + React 18** — Full dashboard, discrepancy explorer, metrics, history
- **API Key auth** — Session-scoped, no server-side persistence

## Verified Testing Evidence

| Suite | Tests | Status |
|-------|-------|--------|
| Backend (pytest) | 205 | ✅ Passing |
| Regression | 5 | ✅ Passing |
| E2E (production) | 28 | ✅ Passing |
| **Total** | **238** | **0 failed** |

## Live Demo

**Production:** https://settleiq-zeta.vercel.app  
**Health:** https://settleiq-zeta.vercel.app/v1/health → `{"status":"ok"}`

## Quick Start

```bash
git clone https://github.com/naresh-cn2/settleiq.git
cd settleiq
pip install -e ".[dev]"
python -m pytest tests/ -q
```

## Safety & Compliance

**All financial data is synthetic.** The system enforces `DataProvenance.SYNTHETIC` and does not connect to live bank accounts, hold production credentials, or execute real fund transfers.

## License

MIT License — see [LICENSE](LICENSE).

---

**Repository:** https://github.com/naresh-cn2/settleiq  
**Release:** https://github.com/naresh-cn2/settleiq/releases/tag/v0.1.0

Questions, feedback, and contributions welcome!