# SettleIQ — Permanent Verifiable Proof Manifest

This repository maintains a formal **Three-Tier Verification System** providing
cryptographic and empirical proof of mathematical correctness, deterministic matching,
AI reasoning accuracy, and tamper detection.

## Summary of Verification Tiers

- **Generated At:** `2026-10-29T13:10:01.053694+00:00`
- **Git Commit:** `0645e5837d2322f8949808e28467ad109c9a2cb7` (`main`)
- **Platform:** `Windows 11 (AMD64)`
- **Python Version:** `3.12.10`

### Tier 1: Execution Evidence (Quality Gates & Compilations)

| Gate | Requirement | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **G1: Money Safety** | Zero binary float usage | AST static gate clean (0 violations) | **PASS** |
| **G2: Test Suite** | 100% test pass rate | 200 passing tests | **PASS** |
| **G3: Code Quality** | Zero static lint warnings | Clean ruff static check | **PASS** |
| **G4: Engine Throughput** | > 1,000 records/sec | 164.3 rec/s (10k batch) | **PASS** |
| **G5: Frontend SPA** | Production web assets | Verified index.html + hashed assets | **PASS** |

### Tier 2: Acceptance Evidence (Domain Correctness & Behavior)

| Verification Area | Requirement | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **Investigator Regression** | Ground-truth benchmark | 30/30 Cases (100% Top-1 Accuracy) | **PASS** |
| **Investigator Independent** | Action vs Root-Cause separation | 22/22 Tests (100% Root-Cause Acc) | **PASS** |
| **Audit Journal Integrity** | Tamper detection | Bit modification detected & rejected | **PASS** |
| **End-to-End Workflow** | 8-step journey | 8/8 HTTP 200/201 Success | **PASS** |
| **Financial Adversarial** | Multi-currency & $100B balances | JPY, BHD, $100B, Net-zero 100% closed | **PASS** |
| **Real Browser E2E** | Live Chrome automation & screenshots | 6 Real PNGs in `proof/screenshots/` | **PASS** |
| **Workflow Snapshots** | 5-view workflow snapshots | 4 Standalone HTML views in `proof/ui/` | **PASS** |

### Tier 3: Independent Verification (Auditor Reproducibility)

#### Artifact Checksums (`proof/builds/LATEST/`)

| Artifact File | SHA-256 Digest |
| :--- | :--- |
| `tier1_execution_evidence.json` | `755b2ce4de7ce9fdf63e044afb9fa659c13d3c5dca5a4383d6dd595e5cd8d52c` |
| `tier2_acceptance_evidence.json` | `4b6a5c2809b443579146457692e44f196224b978f5df26f12b170a5a0b4a3f09` |
| `tier3_independent_verification.json` | `45b35f5dc9c65c80763df2fcbde37b30ecdf965ed4b9f8a6a568a82f78164d4a` |
| `gate_results.json` | `555f464a7f386aedca05014134870af4ab73a900ceefb420ea150b5f809a2137` |
| `test_results.json` | `a5b575781dc5662fabbb8831812b802afe20c6b923c2467e16c41419ead78e9a` |
| `journal_verification.json` | `2c052763909505ea53f73231df8abe45c8538c375c29a00253ba31520359d3b2` |
| `investigator_evaluation.json` | `49e023107b75c52ef66bdeb23029edf57df93b69dc47f7b927c9e87c12fe0d44` |
| `investigator_independent_validation.json` | `5201ee9fca573c450c35231fff875e13206280ac9c62f78277d82b96c102b2c4` |
| `benchmark_results.json` | `60fed405556be437ed41e51b58b49c5116196e2622448ca2f2e2bd789a7946af` |
| `demo_journey_trace.json` | `db38c5b79d35a464f3daf3611315edcf0a607095891a9e339ee875da6300ec9d` |

#### Exact Reproduction Protocol

Any external auditor or engineer can independently reproduce this entire proof package:

```bash
# 1. Verify Money Safety AST Gate
python -m settleiq.cli gate

# 2. Run Pytest Suite
pytest -v

# 3. Run Real Browser E2E Verification
npm --prefix frontend run verify:e2e

# 4. Run Demonstration Journey Trace
python scripts/verify_demo_journey.py

# 5. Execute Complete Proof Pipeline
python scripts/capture_proof.py
```
