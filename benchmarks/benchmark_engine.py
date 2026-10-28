"""SettleIQ Performance and Scale Benchmark Suite.

Executes empirical benchmarks across 1,000, 10,000, 50,000, and 100,000 financial record
workloads to measure:
- Ingestion validation throughput (records/sec)
- Reconciliation matching engine throughput (records/sec)
- Peak memory consumption (tracemalloc)
- Discrepancy classification distributions
- Algorithmic scaling characteristics
"""

from __future__ import annotations

import argparse
import gc
import json
import platform
import sys
import time
import tracemalloc
from decimal import Decimal
from typing import Any

from settleiq.engine.reconcile import RunParameters, reconcile
from settleiq.validation.ingest import validate_records


def generate_benchmark_workload(count: int) -> list[tuple[str, dict[str, object]]]:
    """Generate a representative synthetic dataset with realistic distributions."""
    records: list[tuple[str, dict[str, object]]] = []
    # 1 payout + 1 deposit per 9 charges = 11 records per batch
    batch_count = max(1, count // 11 + 1)

    for b in range(batch_count):
        batch_id = f"bm_sb_{b}"
        batch_charges = 9
        net_amount = Decimal("0.00")

        for c in range(batch_charges):
            cid = f"bm_ch_{b}_{c}"
            amt_cents = 1000 + ((b * 17 + c * 31) % 8900)
            amt = Decimal(amt_cents) / Decimal(100)
            net_amount += amt
            records.append(
                (
                    "charge",
                    {
                        "id": cid,
                        "amount": f"{amt:.2f}",
                        "currency": "USD",
                        "created": "2026-10-15",
                        "batch": batch_id,
                        "reference": f"ref_{b}_{c}",
                    },
                )
            )

        # 1 payout for the batch
        payout_id = f"bm_po_{b}"
        records.append(
            (
                "payout",
                {
                    "id": payout_id,
                    "amount": f"{net_amount:.2f}",
                    "currency": "USD",
                    "arrival_date": "2026-10-17",
                    "batch": batch_id,
                    "payout_reference": f"ref_po_{b}",
                },
            )
        )

        # 1 bank deposit matching the payout
        records.append(
            (
                "deposit",
                {
                    "id": f"bm_bd_{b}",
                    "amount": f"{net_amount:.2f}",
                    "currency": "USD",
                    "posted": "2026-10-18",
                    "narration": f"STRIPE PAYOUT {batch_id}",
                },
            )
        )

        if len(records) >= count:
            break

    # Trim to exact count
    return records[:count]


def benchmark_scale(count: int) -> dict[str, Any]:
    print(f"Generating workload of {count:,} records...", flush=True)
    raw_records = generate_benchmark_workload(count)

    gc.collect()
    tracemalloc.start()
    t0 = time.perf_counter()

    # Step 1: Ingestion & Validation
    t_val_start = time.perf_counter()
    validated = validate_records(raw_records)
    t_val_end = time.perf_counter()

    val_duration = t_val_end - t_val_start
    val_throughput = count / val_duration if val_duration > 0 else 0

    # Step 2: Reconciliation Matching Engine
    t_rec_start = time.perf_counter()
    result = reconcile(validated.accepted, RunParameters("2026-10-01", "2026-10-31"))
    t_rec_end = time.perf_counter()

    rec_duration = t_rec_end - t_rec_start
    rec_throughput = count / rec_duration if rec_duration > 0 else 0

    total_duration = time.perf_counter() - t0
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak_bytes / (1024 * 1024)

    return {
        "record_count": count,
        "total_duration_secs": round(total_duration, 4),
        "validation_duration_secs": round(val_duration, 4),
        "validation_throughput_rec_per_sec": round(val_throughput, 1),
        "reconciliation_duration_secs": round(rec_duration, 4),
        "reconciliation_throughput_rec_per_sec": round(rec_throughput, 1),
        "peak_memory_mb": round(peak_mb, 2),
        "matched_numerator": result.metrics.numerator,
        "eligible_denominator": result.metrics.denominator,
        "auto_match_rate": result.metrics.rate,
        "discrepancy_count": len(result.discrepancies),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="SettleIQ Engine Benchmark")
    parser.add_argument("--scales", nargs="+", type=int, default=[1000, 10000, 50000, 100000])
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args()

    results: list[dict[str, Any]] = []

    print("================================================================================")
    print("SETTLEIQ PERFORMANCE & SCALE BENCHMARK")
    print(f"Platform: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Python: {sys.version.split()[0]} | Decimal Context: 34 digits IEEE 754")
    print("================================================================================")

    for scale in args.scales:
        res = benchmark_scale(scale)
        results.append(res)
        print(
            f"Scale {scale:>7,}: Total={res['total_duration_secs']:>6.2f}s | "
            f"Match={res['reconciliation_throughput_rec_per_sec']:>8,.1f} rec/s | "
            f"Peak Mem={res['peak_memory_mb']:>6.2f} MB"
        )

    print("================================================================================")
    if args.json:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
