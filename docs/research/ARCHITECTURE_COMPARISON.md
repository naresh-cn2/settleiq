# SettleIQ — Architecture Comparison (Batch vs. Event vs. Double-Entry)

**Document ID:** SETTLEIQ-RES-005  
**Status:** ACTIVE  

---

## 1. Architectural Paradigms Compared

| Architectural Paradigm | Primary Use Case | SettleIQ Adoption Decision | Justification |
|:---|:---|:---|:---|
| **Double-Entry General Ledger** (e.g. Modern Treasury, Ledger) | Real-time internal account balances, debit/credit conservation | **Adopted as reference model** | SettleIQ models payouts as balance closures where credits (charges) must balance debits (fees + refunds + net deposit). |
| **Event Sourcing** (e.g. Apache Kafka, Reconcile) | Streaming transaction capture, event replay | **Adopted for Audit Ledger** | Audit journal entries are immutable event streams chaining from a genesis block (`0000...0000`). |
| **Deterministic Batch Observation Windows** (SettleIQ) | Multi-source settlement reconciliation | **Core Architecture** | Using declared observation windows ($\Delta t$) ensures byte-identical reproducibility without ambient wall-clock dependencies. |

---

## 2. In-Memory Algorithmic Efficiency

To scale to 100,000+ records in pure Python without native C++ extensions, SettleIQ discarded naive $O(P \times N)$ iteration in favor of partitioned bucket indexes:

```
Naive Cartesian Scan:
Payouts (P) ────► Loop over All Records (N) ────► O(P x N)  [Crash at 10,000 records]

SettleIQ Linear Partitioning:
All Records ────► Single-Pass Hash Bucket Index ───► records_by_batch[batch_id]
                                                          │
Payouts (P) ────► Direct O(1) Hash Lookup ───────────────► Decompose in O(N) Total
```

