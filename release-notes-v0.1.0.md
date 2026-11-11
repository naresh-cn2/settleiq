# v0.1.0 — Initial Public Release

**SettleIQ** is an open-source, deterministic payment settlement reconciliation engine. It matches Stripe charges, fees, refunds, and payouts with exact-decimal arithmetic, classifies discrepancies via a closed break taxonomy, and maintains a hash-chained audit journal for tamper-evident record-keeping.

---

## What's Included

### Core Engine
- **Exact-decimal money arithmetic** — No floating-point drift; AST-enforced `Decimal` operations via `settleiq.money.Money`
- **Deterministic matching** — Precedence rules (amount → date → idempotency_key → description) with configurable time windows
- **Closed break taxonomy** — 7 break types: `AMOUNT_MISMATCH`, `DATE_MISMATCH`, `MISSING_PAYOUT`, `MISSING_CHARGE`, `FEE_DISCREPANCY`, `REFUND_MISMATCH`, `ORPHANED_RECORD`
- **Hash-chained audit journal** — SHA-256 chained ledger entries for tamper detection (SOX 404 alignment)

### API & Frontend
- **FastAPI** — `/v1/runs`, `/v1/reconcile`, `/v1/breaks`, `/v1/audit`, `/v1/health`
- **React 18 + TypeScript** — Run dashboard, discrepancy explorer, metrics, history views
- **API Key auth** — `X-API-Key` header, session-scoped storage

### Testing Evidence
- **205 backend unit/integration tests** passing (pytest)
- **5 regression tests** for known defects (regression/, 5/5 pass)
- **28 production E2E tests** against live Vercel deployment (28/28 pass)
- **Zero float violations** — AST static gate enforces `Decimal` everywhere money is used

### Deployment
- **Production:** https://settleiq-zeta.vercel.app
- **Health check:** https://settleiq-zeta.vercel.app/v1/health → `{"status":"ok"}`
- **Environment:** SETTLEIQ_API_KEY rotated, SETTLEIQ_CORS_ORIGIN configured

---

## Quick Start

```bash
git clone https://github.com/naresh-cn2/settleiq.git
cd settleiq
pip install -e ".[dev]"
python -m pytest tests/ -q
```

---

## Safety & Compliance

**All financial data in this project is synthetic.** The system enforces `DataProvenance.SYNTHETIC` provenance and does not connect to live bank accounts, hold production credentials, or execute real fund transfers without authorized synthetic parameters.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Verification Checklist

- [x] 205 backend tests passing
- [x] 5 regression tests passing
- [x] 28 E2E production tests passing
- [x] Zero float violations (AST gate)
- [x] Production health endpoint returns 200 OK
- [x] MIT LICENSE file present
- [x] No secrets in tracked files or Git history
- [x] .new_api_key excluded from git (.gitignore)
- [x] Repository is public