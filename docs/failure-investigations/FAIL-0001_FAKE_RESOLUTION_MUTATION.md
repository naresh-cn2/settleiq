# Incident Report: FAIL-0001 — Fake Discrepancy Resolution Mutation

**Date:** 2026-10-28  
**Component:** REST API (`src/settleiq/api/app.py`) & Store (`src/settleiq/persistence/store.py`)  
**Severity:** CRITICAL (Silent State Mutation Loss)  

---

## 1. Symptom & Reproduction

When an investigator invoked `POST /v1/discrepancies/{id}/resolve` through the web dashboard, the API responded with HTTP 200:
```json
{
  "discrepancy_id": "dsc:AMOUNT_BREAK:po_2",
  "status": "resolved",
  "appended": true
}
```
However, upon refreshing the dashboard or querying the database directly:
- `SELECT status FROM discrepancy WHERE discrepancy_id = 'dsc:AMOUNT_BREAK:po_2'` returned `'OPEN'`.
- `SELECT COUNT(*) FROM discrepancy_resolution` returned `0`.
- The audit journal contained no event for the resolution.

The user interface displayed success, but the underlying financial state was completely unmutated.

---

## 2. Root Cause Analysis

1. **Disconnected Route Handler:** In `app.py`, the endpoint handler returned a hardcoded success dictionary without invoking a store method.
2. **Missing Database Table:** The SQLite schema lacked a `discrepancy_resolution` table to persist who resolved the break, at what timestamp, and with what business justification.
3. **Audit Ledger Bypass:** The resolution logic never instantiated a `Journal` instance to append an immutable event.

---

## 3. Corrective Action & Verification

1. Added `discrepancy_resolution` table to `SCHEMA_STATEMENTS` in `src/settleiq/persistence/store.py`:
   ```sql
   CREATE TABLE IF NOT EXISTS discrepancy_resolution (
       resolution_id     TEXT PRIMARY KEY,
       discrepancy_id    TEXT NOT NULL REFERENCES discrepancy(discrepancy_id),
       run_id            TEXT NOT NULL,
       status            TEXT NOT NULL,
       reason            TEXT NOT NULL,
       selected_candidate TEXT,
       resolved_by       TEXT NOT NULL,
       resolved_at       TEXT NOT NULL
   );
   ```
2. Implemented `store.resolve_discrepancy()` to execute atomically inside a `BEGIN IMMEDIATE` transaction:
   - Updates `discrepancy.status = 'RESOLVED'`
   - Inserts record into `discrepancy_resolution`
   - Calls `journal.append_within(connection, cursor, event_payload)`
   - Commits transaction atomically.
3. Added regression integration tests verifying that `find_discrepancy()` reflects `RESOLVED`, `discrepancy_resolution` has the record, and `journal_entry` contains `DiscrepancyResolved`.

