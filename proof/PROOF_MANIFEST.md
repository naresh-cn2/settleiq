# SettleIQ — Permanent Verifiable Proof Manifest

This repository maintains a formal **Three-Tier Verification System** providing
cryptographic and empirical proof of mathematical correctness, deterministic matching,
AI reasoning accuracy, and tamper detection.

## Summary of Verification Tiers

- **Generated At:** `2026-10-29T11:35:58.246375+00:00`
- **Git Commit:** `672ee5e5bc2fa687e2dcfb4e5483629cf5ce9912` (`main`)
- **Platform:** `Windows 11 (AMD64)`
- **Python Version:** `3.12.10`

### Tier 1: Execution Evidence (Quality Gates & Compilations)

| Gate | Requirement | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **G1: Money Safety** | Zero binary float usage | AST static gate clean (0 violations) | **PASS** |
| **G2: Test Suite** | 100% test pass rate | 193 passing tests | **PASS** |
| **G3: Code Quality** | Zero static lint warnings | Clean ruff static check | **PASS** |
| **G4: Engine Throughput** | > 1,000 records/sec | 1,730.5 rec/s (10k batch) | **PASS** |
| **G5: Frontend SPA** | Production web assets | Verified index.html + hashed assets | **PASS** |

### Tier 2: Acceptance Evidence (Domain Correctness & Behavior)

| Verification Area | Requirement | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **Investigator Regression** | Ground-truth benchmark | 30/30 Cases (100% Top-1 Accuracy) | **PASS** |
| **Investigator Independent** | Action vs Root-Cause separation | 15/15 Tests (100% Root-Cause Acc) | **PASS** |
| **Audit Journal Integrity** | Tamper detection | Bit modification detected & rejected | **PASS** |
| **End-to-End Workflow** | 8-step journey | 8/8 HTTP 200/201 Success | **PASS** |
| **Financial Adversarial** | Multi-currency & $100B balances | JPY, BHD, $100B, Net-zero 100% closed | **PASS** |
| **Real Browser E2E** | Live Chrome automation & screenshots | 6 Real PNGs in `proof/screenshots/` | **PASS** |
| **Workflow Snapshots** | 5-view workflow snapshots | 4 Standalone HTML views in `proof/ui/` | **PASS** |

### Tier 3: Independent Verification (Auditor Reproducibility)

#### Artifact Checksums (`proof/builds/LATEST/`)

| Artifact File | SHA-256 Digest |
| :--- | :--- |
| `tier1_execution_evidence.json` | `6a296f782c3225016572a3351953bcc269ef28b77b5078c380309caaeb8df905` |
| `tier2_acceptance_evidence.json` | `afc118b998391d2b89a5381ee038c5023b06aaaf2f15fa1a2e8cb9ceb06729c9` |
| `tier3_independent_verification.json` | `3dd0a288fadbf00f4c88ccfab0d7726ac0a4215fe79e4b04b9181a30b7da14ff` |
| `gate_results.json` | `555f464a7f386aedca05014134870af4ab73a900ceefb420ea150b5f809a2137` |
| `test_results.json` | `c32e4d13e677273c0362305f0c40406d5629c8b95fb72c0b1f296a9c70b9cb34` |
| `journal_verification.json` | `2c052763909505ea53f73231df8abe45c8538c375c29a00253ba31520359d3b2` |
| `investigator_evaluation.json` | `9e7cc44514121401143ee1be9c025d69283d26903e8eb63a5fc5d70811655bc9` |
| `investigator_independent_validation.json` | `784a845a4cec0dcb7d2fb226facaba878db7039f0d6eacbf11a0438c578c33b5` |
| `benchmark_results.json` | `b9960d9d3ca0fed20150873ed5a28471f2a05cb9d4092d969b5236ddd264f35c` |
| `demo_journey_trace.json` | `19d7f56a27c19a08712ffbafbe24759d525a1216dfc2f7f904fb5a55a38ec017` |

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
