# SettleIQ — Master Documentation & Knowledge Base Index

SettleIQ is an independent payment settlement reconciliation and discrepancy investigation platform, built as a verified, high-performance financial engineering product.

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

## 2. Product Strategy & User Experience

| Document | Purpose |
|---|---|
| [`product/PRODUCT_VISION.md`](product/PRODUCT_VISION.md) | Core mission, 5 architectural tenets, and target outcomes |
| [`product/PRODUCT_REQUIREMENTS.md`](product/PRODUCT_REQUIREMENTS.md) | Formal functional (FR-01…08) and non-functional requirements |
| [`product/USER_PERSONAS.md`](product/USER_PERSONAS.md) | 4 enterprise personas and 60-second guided workflow map |
| [`product/PRODUCT_ACCEPTANCE_CRITERIA.md`](product/PRODUCT_ACCEPTANCE_CRITERIA.md) | Verifiable quality gates (G1 through G6) |

---

## 3. Competitive Intelligence & Research

| Dossier | Description |
|---|---|
| [`research/COMPETITIVE_LANDSCAPE.md`](research/COMPETITIVE_LANDSCAPE.md) | Deep profiles: BlackLine, Modern Treasury, HighRadius, Numeric |
| [`research/COMMERCIAL_PRODUCT_MATRIX.md`](research/COMMERCIAL_PRODUCT_MATRIX.md) | 25-dimension feature matrix comparing SettleIQ against commercial vendors |
| [`research/OPEN_SOURCE_REPOSITORY_AUDIT.md`](research/OPEN_SOURCE_REPOSITORY_AUDIT.md) | Technical teardown of open-source reconciliation tools |
| [`research/FEATURE_GAP_ANALYSIS.md`](research/FEATURE_GAP_ANALYSIS.md) | Five industry gaps and SettleIQ solutions |
| [`research/ARCHITECTURE_COMPARISON.md`](research/ARCHITECTURE_COMPARISON.md) | Architectural comparison of financial ledger designs |
| [`research/RESEARCH_SOURCES.md`](research/RESEARCH_SOURCES.md) | Authoritative citations and financial standards references |

---

## 4. Failure Investigations & Engineering Case Studies

| Document | Subject / Discovery |
|---|---|
| [`failure-investigations/FAILURES_INDEX.md`](failure-investigations/FAILURES_INDEX.md) | Central incident registry |
| [`failure-investigations/FAIL-0001_FAKE_RESOLUTION_MUTATION.md`](failure-investigations/FAIL-0001_FAKE_RESOLUTION_MUTATION.md) | Disconnected route resolution RCA & transactional fix |
| [`failure-investigations/FAIL-0002_QUADRATIC_DECOMPOSITION_BOTTLENECK.md`](failure-investigations/FAIL-0002_QUADRATIC_DECOMPOSITION_BOTTLENECK.md) | $O(P \times N)$ bottleneck RCA & $O(N)$ hash partitioning fix |
| [`failure-investigations/FAIL-0003_STATIC_DASHBOARD_ROUTING_MISMATCH.md`](failure-investigations/FAIL-0003_STATIC_DASHBOARD_ROUTING_MISMATCH.md) | FastAPI static mount vs SPA client routing fix |
| [`case-studies/CASE_STUDY_01_ZERO_FLOAT_FINANCIAL_ENGINEERING.md`](case-studies/CASE_STUDY_01_ZERO_FLOAT_FINANCIAL_ENGINEERING.md) | Eliminating float drift via AST static gate |
| [`case-studies/CASE_STUDY_02_HASH_CHAINED_AUDIT_LEDGER.md`](case-studies/CASE_STUDY_02_HASH_CHAINED_AUDIT_LEDGER.md) | Merkle-style tamper detection for SOX 404 compliance |
| [`case-studies/CASE_STUDY_03_LINEAR_SCALING_100K_WORKLOADS.md`](case-studies/CASE_STUDY_03_LINEAR_SCALING_100K_WORKLOADS.md) | Algorithmic batch partitioning and candidate pruning |

---

## 5. Engineering Verification Reports & Proofs

| Report | Purpose | Verification Status |
|---|---|---|
| [`../proof/PROOF_MANIFEST.md`](../proof/PROOF_MANIFEST.md) | Cryptographic proof-of-work manifest | **VERIFIED** (`scripts/capture_proof.py`) |
| [`SECURITY_REVIEW.md`](SECURITY_REVIEW.md) | Threat modeling, attack surfaces, constant-time auth | **VERIFIED** (`tests/integration/test_security_hardening.py`) |
| [`PERFORMANCE_REPORT.md`](PERFORMANCE_REPORT.md) | Empirical scaling benchmarks (1k, 10k, 50k, 100k records) | **VERIFIED** (`benchmarks/benchmark_engine.py`) |
| [`DEPLOYMENT.md`](DEPLOYMENT.md) | Production Docker, PostgreSQL, backup/restore guide | **VERIFIED** (`Dockerfile`, `docker-compose.yml`) |

---

## 6. Implementation Status Summary

The software implementation is fully built, tested, and validated:
- **Test Suite:** 157 automated tests passing (100% pass rate).
- **Float Gate:** AST scanner confirms zero binary floats on monetary paths.
- **Autonomous AI Investigator:** Deterministic evidence-backed reasoning engine with constituent fund journey tracing.
- **Reproducible Demonstration:** `python -m settleiq.cli run` reproduces all 7 defect classifications deterministically.
- **Interactive Workspace:** 5-view React/TypeScript SPA with 60-second guided tour demo seed served directly by FastAPI.
- **Persistence:** Dual engine support for SQLite and PostgreSQL with versioned transactional migrations.
- **Scale:** 100,000 records reconciled in under 38 seconds with linear $O(N)$ candidate pre-indexing.
