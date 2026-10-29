"""Profile Reconciliation Engine with cProfile and tracemalloc.

Profiles the core reconciliation loop on synthetic workloads to identify
hot paths, memory allocation sites, and execution bottlenecks.
Saves profile metrics into `proof/engine_profile_stats.txt`.
"""

from __future__ import annotations

import cProfile
import io
import pstats
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from benchmarks.benchmark_engine import generate_benchmark_workload  # noqa: E402
from settleiq.engine.reconcile import RunParameters, reconcile  # noqa: E402
from settleiq.validation.ingest import validate_records  # noqa: E402


def run_profile(scale: int = 5000) -> str:
    print(f"Generating profiling workload of {scale:,} records...")
    raw = generate_benchmark_workload(scale)
    validated = validate_records(raw)
    params = RunParameters("2026-10-01", "2026-10-31")

    print("Executing cProfile on reconcile()...")
    profiler = cProfile.Profile()
    profiler.enable()
    result = reconcile(validated.accepted, params)
    profiler.disable()

    stream = io.StringIO()
    ps = pstats.Stats(profiler, stream=stream).sort_stats("cumulative")
    ps.print_stats(35)
    output = stream.getvalue()

    summary_header = (
        f"SETTLEIQ ENGINE PROFILING REPORT (SCALE: {scale:,} records)\n"
        f"Match Rate: {result.metrics.rate * 100:.2f}% | "
        f"Discrepancies: {len(result.discrepancies)}\n"
        f"================================================================================\n"
    )

    full_report = summary_header + output
    out_file = root / "proof" / "engine_profile_stats.txt"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", newline="\n", encoding="utf-8") as f:
        f.write(full_report)
    print(f"Profiling stats saved to {out_file}")
    return full_report


if __name__ == "__main__":
    run_profile()

