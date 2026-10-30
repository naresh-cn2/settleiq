# SettleIQ Project Status

## Purpose
SettleIQ is a **payment settlement reconciliation** engine that verifies and resolves discrepancies between merchant payouts and bank statements. It is built as a verified financial engineering product governed by the
[specification]
(links to docs/specifications/SETTLEIQ-MASTER-SPEC.md).

## Architecture & Technology Stack
- **Language**: Python 3.12
- **Web API**: FastAPI 0.115+ (uvicorn server)
- **Frontend**: React 18 / TypeScript, bundled with FastAPI via static file serving
- **Persistence**: Dual‑storage – SQLite (file or memory for demos) *and* PostgreSQL 16 (migrations in `persistence/migrations`).
- **Monetary arithmetic**: Strict `decimal.Decimal` calculations with static AST gate to forbid any binary‑float usage (`tests/gates/float_gate`).
- **Reconciliation Engine**: Deterministic matching using precedence‑ordered rules, closed‑window taxonomies, and constituent‑level payout decomposition.
- **Audit Journal**: SHA‑256 hash‑chained ledger that records every run state and detects payload tampering, digest changes, deletions, reordering, and duplication.
- **CLI**: Single‑module `settleiq.cli` with sub‑commands:
  - `run` – Execute the reference demonstration
  - `gate` – Run the money‑safety static gate
  - `verify` – Load a persisted store and verify the audit journal
- **Testing**: pytest framework with 204 passing tests (unit, property, golden, determinism, integration).
- **Code quality**: Ruff checks on `src tests scripts`.
- **CI**: GitHub Actions `ci.yml` runs all tests, static linting, and headless browser E2E tests.

## Implemented Functionality
1. **Exact Decimal Monetary Arithmetic** – Zero‑float enforcement, per‑currency serialization.
2. **Deterministic Reconciliation** – Precedence rules (`R-EXACT-REFERENCE`, `R-EXACT-AMOUNT`), timed windows, tight match windows.
3. **Closed Discrepancy Taxonomy** – Typed breaks: `NET_GROSS_BREAK`, `AMOUNT_BREAK`, `TIMING_BREAK`, `PHANTOM_PROCESSOR`, `PHANTOM_BANK`, `AMBIGUOUS_MATCH`, `UNKNOWN`.
4. **AI‑Powered Forensic Investigator** – Generates ranked hypotheses backed by audit trail references.
5. **Visual Transaction Journey Trace** – React SPA shows a graph of each fund journey with status indicators.
6. **Tamper‑Evident Audit Journal** – SHA‑256 hash‑chained ledger with built‑in anomaly detection.
7. **Dual Persistence Layer** – SQLite (local demos) and PostgreSQL 16 (enterprise migrations).
8. **Secure REST API** – Constant‑time API key auth, rate limiting, size limits.
9. **Reproducible CLI Demo** – `python -m settleiq.cli run` reproduces the same deterministic output every time.

## Verification Evidence
| Check | Result | Reference |
|-------|--------|-----------|
| Latest CI run | ✅ Success (Run #40915388357) | <https://github.com/naresh-cn2/settleiq/actions/runs/40915388357> |
| Unit / integration tests | ✅ 204 passing | Log captured by CI |
| Ruff lint | ✅ Pass | CI run |
| FastAPI API | ✅ 200‑series responses on `/health` | Running `uvicorn src.settleiq.api.app:app` locally |
| Front‑end build | ✅ Pass (`npm run build`) | CI build logs |
| Static money‑safety gate | ✅ Pass (`python -m settleiq.cli gate`) | Local and CI |
| Deterministic CLI demo | ✅ Matches reference output in README | `python -m settleiq.cli run` |

## Reproduction Instructions
```bash
# 1. Clone
git clone https://github.com/naresh-cn2/settleiq.git
cd settleiq

# 2. Install Python deps (editable with dev extras)
pip install -e ".[dev]"

# 3. Run the full test suite (204 tests)
pytest -q

# 4. Verify the money‑safety static gate
python -m settleiq.cli gate

# 5. Run the deterministic CLI demonstration
python -m settleiq.cli run

# 6. Verify the audit journal for a persisted run
python -m settleiq.cli verify --database settleiq.sqlite3

# 7. Build the front‑end assets (requires Node 20+)
npm --prefix frontend install
npm --prefix frontend run build

# 8. Serve the API + static files (development mode)
uvicorn src.settleiq.api.app:app --reload
```

## Known Limitations & Production Gates
- **Production deployment** – The application has not yet been deployed to any cloud provider.
- **Live payment integrations** – Connections to real‑world merchant or bank APIs are not yet implemented.
- **Multi‑tenant architecture** – Current persistence layer assumes a single‑tenant deployment; no namespace or schema isolation.
- **Commercial validation** – No external beta‑testers or regulatory validation exists.
- **Security hardening** – Basic API key auth is in place; however, finer‑grained RBAC, audit logging, and comprehensive threat modeling are pending.
- **Scalability** – In‑process FastAPI/Uvicorn may need to be sharded behind a reverse proxy for production load.

## Engineering Completion Status
- **Scope**: Engineering scope is *frozen* as of commit `c693519`.
- **CI**: All checks green.
- **Documentation**: README, architecture diagrams, and test manifests are up‑to‑date and reflect the repo state.
- **Work tree**: Clean, no uncommitted changes.
- **Release checklist**: All items marked as complete in the `docs` and `frontend` directories have been verified.
- **Future work**: The next phase is portfolio presentation and commercial deployment preparation.
