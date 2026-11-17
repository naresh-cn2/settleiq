# SettleIQ v0.1.0 — Public Release

## What's New

SettleIQ is now publicly available as an open-source financial reconciliation platform.

### Core Features

- **Exact decimal arithmetic** — No floating-point errors in financial calculations
- **Payout decomposition** — Breaks down payouts into charges, fees, refunds, and adjustments
- **7 discrepancy types** — NET_GROSS_BREAK, AMOUNT_BREAK, TIMING_BREAK, PHANTOM_PROCESSOR, PHANTOM_BANK, AMBIGUOUS_MATCH, UNKNOWN
- **Visual transaction traces** — Graph-based fund journey reconstruction
- **Evidence-backed investigation** — Ranked hypotheses with supporting and contradicting evidence
- **Hash-chained audit journal** — SHA-256 tamper-evident record-keeping
- **JSON and CSV export** — Export runs and discrepancies
- **Full REST API** — For developers building reconciliation into their applications
- **Public demo** — Try without signing up at https://settleiq-zeta.vercel.app

### API Endpoints

- `POST /v1/runs` — Create reconciliation run
- `GET /v1/runs` — List runs
- `GET /v1/runs/{id}` — Get run detail
- `GET /v1/runs/{id}/discrepancies` — List discrepancies for a run
- `GET /v1/discrepancies/{id}` — Get discrepancy detail
- `GET /v1/discrepancies/{id}/investigate` — Get investigation report
- `GET /v1/runs/{id}/trace/{constituent_id}` — Get transaction trace
- `POST /v1/discrepancies/{id}/resolve` — Resolve discrepancy (production)
- `POST /v1/demo/discrepancies/{id}/resolve` — Resolve discrepancy (demo)
- `POST /v1/demo/session` — Create public demo session
- `GET /v1/demo/runs` — Get demo runs
- `GET /v1/demo/runs/{id}/decomposition` — Get payout decomposition
- `GET /v1/demo/runs/{id}/export` — Export demo run (JSON/CSV)
- `POST /v1/import/validate` — Validate import data

### Architecture

- FastAPI backend with SQLite/PostgreSQL persistence
- React 18 + TypeScript frontend
- HMAC-SHA256 stateless demo tokens
- HMAC-SHA256 API key authentication
- Cache-Control: no-store on all API responses
- Security headers (CSP, X-Content-Type-Options, X-Frame-Options, etc.)

### Testing

- 226 backend tests passing
- 28 local browser E2E tests passing
- Ruff static analysis: 0 warnings
- TypeScript: 0 errors
- Vite production build: passing

### Limitations

- Demo mode supports read-only resolution preview (requires API key for persistence)
- Production decomposition endpoint not yet persisted for production runs
- CSV export UI button not yet on frontend (backend supports it)
- PostgreSQL tests require live DSN (8 skipped)
- No live bank/processor connections (import is JSON/CSV file-based)
- No billing/subscriptions implemented yet

### Environment Variables

- `SETTLEIQ_DEMO_SECRET` — HMAC key for demo tokens (min 32 chars)
- `SETTLEIQ_API_KEY` — API key for production endpoints
- `SETTLEIQ_CORS_ORIGIN` — CORS origin
- `SETTLEIQ_DB_PATH` — Database path (default: SQLite)
- `SETTLEIQ_SESSION_SECRET` — Session secret for user authentication

### Deployment

Production deployment: https://settleiq-zeta.vercel.app

### Contributing

Open an issue on GitHub: https://github.com/naresh-cn2/settleiq/issues

### License

MIT License