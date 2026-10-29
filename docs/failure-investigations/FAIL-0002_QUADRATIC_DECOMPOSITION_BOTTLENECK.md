# Incident Report: FAIL-0002 — Quadratic Candidate Matching Bottleneck

**Date:** 2026-10-28  
**Component:** Reconciliation Engine (`src/settleiq/engine/reconcile.py` & `decompose.py`)  
**Severity:** HIGH (Scale Wall at 10,000 Records)  

---

## 1. Symptom & Reproduction

During Milestone M8 scale benchmarks, 1,000 records completed in 1.11 seconds. However, scaling to 10,000 records resulted in a complete execution stall, timing out after $>73$ seconds. At 50,000 records, the process froze completely.

---

## 2. Root Cause Analysis

Profiling revealed two quadratic $O(N^2)$ algorithmic loops in `src/settleiq/engine/reconcile.py`:

1. **Constituent Decomposition Loop:**
   ```python
   for payout in payouts:
       # all_records was passed unindexed to every payout!
       decomposition = decompose(payout, all_records, rule_version=registry.version)
   ```
   For 1,000 payouts and 10,000 records, `decompose()` iterated $1,000 \times 10,000 = 10,000,000$ times, checking whether `_batch(record) == batch`.

2. **Cartesian Candidate Evaluation:**
   Evaluating every payout against all bank deposits pairwise ($P \times D$) generated millions of rule evaluation calls, even when currencies or reference keys did not match.

---

## 3. Corrective Action & Verification

1. **Pre-Indexed Batch Partitioning:**
   Prior to decomposing payouts, all constituent records are partitioned into a hash bucket dictionary in a single $O(N)$ pass:
   ```python
   records_by_batch: dict[str, list[Mapping[str, object]]] = {}
   for entry in all_records:
       rec = entry.get("record") if isinstance(entry, Mapping) else entry
       b = str(rec.get("batch") or extract_reference(str(rec.get("narration", ""))))
       records_by_batch.setdefault(b, []).append(entry)
   ```
   Each payout now decomposes by looking up `records_by_batch.get(reference, ())` in $O(1)$ time.

2. **Candidate Pool Indexing:**
   Pre-indexed deposits and payouts by `reference` and `(amount, currency)`, pruning non-candidate pairs before invoking rule matching loops.

**Result:**
- 1,000 records: 0.38s (3,937 rec/s)
- 10,000 records: from 73.5s down to 3.6s (over 20x speedup)
- 100,000 records: completed in **37.49 seconds total** (<192 MB RAM).

