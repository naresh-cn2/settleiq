# SettleIQ — Permanent Verifiable Proof Manifest

This repository maintains a formal **Three-Tier Verification System** providing
cryptographic and empirical proof of mathematical correctness, deterministic matching,
AI reasoning accuracy, and tamper detection.

## Summary of Verification Tiers

- **Generated At:** `2026-10-29T08:33:43.098168+00:00`
- **Git Commit:** `2d03f9a04c0fc4380795971b01540bb8c81d35ed` (`main`)
- **Platform:** `Windows 11 (AMD64)`
- **Python Version:** `3.12.10`

### Tier 1: Execution Evidence (Quality Gates & Compilations)

| Gate | Requirement | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **G1: Money Safety** | Zero binary float usage | AST static gate clean (0 violations) | **PASS** |
| **G2: Test Suite** | 100% test pass rate | 193 passing tests | **PASS** |
| **G3: Code Quality** | Zero static lint warnings | Clean ruff static check | **PASS** |
| **G4: Engine Throughput** | > 1,000 records/sec | 900.5 rec/s (10k batch) | **PASS** |
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
| `tier1_execution_evidence.json` | `247208be1d3718b5b7c55da7bffeb3b19a7a8ab15376bd5afdfd34c67688f124` |
| `tier2_acceptance_evidence.json` | `7fa8d98818c98bbbd76ffd473d9ad71ec3f7eebf2352bfdf906a090bdfb559d2` |
| `tier3_independent_verification.json` | `8d345be9dc018fab5bf5bc25c54497a2ba03954c127ffde79304ba341fc8dc11` |
| `gate_results.json` | `555f464a7f386aedca05014134870af4ab73a900ceefb420ea150b5f809a2137` |
| `test_results.json` | `c626d18ef9de41280f67dc46ff7641f57d6f96a2f78ea0a74b43c8b42bb0b582` |
| `journal_verification.json` | `2c052763909505ea53f73231df8abe45c8538c375c29a00253ba31520359d3b2` |
| `investigator_evaluation.json` | `5ff120109a2de38b6c46fbec9d23893fe9293cf30968af99464b7b6c0ffcd8e5` |
| `investigator_independent_validation.json` | `97a5ceb4abea69de79d2f22904fa30497ce677605b8dd7182a6458cbf4c73175` |
| `benchmark_results.json` | `bf087e4ce8ffa37423a9aef864c41efc9679c3a0e6c49ce6a2730e5f36672202` |
| `demo_journey_trace.json` | `8e2c6b3c1bac49e902407efb42e05be260fe0efcad5eb794521d5762cf962162` |

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
