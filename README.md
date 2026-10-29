# SettleIQ

[![Python: 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6.svg)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Tests: 170 Passing](https://img.shields.io/badge/Tests-170%20Passing-brightgreen.svg)](tests/)
[![Money Safety: Zero-Float Enforced](https://img.shields.io/badge/Money%20Safety-Zero--Float%20AST-success.svg)](src/settleiq/money/)
[![Proof-of-Work: Verified](https://img.shields.io/badge/Proof--of--Work-Verified%20LATEST-blueviolet.svg)](proof/PROOF_MANIFEST.md)

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
                               | 5-View React/TS Workspace     |
                               | - Visual Money Journey Trace  |
                               | - AI Forensic Co-Pilot        |
                               | - 60-Second Guided Demo Seed  |
                               +-------------------------------+
```

---

## Key Features

1. **Exact Decimal Monetary Arithmetic:** Zero binary float operations (`FloatProhibited` enforced by AST static analyzer gate). Per-currency decimal exponent compliance.
2. **Constituent-Level Payout Decomposition:** Matches transactions at constituent level rather than comparing gross totals. Unexplained residuals are tracked explicitly (`RESIDUAL`).
3. **Deterministic Reconciliation:** Precedence-ordered matching rules (`R-EXACT-REFERENCE`, `R-EXACT-AMOUNT`) with strict settlement windows.
4. **Closed Discrepancy Taxonomy:** Typed breaks (`NET_GROSS_BREAK`, `AMOUNT_BREAK`, `TIMING_BREAK`, `PHANTOM_PROCESSOR`, `PHANTOM_BANK`, `AMBIGUOUS_MATCH`, `UNKNOWN`).
5. **Autonomous AI Forensic Investigator:** Deterministic evidence-backed reasoning engine generating ranked hypotheses with verifiable citations and one-click draft resolutions.
6. **Visual Transaction Journey Trace:** Graph-based fund journey reconstruction (`[Charge] -> [Fee] -> [Net Expected] -> [Payout] -> [Bank Deposit]`) with per-node status and balance close indicators.
7. **Tamper-Evident Audit Journal:** SHA-256 cryptographic hash-chained ledger verifying payload and sequence integrity with verified tamper detection.
8. **Dual Enterprise Persistence:** Full support for PostgreSQL 16 with versioned migrations (`001_initial_schema.sql`) and SQLite with transactional boundaries.
9. **Secured REST API:** Endpoints providing idempotent run execution, AI investigation, transaction tracing, rate limiting, and constant-time authentication.
10. **Interactive 5-View Dashboard:** Modern React 18 / TypeScript single-page application with 60-second guided tour demo seed served directly by FastAPI.
11. **Proven Scale:** Algorithmic $O(N)$ candidate pre-indexing reconciling 100,000 records in 37.49 seconds with <192MB peak memory.

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
# 1. Run the entire automated test suite (170 passing tests)
pytest -v

# 2. Verify the Money-Safety Static Gate (AST zero-float verification)
python -m settleiq.cli gate

# 3. Run the reproducible CLI reconciliation demonstration
python -m settleiq.cli run

# 4. Verify code quality with Ruff
python -m ruff check src tests

# 5. Capture cryptographic proof-of-work bundle
python scripts/capture_proof.py
```

### 3. Launch Web Dashboard & REST API

```bash
# Build frontend static bundle (if modifying TypeScript code):
npm --prefix frontend run build

# Start the application server:
uvicorn settleiq.api.app:app --reload --port 8000
```
Navigate to **`http://localhost:8000/`** to interact with the workspace:
- **Run History View (`/`)**: Overview of all reconciliation runs and one-click **⚡ 60-Second Demo Seed**.
- **Run Detail View (`/runs/:runId`)**: Filtered breakdown of eligible constituents and discrepancies.
- **Discrepancy Investigation View (`/discrepancies`)**: Discrepancy queue across all runs.
- **Investigation Detail View (`/discrepancies/:id`)**: Visual fund journey trace, AI forensic co-pilot hypotheses, and immutable resolution workflow.
- **Metrics View (`/metrics`)**: Auto-match rates, quarantine metrics, and methodology definitions.
- **History View (`/history`)**: Multi-run trend analysis and ledger integrity audits.

---

## Cryptographic Proof-of-Work Pipeline

SettleIQ maintains a permanent, verifiable proof-of-work pipeline in [`proof/`](proof/). Any external auditor can execute:

```bash
python scripts/capture_proof.py
```

This autonomously verifies all 8 quality gates and outputs raw machine-readable JSON artifacts:
- [`proof/PROOF_MANIFEST.md`](proof/PROOF_MANIFEST.md): Executive proof-of-work summary.
- `proof/builds/LATEST/manifest.json`: Environment metadata and gate results.
- `proof/builds/LATEST/gate_results.json`: AST zero-float verification logs.
- `proof/builds/LATEST/test_results.json`: Pytest execution logs (170 passing tests).
- `proof/builds/LATEST/investigator_evaluation.json`: AI investigator ground-truth benchmark (100% Top-1 accuracy).
- `proof/builds/LATEST/journal_verification.json`: Tamper resistance verification logs.
- `proof/builds/LATEST/demo_journey_trace.json`: 8-step end-to-end workflow execution trace.
- `proof/builds/LATEST/benchmark_results.json`: 10,000-record scale and memory benchmarks.
- `proof/builds/LATEST/benchmark_results.json`: 10,000-record scale and memory benchmarks.

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
| **10,000** | 8,421 rec/s | 2,188 rec/s | 19.03 MB | 6.42 s |
| **50,000** | 2,082 rec/s | 3,933 rec/s | 95.27 MB | 36.73 s |
| **100,000** | **9,223 rec/s** | **3,752 rec/s** | **191.29 MB** | **37.49 s** |

Run the benchmark locally:
```bash
python benchmarks/benchmark_engine.py --scales 1000 10000 50000 100000 --json
```
Full profiling analysis: [`docs/PERFORMANCE_REPORT.md`](docs/PERFORMANCE_REPORT.md).

---

## Knowledge Base & Engineering Dossiers

### Product Strategy & Requirements
- [`docs/product/PRODUCT_VISION.md`](docs/product/PRODUCT_VISION.md): Architectural tenets, user outcomes, and product vision.
- [`docs/product/PRODUCT_REQUIREMENTS.md`](docs/product/PRODUCT_REQUIREMENTS.md): Functional (FR-01 to FR-08) & non-functional requirements.
- [`docs/product/USER_PERSONAS.md`](docs/product/USER_PERSONAS.md): Personas (Alex Chen, Maya Patel, Marcus Vance, Elena Rostova) and 60-second journey map.
- [`docs/product/PRODUCT_ACCEPTANCE_CRITERIA.md`](docs/product/PRODUCT_ACCEPTANCE_CRITERIA.md): Six formal acceptance gates (G1 through G6).

### Market & Competitive Intelligence
- [`docs/research/COMPETITIVE_LANDSCAPE.md`](docs/research/COMPETITIVE_LANDSCAPE.md): Competitive profiles on BlackLine, Modern Treasury, HighRadius, Numeric.
- [`docs/research/COMMERCIAL_PRODUCT_MATRIX.md`](docs/research/COMMERCIAL_PRODUCT_MATRIX.md): 25-dimension feature matrix comparing SettleIQ against commercial systems.
- [`docs/research/OPEN_SOURCE_REPOSITORY_AUDIT.md`](docs/research/OPEN_SOURCE_REPOSITORY_AUDIT.md): Technical teardown of open-source reconciliation tools.
- [`docs/research/FEATURE_GAP_ANALYSIS.md`](docs/research/FEATURE_GAP_ANALYSIS.md): Key industry gaps and SettleIQ solutions.
- [`docs/research/ARCHITECTURE_COMPARISON.md`](docs/research/ARCHITECTURE_COMPARISON.md): Architectural comparison of reconciliation paradigms.
- [`docs/research/RESEARCH_SOURCES.md`](docs/research/RESEARCH_SOURCES.md): Authoritative citations and financial standards references.

### Incident Register & Engineering Case Studies
- [`docs/failure-investigations/FAILURES_INDEX.md`](docs/failure-investigations/FAILURES_INDEX.md): Central incident registry.
- [`docs/failure-investigations/FAIL-0001_FAKE_RESOLUTION_MUTATION.md`](docs/failure-investigations/FAIL-0001_FAKE_RESOLUTION_MUTATION.md): Disconnected route resolution RCA & transactional fix.
- [`docs/failure-investigations/FAIL-0002_QUADRATIC_DECOMPOSITION_BOTTLENECK.md`](docs/failure-investigations/FAIL-0002_QUADRATIC_DECOMPOSITION_BOTTLENECK.md): $O(P \times N)$ bottleneck RCA & $O(N)$ hash partitioning fix.
- [`docs/failure-investigations/FAIL-0003_STATIC_DASHBOARD_ROUTING_MISMATCH.md`](docs/failure-investigations/FAIL-0003_STATIC_DASHBOARD_ROUTING_MISMATCH.md): FastAPI static mount vs SPA client routing fix.
- [`docs/case-studies/CASE_STUDY_01_ZERO_FLOAT_FINANCIAL_ENGINEERING.md`](docs/case-studies/CASE_STUDY_01_ZERO_FLOAT_FINANCIAL_ENGINEERING.md): Eliminating float drift via AST static gate.
- [`docs/case-studies/CASE_STUDY_02_HASH_CHAINED_AUDIT_LEDGER.md`](docs/case-studies/CASE_STUDY_02_HASH_CHAINED_AUDIT_LEDGER.md): Merkle-style tamper detection for SOX 404 compliance.
- [`docs/case-studies/CASE_STUDY_03_LINEAR_SCALING_100K_WORKLOADS.md`](docs/case-studies/CASE_STUDY_03_LINEAR_SCALING_100K_WORKLOADS.md): Algorithmic batch partitioning and candidate pruning.

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
