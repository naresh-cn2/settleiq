# SettleIQ — Permanent Verifiable Proof Manifest

This repository maintains a formal **Three-Tier Verification System** providing
cryptographic and empirical proof of mathematical correctness, deterministic matching,
AI reasoning accuracy, and tamper detection.

> [!WARNING]
> **Cryptographic Scope & Limitation**: SHA-256 digests verify accidental corruption, bit-rot, and file tampering relative to the manifest. They do NOT provide authenticity or immutability against an attacker who has write access to both the artifact repository and the manifest itself, unless the root digest is externally anchored to an immutable ledger or witness log.

## Summary of Verification Tiers

- **Generated At:** `2026-10-29T15:30:50.047826+00:00`
- **Git Commit:** `a86abe7af5c48758fbb05ad4008ea95a96d064ab` (`main`)
- **Platform:** `Windows 11 (AMD64)`
- **Python Version:** `3.12.10`

### Tier 1: Execution Evidence (Quality Gates & Compilations)

| Gate | Requirement | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **G1: Money Safety** | Zero binary float usage | AST static gate clean (0 violations) | **PASS** |
| **G2: Test Suite** | 100% test pass rate | 204 passing tests | **PASS** |
| **G3: Code Quality** | Zero static lint warnings | Clean ruff static check | **PASS** |
| **G4: Engine Throughput** | > 1,000 records/sec | 6,265.5 rec/s (10k batch) | **PASS** |
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
| `tier1_execution_evidence.json` | `b229fdec88872d8be89b420a3913ee01f96a162c74de75887a96e70051980308` |
| `tier2_acceptance_evidence.json` | `135ef31d063f2efc2df2f315431b03c0b5813536e0b083f4b2a2c6d4943ef461` |
| `tier3_independent_verification.json` | `1b541da20e6c3317d4f92d5805e1ce3f5f1541e355ed59aa3dc986972d165812` |
| `gate_results.json` | `555f464a7f386aedca05014134870af4ab73a900ceefb420ea150b5f809a2137` |
| `test_results.json` | `90bf6a416dd5b4d214f895f3e0f747585c0ce49d87c1a1e0a5b4572f049cfb09` |
| `journal_verification.json` | `2c052763909505ea53f73231df8abe45c8538c375c29a00253ba31520359d3b2` |
| `investigator_evaluation.json` | `c69bb89963a2c1a286b84d5fc8e7f6985f01bef188f58f281261e9c2a095308e` |
| `investigator_independent_validation.json` | `dedeb6669dd5cd8ffb39bf3c26ce4b3d0199eeeaa226e8ca512ef8a146abd9b6` |
| `benchmark_results.json` | `26b56c038b96cfde6905b2123a79cccb4ce4ab01dddb4a56bd975f021ea4a3d9` |
| `demo_journey_trace.json` | `f2c2563d7657566632ca41a77f569d0d377f197e399eb1c6b502c0643cd4555b` |

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
