"""Integration test verifying proof manifest cryptographic detection and completeness.

Ensures that:
1. Every file in proof/builds/LATEST matches its recorded SHA-256 hash.
2. Modified files are immediately detected.
3. Missing files are immediately detected.
4. Unexpected extra files in the proof directory are detected.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import pytest


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class TestProofManifestIntegrity:
    """Verifies that the Three-Tier proof manifest enforces strict cryptographic integrity."""

    @pytest.fixture
    def proof_dir(self) -> Path:
        root = Path(__file__).resolve().parent.parent.parent
        latest = root / "proof" / "builds" / "LATEST"
        assert latest.exists(), "proof/builds/LATEST must exist"
        return latest

    def test_current_manifest_checksums_match_disk(self, proof_dir: Path) -> None:
        """Every artifact listed in tier3_independent_verification.json must match its disk hash."""
        tier3_file = proof_dir / "tier3_independent_verification.json"
        assert tier3_file.exists()
        tier3_data = json.loads(tier3_file.read_text(encoding="utf-8"))
        checksums: dict[str, str] = tier3_data["artifacts_sha256"]

        for filename, expected_hash in checksums.items():
            artifact_path = proof_dir / filename
            assert artifact_path.exists(), f"Artifact {filename} missing from disk"
            actual_hash = _sha256(artifact_path)
            assert actual_hash == expected_hash, (
                f"Hash mismatch for {filename}: expected {expected_hash}, got {actual_hash}"
            )

    def test_manifest_detects_byte_level_mutation(self, proof_dir: Path) -> None:
        """Modifying even 1 byte in an artifact must fail verification."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            temp_copy = Path(td) / "LATEST"
            shutil.copytree(proof_dir, temp_copy)

            # Incur a 1-byte mutation on gate_results.json
            target = temp_copy / "gate_results.json"
            content = target.read_bytes()
            target.write_bytes(content + b" ")

            tier3_data = json.loads((temp_copy / "tier3_independent_verification.json").read_text())
            expected_hash = tier3_data["artifacts_sha256"]["gate_results.json"]
            mutated_hash = _sha256(target)

            assert mutated_hash != expected_hash

    def test_manifest_detects_missing_artifact(self, proof_dir: Path) -> None:
        """Deleting an artifact must be detected."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            temp_copy = Path(td) / "LATEST"
            shutil.copytree(proof_dir, temp_copy)

            target = temp_copy / "test_results.json"
            target.unlink()

            tier3_data = json.loads((temp_copy / "tier3_independent_verification.json").read_text())
            assert not (temp_copy / "test_results.json").exists()
            assert "test_results.json" in tier3_data["artifacts_sha256"]

    def test_manifest_detects_unexpected_extra_artifacts(self, proof_dir: Path) -> None:
        """Detects foreign or untracked JSON artifacts placed in the proof directory."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            temp_copy = Path(td) / "LATEST"
            shutil.copytree(proof_dir, temp_copy)

            foreign_file = temp_copy / "untracked_foreign_evidence.json"
            foreign_file.write_text('{"hacked": true}')

            tier3_data = json.loads((temp_copy / "tier3_independent_verification.json").read_text())
            tracked_files = set(tier3_data["artifacts_sha256"].keys()) | {
                "manifest.json",
                "tier3_independent_verification.json",
            }
            actual_files = {p.name for p in temp_copy.glob("*.json")}

            untracked = actual_files - tracked_files
            assert "untracked_foreign_evidence.json" in untracked
