# Root-Cause Analysis: Batch-Level Constituent-Mapping Defect in SettleIQ

> **Publication date:** November 10, 2026  
> **Production URL:** https://settleiq-zeta.vercel.app  
> **Repository:** github.com/naresh-cn2/settleiq  
> **Data note:** All examples use synthetic financial data only. No real customer information is used.

## Summary

A defect in SettleIQ's payout decomposition logic caused payouts sharing the same settlement batch to cross-contaminate each other's constituents. When two payouts were in the same batch (e.g., `BATCH-001`), each payout claimed **all** charge and fee records from that batch as its constituents, rather than only the records matching its own settlement reference. This produced incorrect NET_GROSS_BREAK discrepancies for correctly-paid payouts and masked genuine short payments.

## The Bug

### Before the Fix

The `decompose()` function in `src/settleiq/engine/decompose.py` filtered constituents by batch only:

```python
if _batch(record) != batch:
    continue
```

When payout `pay-001` (BATCH-001, REF-001, $90) and payout `pay-002` (BATCH-001, REF-002, $150) shared batch `BATCH-001`:

| Payout | Expected Constituents | Actual Constituents (Bug) | Result |
|--------|----------------------|---------------------------|--------|
| pay-001 | chg-001 ($100), fee-001 ($10) | chg-001, fee-001, chg-002, fee-002 | Net expected $270, paid $90 → NET_GROSS_BREAK |
| pay-002 | chg-002 ($200), fee-002 ($20) | chg-001, fee-001, chg-002, fee-002 | Net expected $270, paid $150 → NET_GROSS_BREAK |

Both payouts were incorrectly flagged as NET_GROSS_BREAK because each saw the other payout's records.

### After the Fix

Added reference-level filtering when a payout carries a settlement reference:

```python
payout_reference = str(payout.get("reference", ""))
...
if payout_reference and str(record.get("reference", "")) != payout_reference:
    continue
```

| Payout | Expected Constituents | Actual Constituents (Fixed) | Result |
|--------|----------------------|----------------------------|--------|
| pay-001 | chg-001 ($100), fee-001 ($10) | chg-001, fee-001 | Net expected $90, paid $90 → closes exactly |
| pay-002 | chg-002 ($200), fee-002 ($20) | chg-002, fee-002 | Net expected $180, paid $150 → $30 short (NET_GROSS_BREAK) |

## Three-Record Test Case

| Reference | Charge | Fee | Expected Net | Payout Paid | Discrepancy |
|-----------|--------|-----|--------------|-------------|-------------|
| REF-001 | $100.00 | $10.00 | $90.00 | $90.00 | None (closes exactly) |
| REF-002 | $200.00 | $20.00 | $180.00 | $150.00 | NET_GROSS_BREAK, $30.00 short, HIGH |
| REF-003 | $300.00 | $30.00 | $330.00 | $0.00 (missing) | PHANTOM_PROCESSOR for chg-003 and fee-003, HIGH |

## Why Batch-Only Matching Is Insufficient

In financial reconciliation, a batch is a **processing grouping**, not a **settlement grouping**. Multiple settlement references can share a batch. Matching by batch alone conflates distinct settlements:

1. **False positives:** Correctly-paid payouts appear to have breaks because they "see" other payouts' constituents
2. **False negatives:** Genuine breaks can be masked when offsetting errors from different references cancel out
3. **Incorrect constituent mapping:** Discrepancies point to the wrong source records, making investigation impossible

## Fix Location

**File:** `src/settleiq/engine/decompose.py`  
**Lines:** 130-150

The fix adds a reference guard after the batch check:

```python
# When a payout carries a settlement reference, only constituents whose
# reference matches may be part of its composition. This prevents a payout
# from claiming charge/fee records from a different settlement reference
# that merely happens to share the same batch.
payout_reference = str(payout.get("reference", ""))
...
if payout_reference and str(record.get("reference", "")) != payout_reference:
    continue
```

## Backward Compatibility

If a payout carries no settlement reference (`reference` is empty or missing), the fix falls back to batch-only matching, preserving existing behavior for reference-less records.

## Verification

- **Local tests:** 5/5 regression tests pass
- **Full suite:** 213 tests pass (205 passed, 8 skipped PostgreSQL)
- **Production deployment:** Commit `4fe20b4` on GitHub `main` branch; deployed to production at https://settleiq-zeta.vercel.app
- **All examples use synthetic data only** — no real customer financial information
