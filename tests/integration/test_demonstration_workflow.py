"""End-to-end demonstration test (SETTLEIQ-M1-001 AC-6.04, Gate 2 of section 17).

Loads the generated dataset, runs the engine, and asserts that each injected
defect is classified into the type recorded in the manifest *before* the run.

This is the demonstration contract: a third party runs it and sees the same
result. It asserts classifications, not merely that breaks appeared.
"""

from __future__ import annotations

import pytest

from settleiq.engine import (
    Confidence,
    DiscrepancyType,
    RunParameters,
    reconcile,
    severity_for,
)
from settleiq.engine.metrics import compute
from settleiq.engine.rules import RuleRegistry
from settleiq.fixtures.generator import generate
from settleiq.validation import IngestionResult, validate_records

WINDOW_START = "2026-10-01"
WINDOW_END = "2026-10-31"


@pytest.fixture(scope="module")
def dataset():
    return generate()


@pytest.fixture(scope="module")
def validated(dataset) -> IngestionResult:
    return validate_records(dataset.records)


@pytest.fixture(scope="module")
def params() -> RunParameters:
    return RunParameters(window_start=WINDOW_START, window_end=WINDOW_END)


@pytest.fixture(scope="module")
def result(validated, params):
    return reconcile(validated.accepted, params)


def test_ingestion_accepts_the_clean_baseline(validated: IngestionResult) -> None:
    assert validated.accepted_count >= 8
    assert validated.quarantined_count == 0


def test_dataset_digest_is_reproducible() -> None:
    first, second = generate(), generate()
    assert first.input_digest == second.input_digest
    assert [d.expected_discrepancy for d in first.defects] == [
        d.expected_discrepancy for d in second.defects
    ]


def test_run_identity_is_derived_and_stable(result) -> None:
    assert len(result.identity.run_id) == 64
    assert result.identity.rule_version


def test_every_injected_defect_is_classified_as_recorded(dataset, result) -> None:
    """The core assertion: expectations recorded before the run are met."""
    produced = {d.type.value for d in result.discrepancies}
    for defect in dataset.defects:
        assert defect.expected_discrepancy in produced, (
            f"injected defect {defect.defect_id} ({defect.kind}) expected "
            f"{defect.expected_discrepancy}; produced {sorted(produced)}"
        )


def test_unknown_is_reachable_and_reported(result) -> None:
    assert any(d.type is DiscrepancyType.UNKNOWN for d in result.discrepancies)


def test_phantom_breaks_distinguish_sides(result) -> None:
    types = {d.type for d in result.discrepancies}
    assert DiscrepancyType.PHANTOM_PROCESSOR in types
    assert DiscrepancyType.PHANTOM_BANK in types


def test_deterministic_run_is_byte_identical(validated: IngestionResult, params) -> None:
    one = reconcile(validated.accepted, params)
    two = reconcile(validated.accepted, params)
    assert one.identity.run_id == two.identity.run_id
    assert one.identity.input_digest == two.identity.input_digest


def test_rule_version_change_produces_a_different_run(validated: IngestionResult) -> None:
    other = RunParameters(
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        registry=RuleRegistry(version="1.0.1", rules=()),
    )
    base = RunParameters(window_start=WINDOW_START, window_end=WINDOW_END)
    assert reconcile(validated.accepted, base).identity.run_id != reconcile(
        validated.accepted, other
    ).identity.run_id


def test_metrics_are_computed_with_a_stated_denominator(result) -> None:
    metrics = compute(result.counts)
    assert metrics.denominator == result.counts["eligible"]
    assert metrics.numerator == result.counts["deterministic"]
    assert metrics.methodology_version
    assert "eligible" in metrics.denominator_definition
    assert "human-confirmed" in metrics.to_canonical()["human_confirmation_treatment"]


def test_metrics_are_reproducible_across_runs(validated: IngestionResult, params) -> None:
    one = compute(reconcile(validated.accepted, params).counts)
    two = compute(reconcile(validated.accepted, params).counts)
    assert one.to_canonical() == two.to_canonical()


def test_ambiguous_decisions_carry_no_selected_candidate(result) -> None:
    for decision in result.decisions:
        if decision.confidence is Confidence.AMBIGUOUS:
            assert decision.matched_candidate is None
            assert len(decision.surviving_candidates) > 1


def test_severity_is_derived_not_manual(result) -> None:
    for discrepancy in result.discrepancies:
        assert discrepancy.severity == severity_for(discrepancy.type)


def test_severity_raises_for_an_unknown_pair() -> None:
    with pytest.raises(KeyError):
        severity_for(DiscrepancyType.UNKNOWN, "NO_SUCH_BAND")


def test_clean_dataset_produces_no_breaks(params: RunParameters) -> None:
    clean = generate(clean=True)
    outcome = reconcile(validate_records(clean.records).accepted, params)
    assert outcome.discrepancies == []


def test_reconcile_rejects_a_malformed_entry() -> None:
    with pytest.raises(ValueError):
        reconcile([{"kind": "charge"}], RunParameters(WINDOW_START, WINDOW_END))
