# SettleIQ — Permanent Verifiable Proof Manifest

This directory provides cryptographically verifiable evidence of SettleIQ's implementation completeness, mathematical safety, deterministic reconciliation, and tamper detection.

## Latest Proof Execution Summary

- **Generated At:** `2026-10-29T04:17:04.733883+00:00`
- **Git Commit:** `d2ecf4cfe87bafdb849f87d94cce12fa2d3528ce`
- **Platform:** `Windows 11 (AMD64)`
- **Python Version:** `3.12.10`

| Quality Gate | Requirement | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **G1: Money Safety** | Zero float usage across financial core | AST static gate 100% clean | **PASS** |
| **G2: Deterministic Reconciliation** | Multi-way matching & classification | 157 passing unit & integration tests | **PASS** |
| **G3: Audit Journal** | Tamper detection across middle edits | Payload modification detected (`PAYLOAD_MODIFIED`) | **PASS** |
| **G4: Throughput & Scale** | > 1,000 rec/sec matching throughput | `1,860.2` rec/sec at 10,000 batch | **PASS** |
| **G5: Code Quality** | Zero linter or typing warnings | Ruff checks clean across `src/` and `tests/` | **PASS** |
| **G6: Full-Stack Distribution** | Production SPA served via FastAPI | Verified static bundle (`index.html` + JS/CSS assets) | **PASS** |

## Independent Reproduction Protocol

Any external auditor or engineer can independently re-generate and verify this entire proof bundle by running:

```bash
python scripts/capture_proof.py
```

All raw structured JSON files are archived under `proof/builds/LATEST/`:
- `manifest.json`: Top-level environment and gate audit.
- `gate_results.json`: AST static analysis logs.
- `test_results.json`: Pytest execution logs.
- `journal_verification.json`: Merkle-style hash verification logs.
- `benchmark_results.json`: Scale throughput and peak memory metrics.
