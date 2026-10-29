# SettleIQ — Permanent Verifiable Proof Manifest

This repository maintains a formal **Three-Tier Verification System** providing
cryptographic and empirical proof of mathematical correctness, deterministic matching,
AI reasoning accuracy, and tamper detection.

## Summary of Verification Tiers

- **Generated At:** `2026-10-29T07:14:45.551507+00:00`
- **Git Commit:** `0c1e6deb2fed0367c2dd8e8da902dabc938b6ef1` (`main`)
- **Platform:** `Windows 11 (AMD64)`
- **Python Version:** `3.12.10`

### Tier 1: Execution Evidence (Quality Gates & Compilations)

| Gate | Requirement | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **G1: Money Safety** | Zero binary float usage | AST static gate clean (0 violations) | **PASS** |
| **G2: Test Suite** | 100% test pass rate | 178 passing tests | **PASS** |
| **G3: Code Quality** | Zero static lint warnings | Clean ruff static check | **PASS** |
| **G4: Engine Throughput** | > 1,000 records/sec | 604.0 rec/s (10k batch) | **PASS** |
| **G5: Frontend SPA** | Production web assets | Verified index.html + hashed assets | **PASS** |

### Tier 2: Acceptance Evidence (Domain Correctness & Behavior)

| Verification Area | Requirement | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **AI Forensic Investigator** | Ground-truth benchmark | 30/30 Cases (100% Top-1 Accuracy) | **PASS** |
| **Audit Journal Integrity** | Tamper detection | Bit modification detected & rejected | **PASS** |
| **End-to-End Workflow** | 8-step journey | 8/8 HTTP 200/201 Success | **PASS** |
| **Financial Adversarial** | Multi-currency & $100B balances | JPY, BHD, $100B, Net-zero 100% closed | **PASS** |
| **Browser-Level UI** | 5-view workflow snapshots | 4 Standalone HTML views in `proof/ui/` | **PASS** |

### Tier 3: Independent Verification (Auditor Reproducibility)

#### Artifact Checksums (`proof/builds/LATEST/`)

| Artifact File | SHA-256 Digest |
| :--- | :--- |
| `tier1_execution_evidence.json` | `b8aa291fa5b13773e38b9ed6ed0e689384d57f2db3492deebc40cad985e7b21a` |
| `tier2_acceptance_evidence.json` | `2af6d1af517dba9b43f248d777173f4b0bcf3324473c644fdd28e8260a6b83e5` |
| `tier3_independent_verification.json` | `3f230c43cda3b5e2aa99588849fb17ea0ce630b67cd91097321a806c80136803` |
| `gate_results.json` | `555f464a7f386aedca05014134870af4ab73a900ceefb420ea150b5f809a2137` |
| `test_results.json` | `a1dd94bdd0f1146b49698b6bd37830ed76464ae636b0f21863a7c05b814164ea` |
| `journal_verification.json` | `2c052763909505ea53f73231df8abe45c8538c375c29a00253ba31520359d3b2` |
| `investigator_evaluation.json` | `338e0af5998328bea0cad99189453e1ce8352558ed194ce34b7338b47ab70a84` |
| `benchmark_results.json` | `ed503778aac4d540b3a92fb8388fc3c430f42f2dd7af39e1e3af98e42e6ff1ea` |
| `demo_journey_trace.json` | `3b969993a63646de29629c8aed2eac4d09a274b1f4997d6c45734e481b9d2cf6` |

#### Exact Reproduction Protocol

Any external auditor or engineer can independently reproduce this entire proof package:

```bash
# 1. Verify Money Safety AST Gate
python -m settleiq.cli gate

# 2. Run Pytest Suite
pytest -v

# 3. Run E2E Demonstration Journey
python scripts/verify_demo_journey.py

# 4. Generate UI Acceptance Snapshots
python scripts/verify_ui_workflow.py

# 5. Execute Complete Proof Pipeline
python scripts/capture_proof.py
```
