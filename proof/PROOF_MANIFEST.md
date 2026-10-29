# SettleIQ — Permanent Verifiable Proof Manifest

This directory provides cryptographically verifiable evidence of SettleIQ's
implementation completeness, mathematical safety, deterministic reconciliation,
and tamper detection.

## Latest Proof Execution Summary

- **Generated At:** `2026-10-29T06:39:04.982837+00:00`
- **Git Commit:** `6c1bc549a95a75e0783e39d49d9bfd69d0826563` (`main`)
- **Platform:** `Windows 11 (AMD64)`
- **Python Version:** `3.12.10`

| Quality Gate | Requirement | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **G1: Money Safety** | Zero float usage | AST static gate clean | **PASS** |
| **G2: Reconciliation** | Multi-way matching | 170 passing tests | **PASS** |
| **G3: Audit Journal** | Tamper detection | Payload mutation detected | **PASS** |
| **G4: AI Investigator** | Ground-truth ranking | 100% Top-1 Accuracy | **PASS** |
| **G5: Throughput** | > 1k rec/s | 1,493.7 rec/s (10k batch) | **PASS** |
| **G6: Code Quality** | Zero warnings | Clean ruff static analysis | **PASS** |
| **G7: Full-Stack SPA** | Production bundle | Verified static bundle | **PASS** |
| **G8: E2E Demonstration** | Complete 8-step flow | 8/8 Steps Succeeded | **PASS** |

## Cryptographic Artifact Checksums (`proof/builds/LATEST/`)

| Artifact | SHA-256 Digest |
| :--- | :--- |
| `gate_results.json` | `555f464a7f386aedca05014134870af4ab73a900ceefb420ea150b5f809a2137` |
| `test_results.json` | `2d5638c8f81ad75e13e3e944b3d6d60be0907416b4b728cc310d8b8d84b07ef3` |
| `investigator_evaluation.json` | `8b7f54abf1e02c2699e4db64ef876a97587d8452e9250fe5ac689d2fb90844b9` |
| `journal_verification.json` | `2c052763909505ea53f73231df8abe45c8538c375c29a00253ba31520359d3b2` |
| `benchmark_results.json` | `2673b01fa9aee6186042807f1cfe6301237feeac6e2464bdc2ef318beaf78830` |
| `demo_journey_trace.json` | `c3848c53e7a2c64a533e23dc45484d156b13c35438eff5b9b7c48f12ec5ad7dc` |

## Independent Reproduction Protocol

Any external auditor or engineer can independently re-verify this bundle:

```bash
python scripts/capture_proof.py
```
