"""Controlled multi-repetition benchmark isolating cold-start from warm-run state."""

from __future__ import annotations

import gc
import statistics
import time

from benchmarks.benchmark_engine import generate_benchmark_workload
from settleiq.engine.reconcile import RunParameters, reconcile
from settleiq.validation.ingest import validate_records


def run_controlled_benchmark(scale: int = 5000, repetitions: int = 10) -> dict[str, object]:
    raw_e2e_durations: list[float] = []
    raw_matching_durations: list[float] = []
    digest_matches: list[bool] = []

    first_digest: str | None = None
    params = RunParameters("2026-10-01", "2026-10-31")

    for _rep in range(repetitions):
        gc.collect()
        t0 = time.perf_counter()

        # Step 1: Workload generation and Ingestion
        workload = generate_benchmark_workload(scale)
        validated = validate_records(workload)
        t_ingest = time.perf_counter()

        # Step 2: Core Matching Engine
        result = reconcile(validated.accepted, params)
        t_end = time.perf_counter()

        matching_time = t_end - t_ingest
        e2e_time = t_end - t0

        raw_matching_durations.append(matching_time)
        raw_e2e_durations.append(e2e_time)

        # Verify digest invariance
        current_digest = result.identity.run_id
        if first_digest is None:
            first_digest = current_digest
            digest_matches.append(True)
        else:
            digest_matches.append(current_digest == first_digest)

    # Separate Cold Start (Trial 1) from Warm State (Trials 2-10)
    cold_e2e = raw_e2e_durations[0]
    cold_matching = raw_matching_durations[0]

    warm_e2e = raw_e2e_durations[1:]
    warm_matching = raw_matching_durations[1:]

    def stats(data: list[float]) -> dict[str, float]:
        sorted_d = sorted(data)
        return {
            "mean": statistics.mean(data),
            "median": statistics.median(data),
            "stddev": statistics.stdev(data) if len(data) > 1 else 0.0,
            "min": sorted_d[0],
            "max": sorted_d[-1],
            "spread_range": sorted_d[-1] - sorted_d[0],
        }

    summary = {
        "scale_records": scale,
        "repetitions": repetitions,
        "all_digests_identical": all(digest_matches),
        "raw_matching_durations": [round(d, 4) for d in raw_matching_durations],
        "raw_e2e_durations": [round(d, 4) for d in raw_e2e_durations],
        "cold_start": {
            "e2e_seconds": round(cold_e2e, 4),
            "matching_seconds": round(cold_matching, 4),
            "matching_throughput_rec_sec": round(scale / cold_matching, 1),
        },
        "warm_matching_stats": {k: round(v, 4) for k, v in stats(warm_matching).items()},
        "warm_matching_throughput_stats": {
            "mean_rec_sec": round(scale / stats(warm_matching)["mean"], 1),
            "median_rec_sec": round(scale / stats(warm_matching)["median"], 1),
            "min_rec_sec": round(scale / stats(warm_matching)["max"], 1),
            "max_rec_sec": round(scale / stats(warm_matching)["min"], 1),
        },
        "warm_e2e_stats": {k: round(v, 4) for k, v in stats(warm_e2e).items()},
    }
    return summary


if __name__ == "__main__":
    import json
    res = run_controlled_benchmark(scale=5000, repetitions=10)
    print(json.dumps(res, indent=2))
