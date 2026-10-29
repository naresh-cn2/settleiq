# SettleIQ — Permanent Verifiable Proof Manifest

This repository maintains a formal **Three-Tier Verification System** providing
cryptographic and empirical proof of mathematical correctness, deterministic matching,
AI reasoning accuracy, and tamper detection.

> [!WARNING]
> **Cryptographic Scope & Limitation**: SHA-256 digests verify accidental corruption, bit-rot, and file tampering relative to the manifest. They do NOT provide authenticity or immutability against an attacker who has write access to both the artifact repository and the manifest itself, unless the root digest is externally anchored to an immutable ledger or witness log.

## Summary of Verification Tiers

- **Generated At:** `2026-10-29T16:41:54.602863+00:00`
- **Git Commit:** `63f83895ccffd7af6c6675a92935f06fb9711ca1` (`main`)
- **Platform:** `Windows 11 (AMD64)`
- **Python Version:** `3.12.10`

### Tier 1: Execution Evidence (Quality Gates & Compilations)

| Gate | Requirement | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **G1: Money Safety** | Zero binary float usage | AST static gate clean (0 violations) | **PASS** |
| **G2: Test Suite** | 100% test pass rate | 204 passing tests | **PASS** |
| **G3: Code Quality** | Zero static lint warnings | Clean ruff static check | **PASS** |
| **G4: Engine Throughput** | > 1,000 records/sec | 3,812.4 rec/s (10k batch) | **PASS** |
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
| `tier1_execution_evidence.json` | `773fbef587a5f00b970ff229676ef31fc6e1c58c2e2fc73dca3c5d57f6734c4f` |
| `tier2_acceptance_evidence.json` | `e80a6fe9d33bcada9ec4842ba38f99923a220dbed2be97e5f0c4b0d316cc4fac` |
| `tier3_independent_verification.json` | `73d13698b4232954c534756d6320561f09d40a270a42d5f886db2a54b4525d93` |
| `gate_results.json` | `81ba477737d358ce968652539dda198831e516cbb1f27b42783de074711c09d8` |
| `test_results.json` | `5b0b9e5440922130430665c63f7e1cdd5bdbaf2ac12eb54415f21501b7c4bfc9` |
| `journal_verification.json` | `4df66302f28a77bbc9651711d2db14562816475a51a241ba6438e70b65d8a1e2` |
| `investigator_evaluation.json` | `6acbcf9235d015e87c69ac6840c96f166c86efb53e51c0cf38dfc837969541fe` |
| `investigator_independent_validation.json` | `6180c7d3252788b504bd597380099f2751d7671bac64e3354f6a37d78d6d8348` |
| `benchmark_results.json` | `e5a8bdb4d7be4e6bae162e8973ebc7f905dde9c0386d90ebe9d76fc95d215c86` |
| `demo_journey_trace.json` | `463e4d47c337bdab8b55e20d7be8abd14441c4e30a4918e1773c5adfb4ee7927` |

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
