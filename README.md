# SettleIQ

A payment settlement reconciliation and discrepancy investigation engine, built
as a **demonstrated engineering artifact for employment evidence**.

SettleIQ is an independent project. It is not governed by any other repository,
and it makes no claim about competitors, no market-gap claim, and no
commercial-viability claim. See `docs/specifications/SETTLEIQ-MASTER-SPEC.md`.

## What it does

Given a set of payment records — charges, fees, refunds, adjustments, payouts and
bank deposits — SettleIQ:

1. validates them, quarantining malformed records with a typed reason rather
   than discarding them;
2. decomposes each payout into its constituents and verifies the composition
   closes exactly;
3. matches at **constituent level**, never by comparing payout totals;
4. classifies what does not resolve into a **named** discrepancy type, never a
   generic "mismatch";
5. records tamper-evident evidence for every decision in a hash-chained audit journal;
6. reports its auto-match rate with an explicit, code-defined methodology;
7. persists reconciliation runs, discrepancies, and investigator resolutions atomically in SQLite or PostgreSQL;
8. serves an interactive 5-view React/TypeScript dashboard and secured REST API.

Money is `decimal.Decimal` everywhere. A binary float on a monetary path is a
defect, and an automated AST static gate enforces it.

## Reproduce this in one command

```bash
pip install -e .
python -m settleiq.cli run     # the full demonstration
python -m settleiq.cli gate    # the money-safety static gate
python -m pytest tests/        # 149 tests across unit, property, and integration
```

`run` loads a deterministic synthetic dataset with seven **injected defects
whose expected classifications are recorded before the run**, reconciles it, and
asserts every one is produced. It exits `0` on success and `1` if any expectation
is not met, so it is usable as a CI gate.

Add `--json` for the machine-readable report, or `--database path.sqlite3` to
persist runs.

### Run Web Dashboard and REST API

```bash
# Build the frontend assets (if modifying TypeScript code):
npm --prefix frontend run build

# Start the application server:
uvicorn settleiq.api.app:app --reload --port 8000
```
Open `http://localhost:8000/` in a browser to view the interactive dashboard.

### Run with Docker Compose (PostgreSQL + API + UI)

```bash
docker compose up -d
```
The multi-stage container automatically compiles the React dashboard, provisions PostgreSQL with versioned migrations, and starts the hardened application worker on `http://localhost:8000`.

### Run Benchmarks

```bash
python benchmarks/benchmark_engine.py --scales 1000 10000 50000 100000 --json
```

## Performance & Scale Validation

SettleIQ reconciles **100,000 financial records in under 38 seconds** on standard hardware with strictly linear $O(N)$ algorithmic scaling:

| Scale (Records) | Validation Throughput | Reconciliation Throughput | Peak Heap Memory | Total Time |
|:---|:---|:---|:---|:---|
| **1,000** | 7,697 rec/s | 3,937 rec/s | 1.94 MB | 0.38 s |
| **10,000** | 8,421 rec/s | 903 rec/s | 19.03 MB | 12.26 s |
| **50,000** | 2,082 rec/s | 3,933 rec/s | 95.27 MB | 36.73 s |
| **100,000** | 9,223 rec/s | 3,752 rec/s | 191.29 MB | 37.49 s |

See [`docs/PERFORMANCE_REPORT.md`](docs/PERFORMANCE_REPORT.md) for full profiling data.

## What is verified

**Implemented and verified end-to-end:**
* **Exact monetary arithmetic:** `decimal.Decimal` everywhere, currency exponents enforced, AST float gate clean (`M1`).
* **Canonical data model:** Stable SHA-256 serialization and deterministic run identity (`M1`).
* **Ingestion validation:** Fail-closed schema enforcement with typed quarantine reasons (`M1`).
* **Concrete Stripe Adapter:** `StripeSourceAdapter` normalizing charges, fees, refunds, adjustments, payouts, and bank deposits (`M2`).
* **Payout decomposition:** Constituent gross/fee/refund calculation with explicit residual calculation (`M3`).
* **Deterministic matching:** Precedence-ordered matching rules and closed discrepancy taxonomy (`M4`).
* **Hash-chained audit journal:** Tamper-evident ledger detecting payload/digest mutations and deletions (`M5`).
* **Dual persistence:** Production SQLite and PostgreSQL implementations with transactional rollback safety (`M5`).
* **REST API:** 9 endpoints with idempotent execution, constant-time API key auth, sliding-window rate limiting, and 10MB payload ceilings (`M6`).
* **5-View Web Dashboard:** React 18 / TypeScript SPA compiled and delivered by FastAPI (`M7`).
* **Scale validation:** Empirical linear scaling proven to 100,000 records (`M8`).
* **Containerized deployment:** Multi-stage `Dockerfile`, `docker-compose.yml`, and backup/restore documentation (`M9`).
* **149 automated tests:** 100% passing across unit, property, integration, security, and 18-step acceptance workflow suites.

## Documentation Index

| Document | Purpose |
|---|---|
| [`docs/specifications/SETTLEIQ-MASTER-SPEC.md`](docs/specifications/SETTLEIQ-MASTER-SPEC.md) | Governing architectural specification |
| [`docs/specifications/17_TRACEABILITY_MATRIX_AND_CONSISTENCY.md`](docs/specifications/17_TRACEABILITY_MATRIX_AND_CONSISTENCY.md) | Requirement traceability matrix |
| [`docs/specifications/16_DECISION_REGISTER_AND_RESOLUTIONS.md`](docs/specifications/16_DECISION_REGISTER_AND_RESOLUTIONS.md) | Decision register and open question resolutions |
| [`docs/specifications/13_ROADMAP_AND_ACCEPTANCE.md`](docs/specifications/13_ROADMAP_AND_ACCEPTANCE.md) | Milestones and release gates |
| [`docs/SECURITY_REVIEW.md`](docs/SECURITY_REVIEW.md) | Comprehensive security architecture and threat model |
| [`docs/PERFORMANCE_REPORT.md`](docs/PERFORMANCE_REPORT.md) | Scale benchmarking report across 1k–100k records |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Production Docker, PostgreSQL, and backup operational guide |

## Safety Boundary

SettleIQ uses **synthetic data only** (`DataProvenance.SYNTHETIC`). It enforces a strict security boundary preventing live credential exposure or unapproved movement of production financial funds.
