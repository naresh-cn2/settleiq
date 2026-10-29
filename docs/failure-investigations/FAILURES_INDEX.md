# SettleIQ — Failure Intelligence Register

**Document ID:** SETTLEIQ-FAIL-INDEX  
**Status:** ACTIVE  

This register documents genuine technical failures, architectural defects, and performance bottlenecks encountered during the engineering of SettleIQ, including reproduction, root-cause analysis, corrective transactions, and automated regression tests.

---

## Failure Register

| Failure ID | Component | Symptom | Root Cause | Resolution | Regression Test |
|:---|:---|:---|:---|:---|:---|
| **FAIL-0001** | REST API & Store | Resolution endpoint returned HTTP 200 without persisting resolution to DB or journal | Missing database update statement and uncalled journal append in handler | Implemented `store.resolve_discrepancy()` in single `BEGIN IMMEDIATE` transaction updating `discrepancy.status` and appending audit event | `tests/integration/test_api.py::test_resolve_discrepancy` |
| **FAIL-0002** | Reconciliation Engine | Benchmark timeout / crash at 10,000 records | $O(P \times N)$ unindexed decomposition passing all records to every payout, plus $O(P \times D)$ Cartesian rule loops | Pre-indexed records by batch hash bucket in single pass ($O(N)$) and pruned candidate pools by reference/amount | `benchmarks/benchmark_engine.py` (100k in 37.49s) |
| **FAIL-0003** | Dashboard Delivery | Direct browser navigation to `/runs/...` returned HTTP 404 | FastAPI static files mounted only on `/`, client-side React routes unhandled by backend | Added SPA fallback route `/{full_path:path}` serving `index.html` while preserving API 404s | `tests/integration/test_acceptance_workflow.py` (Step 2) |

