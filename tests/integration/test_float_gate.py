"""The money-safety gate, exercised as a test (SETTLEIQ-M1-001 AC-7.04).

A gate that is described but not executed is not a gate. These tests both prove
it catches a real float and prove it passes on the real codebase.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from settleiq.gates.float_gate import scan, scan_package

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC = REPO_ROOT / "src" / "settleiq"


def test_gate_passes_on_the_real_monetary_packages() -> None:
    violations = scan_package(SRC / "money") + scan_package(SRC / "model")
    assert violations == [], f"unexpected violations: {violations}"


def test_gate_detects_a_float_literal(tmp_path: Path) -> None:
    bad = tmp_path / "bad.py"
    bad.write_text("x = 1.5\n", encoding="utf-8")
    violations = scan(bad)
    assert len(violations) == 1
    assert "literal" in violations[0].detail


def test_gate_detects_a_float_call(tmp_path: Path) -> None:
    bad = tmp_path / "bad_call.py"
    bad.write_text("value = float(text)\n", encoding="utf-8")
    assert any("float()" in v.detail for v in scan(bad))


def test_gate_detects_a_float_annotation(tmp_path: Path) -> None:
    bad = tmp_path / "bad_ann.py"
    bad.write_text("def f(x: float) -> None:\n    pass\n", encoding="utf-8")
    assert any("annotation" in v.detail for v in scan(bad))


def test_gate_respects_an_explicit_waiver(tmp_path: Path) -> None:
    ok = tmp_path / "ok.py"
    ok.write_text("x = 1.5  # gate: waive\n", encoding="utf-8")
    assert scan(ok) == []


def test_gate_reports_a_clean_exit_code() -> None:
    from settleiq.gates.float_gate import main

    assert main([str(SRC / "money")]) == 0
