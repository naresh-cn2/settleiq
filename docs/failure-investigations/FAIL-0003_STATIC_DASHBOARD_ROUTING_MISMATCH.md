# Incident Report: FAIL-0003 — Static Dashboard SPA Routing Mismatch

**Date:** 2026-10-28  
**Component:** Web Interface Delivery (`src/settleiq/api/app.py` & React Router)  
**Severity:** MEDIUM (Direct Navigation 404s)  

---

## 1. Symptom & Reproduction

While the React dashboard loaded correctly when entering at the root URL (`http://localhost:8000/`), navigating directly to a deep client-side route (e.g. `http://localhost:8000/runs/run_123` or refreshing the page on `http://localhost:8000/discrepancies`) returned a FastAPI HTTP 404 Not Found error.

---

## 2. Root Cause Analysis

FastAPI's `StaticFiles` was mounted only on root or `/assets`. When a browser directly requests `/runs/run_123`, the request hits the FastAPI server rather than the client-side React Router. Because no backend API endpoint existed for `/runs/{run_id}` (only `/v1/runs/{run_id}`), FastAPI returned HTTP 404 instead of serving `index.html`.

---

## 3. Corrective Action & Verification

1. Configured explicit mount for `/assets` pointing to `STATIC_DIR / "assets"`.
2. Implemented a catch-all SPA fallback route in `src/settleiq/api/app.py`:
   ```python
   @app.get("/{full_path:path}")
   def serve_spa(full_path: str) -> FileResponse:
       if full_path.startswith("v1/") or full_path.startswith("api/") or full_path.startswith("assets/"):
           raise HTTPException(status_code=404, detail="Resource not found")
       index_file = STATIC_DIR / "index.html"
       if index_file.exists():
           return FileResponse(index_file)
       raise HTTPException(status_code=404, detail="Frontend build assets not found")
   ```
3. Added automated regression assertions in `tests/integration/test_acceptance_workflow.py` testing both root `/` and deep client route `/runs/test_run_123`.

