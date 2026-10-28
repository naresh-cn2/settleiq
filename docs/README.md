# SettleIQ — Documentation Index

SettleIQ is an **independent** payment settlement reconciliation and discrepancy investigation engine, built as a demonstrated engineering artifact for employment evidence. It is not governed by any other repository, and it makes no claim about competitors, no market-gap claim, and no commercial-viability claim.

---

## 1. Specification Baseline & Architectural Documents

All specifications in `docs/specifications/` govern the implemented architecture:

| # | Document | Domain of Authority | Status |
|---|---|---|---|
| — | [`SETTLEIQ-MASTER-SPEC.md`](specifications/SETTLEIQ-MASTER-SPEC.md) | Sole authority for scope, frame, and requirements | **RATIFIED & IMPLEMENTED** |
| 01 | [`01_OBJECTIVES_AND_BOUNDARIES.md`](specifications/01_OBJECTIVES_AND_BOUNDARIES.md) | Objectives, independence, boundaries, success criteria | **IMPLEMENTED** |
| 02 | [`02_PROBLEM_AND_USE_CASES.md`](specifications/02_PROBLEM_AND_USE_CASES.md) | Problem statement, actors, use cases, scope | **IMPLEMENTED** |
| 03 | [`03_EVIDENCE_AND_RESEARCH_REGISTER.md`](specifications/03_EVIDENCE_AND_RESEARCH_REGISTER.md) | Research record; verified / not verified claims | **PRESERVED** |
| 04 | [`04_REQUIREMENTS_AND_NON_GOALS.md`](specifications/04_REQUIREMENTS_AND_NON_GOALS.md) | Consolidated requirement register and binding non-goals | **IMPLEMENTED** |
| 05 | [`05_ARCHITECTURE.md`](specifications/05_ARCHITECTURE.md) | Components, boundaries, deployment view | **IMPLEMENTED** |
| 06 | [`06_DATA_MODEL_AND_PERSISTENCE.md`](specifications/06_DATA_MODEL_AND_PERSISTENCE.md) | Canonical types, schema, migrations, transaction boundaries | **IMPLEMENTED** |
| 07 | [`07_RECONCILIATION_ENGINE_SPEC.md`](specifications/07_RECONCILIATION_ENGINE_SPEC.md) | Decomposition, matching, confidence, fail-closed, determinism | **IMPLEMENTED** |
| 08 | [`08_DISCREPANCY_AND_AUDIT_SPEC.md`](specifications/08_DISCREPANCY_AND_AUDIT_SPEC.md) | Typed taxonomy, investigation workflow, hash-chained audit | **IMPLEMENTED** |
| 09 | [`09_API_AND_INTEGRATION_SPEC.md`](specifications/09_API_AND_INTEGRATION_SPEC.md) | REST/OpenAPI, frozen `SourceAdapter` interface, idempotency | **IMPLEMENTED** |
| 10 | [`10_DASHBOARD_SPEC.md`](specifications/10_DASHBOARD_SPEC.md) | Five functional views | **IMPLEMENTED** |
| 11 | [`11_TESTING_AND_PERFORMANCE_SPEC.md`](specifications/11_TESTING_AND_PERFORMANCE_SPEC.md) | Test classes, Decimal gates, tamper suite, benchmark gate | **IMPLEMENTED** |
| 12 | [`12_DECISIONS_AND_OPEN_QUESTIONS.md`](specifications/12_DECISIONS_AND_OPEN_QUESTIONS.md) | The five engineering questions, ADRs, open questions | **RESOLVED** |
| 13 | [`13_ROADMAP_AND_ACCEPTANCE.md`](specifications/13_ROADMAP_AND_ACCEPTANCE.md) | Milestones, dependency graph, release gates | **VERIFIED (M1-M9)** |
| 14 | [`14_EMPLOYMENT_EVIDENCE.md`](specifications/14_EMPLOYMENT_EVIDENCE.md) | Skills-to-artifact mapping | **EVIDENCED** |
| 15 | [`15_RISKS_AND_NON_GOALS.md`](specifications/15_RISKS_AND_NON_GOALS.md) | Risk register with verifiable mitigations; non-goals | **MITIGATED** |
| 16 | [`16_DECISION_REGISTER_AND_RESOLUTIONS.md`](specifications/16_DECISION_REGISTER_AND_RESOLUTIONS.md) | Architecture decision baseline; resolution of open questions | **ADOPTED** |
| 17 | [`17_TRACEABILITY_MATRIX_AND_CONSISTENCY.md`](specifications/17_TRACEABILITY_MATRIX_AND_CONSISTENCY.md) | Requirements-to-verification traceability and test evidence | **VERIFIED** |
| 18 | [`18_M1_IMPLEMENTATION_PLAN.md`](specifications/18_M1_IMPLEMENTATION_PLAN.md) | Baseline implementation plan | **EXECUTED** |

---

## 2. Engineering Verification Reports

| Report | Purpose | Verification Status |
|---|---|---|
| [`SECURITY_REVIEW.md`](SECURITY_REVIEW.md) | Threat modeling, attack surfaces, security baseline, constant-time auth | **VERIFIED** (`tests/integration/test_security_hardening.py`) |
| [`PERFORMANCE_REPORT.md`](PERFORMANCE_REPORT.md) | Empirical scaling benchmarks (1k, 10k, 50k, 100k records) | **VERIFIED** (`benchmarks/benchmark_engine.py`) |
| [`DEPLOYMENT.md`](DEPLOYMENT.md) | Production Docker, PostgreSQL, migrations, backup/restore guide | **VERIFIED** (`Dockerfile`, `docker-compose.yml`) |

---

## 3. Implementation Status Summary

The software implementation is fully built, tested, and validated:
- **Test Suite:** 149 automated tests passing (100% pass rate).
- **Float Gate:** AST scanner confirms zero binary floats on monetary paths.
- **Reproducible Demonstration:** `python -m settleiq.cli run` reproduces all 7 defect classifications deterministically.
- **REST API & Dashboard:** FastAPI static delivery serving the compiled 5-view React/TypeScript SPA at `http://localhost:8000/`.
- **Persistence:** Dual engine support for SQLite and PostgreSQL with versioned transactional migrations.
- **Scale:** 100,000 records reconciled in under 38 seconds with linear $O(N)$ candidate pre-indexing.
