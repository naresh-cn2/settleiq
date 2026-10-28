# SettleIQ

[![Python: 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6.svg)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Tests: 149 Passing](https://img.shields.io/badge/Tests-149%20Passing-brightgreen.svg)](tests/)
[![Money Safety: Zero-Float Enforced](https://img.shields.io/badge/Money%20Safety-Zero--Float%20AST-success.svg)](src/settleiq/money/)

A high-performance payment settlement reconciliation and discrepancy investigation application, built as an independent, fully verified financial engineering product.

SettleIQ is an independent project governed solely by its authoritative specification ([`docs/specifications/SETTLEIQ-MASTER-SPEC.md`](docs/specifications/SETTLEIQ-MASTER-SPEC.md)).

---

## Architecture Overview

```
                                      +--------------------------+
                                      |   Stripe Source Data     |
                                      |   (Synthetic Provenance) |
                                      +-------------+------------+
                                                    |
                                                    v
                                      +--------------------------+
                                      |   StripeSourceAdapter    |
                                      | (Frozen Adapter Protocol)|
                                      +-------------+------------+
                                                    |
                                                    v
                                      +--------------------------+
                                      |   Ingestion Validation   |
                                      |  (Fail-Closed Quarantine)|
                                      +-------------+------------+
                                                    |
                     +------------------------------+-------------------------------+
                     |                                                              |
                     v                                                              v
       +----------------------------+                                 +----------------------------+
       |   Payout Decomposition     |                                 |   Deterministic Matching   |
       |  Gross - Fees - Refunds    |                                 | Precedence Rules & Windows |
       | = Net (Exact Decimal Money)|                                 | Closed Break Taxonomy      |
       +--------------+-------------+                                 +--------------+-------------+
                      |                                                              |
                      +------------------------------+-------------------------------+
                                                     |
                                                     v
                                      +--------------------------+
                                      | Transactional Engine     |
                                      |  Atomic Run & Resolution |
                                      +-------+----------+-------+
                                              |          |
                      +-----------------------+          +-----------------------+
                      |                                                          |
                      v                                                          v
       +----------------------------+                             +----------------------------+
       | Dual Persistence Layer     |                             | Hash-Chained Audit Journal |
       | - PostgreSQL 16 (Migrated) |                             | - Tamper-Evident SHA-256   |
       | - SQLite (File / Memory)   |                             | - Payload Mutation Detector|
       +--------------+-------------+                             +--------------+-------------+
                      |                                                          |
                      +-----------------------+----------+-----------------------+
                                              |
                                              v
                               +-------------------------------+
                               | Hardened FastAPI REST API     |
                               | - Constant-Time API Key Auth  |
                               | - Sliding-Window Rate Limiter |
                               | - 10MB Body Cap & Float Block |
                               +---------------+---------------+
                                               |
                                               v
                               +-------------------------------+
                               | 5-View React/TS Dashboard     |
                               | Runs, Discrepancies, Detail,  |
                               | Metrics, Run Comparison SPA   |
                               +-------------------------------+
```

---

## Key Features

1. **Exact Decimal Monetary Arithmetic:** Zero binary float operations (`FloatProhibited` enforced by AST static analyzer gate). Per-currency decimal exponent compliance.
2. **Constituent-Level Payout Decomposition:** Matches transactions at constituent level rather than comparing gross totals. Unexplained residuals are tracked explicitly (`RESIDUAL`).
3. **Deterministic Reconciliation:** Precedence-ordered matching rules (`R-EXACT-REFERENCE`, `R-EXACT-AMOUNT`) with strict settlement windows.
4. **Closed Discrepancy Taxonomy:** Typed breaks (`NET_GROSS_BREAK`, `AMOUNT_BREAK`, `TIMING_BREAK`, `PHANTOM_PROCESSOR`, `PHANTOM_BANK`, `AMBIGUOUS_MATCH`, `UNKNOWN`).
5. **Tamper-Evident Audit Journal:** SHA-256 cryptographic hash-chained ledger verifying payload and sequence integrity with verified tamper detection.
6. **Dual Enterprise Persistence:** Full support for PostgreSQL 16 with versioned migrations (`001_initial_schema.sql`) and SQLite with transactional boundaries.
7. **Secured REST API:** 9 endpoints providing idempotent run execution, genuine discrepancy resolution, sliding-window rate limiting, and constant-time authentication.
8. **Interactive 5-View Dashboard:** Modern React 18 / TypeScript single-page application served directly by FastAPI.
9. **Proven Scale:** Algorithmic $O(N)$ candidate pre-indexing reconciling 100,000 records in 37.49 seconds with <192MB peak memory.

---

## Quickstart & Reproduction

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/bukyanaresh/settleiq.git
cd settleiq

# Install Python package in editable mode with development dependencies
pip install -e ".[dev]"
```

### 2. Verify Core Gates in One Step

```bash
# 1. Run the entire automated test suite (149 passing tests)
pytest -v

# 2. Verify the Money-Safety Static Gate (AST zero-float verification)
python -m settleiq.cli gate

# 3. Run the reproducible CLI reconciliation demonstration
python -m settleiq.cli run

# 4. Verify code quality with Ruff
python -m ruff check src tests
```

### 3. Launch Web Dashboard & REST API

```bash
# Build frontend static bundle (if modifying TypeScript code):
npm --prefix frontend run build

# Start the application server:
uvicorn settleiq.api.app:app --reload --port 8000
```
Navigate to **`http://localhost:8000/`** to interact with the 5 dashboard views:
- **Run History View (`/`)**: Overview of all reconciliation runs and auto-match rates.
- **Run Detail View (`/runs/:runId`)**: Filtered breakdown of eligible constituents and discrepancies.
- **Discrepancy Investigation View (`/discrepancies`)**: Discrepancy queue across all runs.
- **Investigation Detail View (`/discrepancies/:id`)**: Audit history, evidence, and persistent resolution workflow.
- **Run Comparison View (`/compare`)**: Side-by-side reconciliation outcome comparison.

---

## Docker Deployment (PostgreSQL + API + UI)

Deploy the complete containerized stack in a single command:

```bash
docker compose up -d
```

This starts:
- `settleiq-postgres`: PostgreSQL 16 Alpine database with health checks and volume persistence.
- `settleiq-app`: Hardened multi-stage container serving the compiled React frontend and FastAPI backend on `http://localhost:8000`.

To view container logs or run database backups:
```bash
# View service logs
docker compose logs -f app

# Run database backup
docker exec -t settleiq-postgres pg_dump -U settleiq settleiq_db > backup.sql
```
Detailed operations guide: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

---

## Empirical Performance Benchmarks

Benchmark suite executed across multi-scale workloads via `benchmarks/benchmark_engine.py`:

| Scale (Records) | Ingestion Validation | Reconciliation Engine | Peak Memory | Total Latency |
|:---|:---|:---|:---|:---|
| **1,000** | 7,697 rec/s | 3,937 rec/s | 1.94 MB | 0.38 s |
| **10,000** | 8,421 rec/s | 903 rec/s | 19.03 MB | 12.26 s |
| **50,000** | 2,082 rec/s | 3,933 rec/s | 95.27 MB | 36.73 s |
| **100,000** | **9,223 rec/s** | **3,752 rec/s** | **191.29 MB** | **37.49 s** |

Run the benchmark locally:
```bash
python benchmarks/benchmark_engine.py --scales 1000 10000 50000 100000 --json
```
Full profiling analysis: [`docs/PERFORMANCE_REPORT.md`](docs/PERFORMANCE_REPORT.md).

---

## Security Baseline

- **Authentication:** Constant-time `hmac.compare_digest` protects mutating endpoints (`POST /v1/*`) when `SETTLEIQ_API_KEY` is configured.
- **Rate Limiting:** Sliding-window in-memory rate limiter protects endpoints against DoS attacks (HTTP 429).
- **Body Size Caps:** Enforces a 10MB ceiling on HTTP request payloads (HTTP 413).
- **Security Headers:** Strict Content Security Policy (CSP), `X-Content-Type-Options: nosniff`, and `X-Frame-Options: DENY`.
- Comprehensive threat modeling: [`docs/SECURITY_REVIEW.md`](docs/SECURITY_REVIEW.md).

---

## Documentation Index

| Specification / Report | Description |
|---|---|
| [`docs/specifications/SETTLEIQ-MASTER-SPEC.md`](docs/specifications/SETTLEIQ-MASTER-SPEC.md) | Authoritative master specification |
| [`docs/specifications/17_TRACEABILITY_MATRIX_AND_CONSISTENCY.md`](docs/specifications/17_TRACEABILITY_MATRIX_AND_CONSISTENCY.md) | Requirements-to-verification traceability matrix |
| [`docs/SECURITY_REVIEW.md`](docs/SECURITY_REVIEW.md) | Security review and threat model |
| [`docs/PERFORMANCE_REPORT.md`](docs/PERFORMANCE_REPORT.md) | Performance benchmark and algorithmic complexity report |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Container orchestration and database operational guide |
| [`docs/README.md`](docs/README.md) | Master documentation index |

---

## Safety & Compliance

SettleIQ enforces strict synthetic data confinement (`DataProvenance.SYNTHETIC`). The system does not hold production financial credentials, connect to live bank accounts, or execute monetary fund transfers without authorized synthetic parameters.
