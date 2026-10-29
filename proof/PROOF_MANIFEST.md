# SettleIQ — Permanent Verifiable Proof Manifest

This repository maintains a formal **Three-Tier Verification System** providing
cryptographic and empirical proof of mathematical correctness, deterministic matching,
AI reasoning accuracy, and tamper detection.

## Summary of Verification Tiers

- **Generated At:** `2026-10-29T14:06:31.449548+00:00`
- **Git Commit:** `5a313d1503907295ea2b649cf67ecc0b29a8db90` (`main`)
- **Platform:** `Windows 11 (AMD64)`
- **Python Version:** `3.12.10`

### Tier 1: Execution Evidence (Quality Gates & Compilations)

| Gate | Requirement | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **G1: Money Safety** | Zero binary float usage | AST static gate clean (0 violations) | **PASS** |
| **G2: Test Suite** | 100% test pass rate | 204 passing tests | **PASS** |
| **G3: Code Quality** | Zero static lint warnings | Clean ruff static check | **PASS** |
| **G4: Engine Throughput** | > 1,000 records/sec | 1,485.2 rec/s (10k batch) | **PASS** |
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
| `tier1_execution_evidence.json` | `5e1d4026d76abc0b6ea9282acba5df1bf59ed1ab1491232d2beb930e23a54ed8` |
| `tier2_acceptance_evidence.json` | `0a4d8d243608c3b2efccdc27c6d93c8dd8310dc013c49cd78462b3cd21394c22` |
| `tier3_independent_verification.json` | `740c32f8deb5b4d3d07534ee5e23b870b03cf2d449670b468e598ad4ffb1f6de` |
| `gate_results.json` | `555f464a7f386aedca05014134870af4ab73a900ceefb420ea150b5f809a2137` |
| `test_results.json` | `142713a7e83f60cff763ecfa8b7212c7a0e86ab0546f46ea52c9633557ce03e7` |
| `journal_verification.json` | `2c052763909505ea53f73231df8abe45c8538c375c29a00253ba31520359d3b2` |
| `investigator_evaluation.json` | `e8be483746c352ba17b52ab62a3a4bc906fc6608d1fdd969308d510976f68f29` |
| `investigator_independent_validation.json` | `daf5977f89ad4d95715d2e2350338393d17ffca02878797c7c4e717c20512bcf` |
| `benchmark_results.json` | `65f056b5f5cee5059675c47ddf72f3feaa6a3076dc219074ce84fad2b3eaf45e` |
| `demo_journey_trace.json` | `c33ee1007546fc0d0a4fdf379cae5205dcc75a5b97fe0a069e77aee77f610891` |

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
