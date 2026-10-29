"""Comprehensive empirical evaluation suite for the AI Discrepancy Investigator.

Tests:
1. Ground-truth root cause classification across all 7 discrepancy types.
2. Positive and negative residual decomposition (fee deduction vs rebate).
3. Timing lag vs clock skew vs contradictory SLA window evidence.
4. Amount break wire fee vs deposit overpayment vs identical amount contradiction.
5. Incomplete / insufficient evidence uncertainty handling.
6. Non-mutation invariant: draft resolutions do not alter database or audit journal.
7. Precision and Top-1 hypothesis ranking metrics.
"""

from decimal import Decimal
from typing import Any

from settleiq.engine.discrepancy import DiscrepancyType
from settleiq.engine.investigator import (
    build_transaction_trace,
    investigate_discrepancy,
)
from settleiq.persistence.store import open_store


def test_eval_net_gross_shortfall_deduction() -> None:
    """Case 1: Payout is LESS than net expected (fee/reserve deduction)."""
    disc = {
        "discrepancy_id": "disc_fee_deduct",
        "type": DiscrepancyType.NET_GROSS_BREAK.value,
        "severity": "HIGH",
        "constituent_id": "po_batch_short",
        "reason": (
            "batch 'po_batch_short' nets 100.00|USD but the payout paid 95.00|USD; "
            "residual 5.00|USD"
        ),
    }
    report = investigate_discrepancy(disc)
    assert report.hypotheses[0].rank == 1
    assert "Interchange Fee or Reserve Deduction" in report.hypotheses[0].title
    assert report.hypotheses[0].confidence == "HIGH"
    assert report.recommended_action == "ADJUST_FEE"
    assert report.draft_resolution["action"] == "ADJUST_FEE"


def test_eval_net_gross_surplus_rebate() -> None:
    """Case 2: Payout is MORE than net expected (processor rebate/credit)."""
    disc = {
        "discrepancy_id": "disc_rebate_surplus",
        "type": DiscrepancyType.NET_GROSS_BREAK.value,
        "severity": "HIGH",
        "constituent_id": "po_batch_surplus",
        "reason": (
            "batch 'po_batch_surplus' nets 56.00|USD but the payout paid 60.00|USD; "
            "residual -4.00|USD"
        ),
    }
    report = investigate_discrepancy(disc)
    assert report.hypotheses[0].rank == 1
    assert "Retroactive Fee Rebate" in report.hypotheses[0].title
    assert report.hypotheses[0].confidence == "HIGH"
    assert report.recommended_action == "BOOK_REBATE"
    assert report.draft_resolution["action"] == "BOOK_REBATE"


def test_eval_amount_break_wire_fee() -> None:
    """Case 3: Bank deposit is less than processor payout (intermediary fee)."""
    disc = {
        "discrepancy_id": "disc_wire_fee",
        "type": DiscrepancyType.AMOUNT_BREAK.value,
        "severity": "MEDIUM",
        "constituent_id": "po_wire",
        "reason": "payout paid 500.00|USD but deposit posted 485.00|USD",
    }
    report = investigate_discrepancy(disc)
    assert report.hypotheses[0].rank == 1
    assert "Wire Clearing Fee" in report.hypotheses[0].title
    assert report.hypotheses[0].confidence == "HIGH"
    assert report.recommended_action == "ACCEPT_TOLERANCE"


def test_eval_amount_break_overpayment() -> None:
    """Case 4: Bank deposit is MORE than payout (consolidated settlement)."""
    disc = {
        "discrepancy_id": "disc_overpay",
        "type": DiscrepancyType.AMOUNT_BREAK.value,
        "severity": "HIGH",
        "constituent_id": "po_overpay",
        "reason": "payout paid 500.00|USD but deposit posted 650.00|USD",
    }
    report = investigate_discrepancy(disc)
    assert report.hypotheses[0].rank == 1
    assert "Consolidated Bank Deposit" in report.hypotheses[0].title
    assert report.recommended_action == "INVESTIGATE_OVERPAYMENT"


def test_eval_amount_break_contradictory_evidence() -> None:
    """Case 5: Reason claims amount break but payout equals deposit."""
    disc = {
        "discrepancy_id": "disc_contra_amount",
        "type": DiscrepancyType.AMOUNT_BREAK.value,
        "severity": "MEDIUM",
        "constituent_id": "po_contra",
        "reason": "payout paid 100.00|USD but deposit posted 100.00|USD",
    }
    report = investigate_discrepancy(disc)
    assert report.hypotheses[0].confidence == "INSUFFICIENT"
    assert "Contradictory Evidence" in report.hypotheses[0].title
    assert report.recommended_action == "MANUAL_REVIEW"


def test_eval_timing_break_lag() -> None:
    """Case 6: Bank deposit posted late (clearing lag)."""
    disc = {
        "discrepancy_id": "disc_timing_lag",
        "type": DiscrepancyType.TIMING_BREAK.value,
        "severity": "LOW",
        "constituent_id": "po_lag",
        "reason": "payout arrived 2026-10-01, deposit posted 2026-10-14: 13 days exceeds window",
    }
    report = investigate_discrepancy(disc)
    assert report.hypotheses[0].rank == 1
    assert "Clearing Lag" in report.hypotheses[0].title
    assert report.hypotheses[0].confidence == "HIGH"
    assert report.recommended_action == "ACCEPT_LAG"


def test_eval_timing_break_clock_skew() -> None:
    """Case 7: Deposit posted before payout arrived (pre-funding or clock skew)."""
    disc = {
        "discrepancy_id": "disc_timing_skew",
        "type": DiscrepancyType.TIMING_BREAK.value,
        "severity": "MEDIUM",
        "constituent_id": "po_skew",
        "reason": "payout arrived 2026-10-10, deposit posted 2026-10-08: -2 days exceeds window",
    }
    report = investigate_discrepancy(disc)
    assert report.hypotheses[0].rank == 1
    assert "Pre-funding" in report.hypotheses[0].title
    assert report.recommended_action == "VERIFY_CLOCK_SKEW"


def test_eval_timing_break_contradictory_window() -> None:
    """Case 8: Elapsed days within 3-day window."""
    disc = {
        "discrepancy_id": "disc_timing_within",
        "type": DiscrepancyType.TIMING_BREAK.value,
        "severity": "LOW",
        "constituent_id": "po_within",
        "reason": "payout arrived 2026-10-01, deposit posted 2026-10-03: 2 days exceeds window",
    }
    report = investigate_discrepancy(disc)
    assert report.hypotheses[0].confidence == "INSUFFICIENT"
    assert "Contradictory Evidence" in report.hypotheses[0].title
    assert report.recommended_action == "MANUAL_REVIEW"


def test_eval_insufficient_evidence() -> None:
    """Case 9: Empty reason and no records provided."""
    disc = {
        "discrepancy_id": "disc_empty",
        "type": DiscrepancyType.NET_GROSS_BREAK.value,
        "severity": "HIGH",
        "constituent_id": "po_empty",
        "reason": "",
    }
    report = investigate_discrepancy(disc)
    assert report.hypotheses[0].confidence == "INSUFFICIENT"
    assert "Insufficient Evidence" in report.hypotheses[0].title
    assert report.recommended_action == "MANUAL_REVIEW"


def test_eval_unknown_schema_type() -> None:
    """Case 10: Unmodeled record type (e.g. chargeback dispute)."""
    disc = {
        "discrepancy_id": "disc_unknown",
        "type": DiscrepancyType.UNKNOWN.value,
        "severity": "HIGH",
        "constituent_id": "dp_1",
        "reason": "record kind 'dispute' is not modelled by the canonical data model",
    }
    report = investigate_discrepancy(disc)
    assert report.hypotheses[0].confidence == "INSUFFICIENT"
    assert "Unrecognized Record Schema" in report.hypotheses[0].title
    assert report.recommended_action == "MANUAL_REVIEW"


def test_eval_draft_resolution_non_mutation_invariant(tmp_path) -> None:
    """Case 11: Invoking investigator NEVER mutates persistence or audit ledger."""
    store = open_store(tmp_path / "test_freeze.sqlite3")
    from settleiq.engine import RunParameters, reconcile
    from settleiq.fixtures.generator import generate
    from settleiq.validation import validate_records

    dataset = generate()
    validated = validate_records(dataset.records)
    result = reconcile(validated.accepted, RunParameters("2026-10-01", "2026-10-31"))
    run_id = store.record_run(result)

    discrepancies = store.discrepancies_for(run_id)
    assert len(discrepancies) > 0
    target_disc = discrepancies[0]
    disc_id = target_disc["discrepancy_id"]

    # Call investigator
    report = investigate_discrepancy(target_disc)
    assert report.draft_resolution is not None

    # Verify store discrepancy status remains strictly OPEN
    stored_after = store.find_discrepancy(disc_id)
    assert stored_after is not None
    assert stored_after["status"] == "OPEN"
    assert "resolution_history" not in stored_after or len(stored_after["resolution_history"]) == 0
    assert "resolution_history" not in stored_after or len(stored_after["resolution_history"]) == 0


def test_eval_top1_accuracy_benchmark() -> None:
    """Case 12: Benchmark Top-1 accuracy across 10 labelled test cases."""
    labelled_cases: list[dict[str, Any]] = [
        {
            "disc": {
                "discrepancy_id": "d1",
                "type": "NET_GROSS_BREAK",
                "reason": "nets 100.00|USD but the payout paid 90.00|USD; residual 10.00|USD",
            },
            "expected_action": "ADJUST_FEE",
            "expected_confidence": "HIGH",
        },
        {
            "disc": {
                "discrepancy_id": "d2",
                "type": "NET_GROSS_BREAK",
                "reason": "nets 50.00|USD but the payout paid 60.00|USD; residual -10.00|USD",
            },
            "expected_action": "BOOK_REBATE",
            "expected_confidence": "HIGH",
        },
        {
            "disc": {
                "discrepancy_id": "d3",
                "type": "AMOUNT_BREAK",
                "reason": "payout paid 100.00|USD but deposit posted 95.00|USD",
            },
            "expected_action": "ACCEPT_TOLERANCE",
            "expected_confidence": "HIGH",
        },
        {
            "disc": {
                "discrepancy_id": "d4",
                "type": "AMOUNT_BREAK",
                "reason": "payout paid 100.00|USD but deposit posted 110.00|USD",
            },
            "expected_action": "INVESTIGATE_OVERPAYMENT",
            "expected_confidence": "HIGH",
        },
        {
            "disc": {
                "discrepancy_id": "d5",
                "type": "TIMING_BREAK",
                "reason": "payout arrived 2026-10-01, deposit posted 2026-10-15: 14 days",
            },
            "expected_action": "ACCEPT_LAG",
            "expected_confidence": "HIGH",
        },
        {
            "disc": {
                "discrepancy_id": "d6",
                "type": "TIMING_BREAK",
                "reason": "payout arrived 2026-10-10, deposit posted 2026-10-05: -5 days",
            },
            "expected_action": "VERIFY_CLOCK_SKEW",
            "expected_confidence": "HIGH",
        },
        {
            "disc": {
                "discrepancy_id": "d7",
                "type": "PHANTOM_PROCESSOR",
                "reason": "charge has no payout on processor side",
            },
            "expected_action": "HOLD_IN_SUSPENSE",
            "expected_confidence": "HIGH",
        },
        {
            "disc": {
                "discrepancy_id": "d8",
                "type": "PHANTOM_BANK",
                "reason": "bank deposit reference matches no payout",
            },
            "expected_action": "RECLASSIFY_DEPOSIT",
            "expected_confidence": "HIGH",
        },
        {
            "disc": {
                "discrepancy_id": "d9",
                "type": "AMBIGUOUS_MATCH",
                "reason": "2 candidates survived without tie breaker",
            },
            "expected_action": "REQUIRE_HUMAN_SELECTION",
            "expected_confidence": "MEDIUM",
        },
        {
            "disc": {
                "discrepancy_id": "d10",
                "type": "UNKNOWN",
                "reason": "record kind 'unrecognized' is unmodeled",
            },
            "expected_action": "MANUAL_REVIEW",
            "expected_confidence": "INSUFFICIENT",
        },
    ]

    correct_actions = 0
    correct_confidences = 0
    total = len(labelled_cases)

    for item in labelled_cases:
        report = investigate_discrepancy(item["disc"])
        if report.recommended_action == item["expected_action"]:
            correct_actions += 1
        if report.hypotheses[0].confidence == item["expected_confidence"]:
            correct_confidences += 1

    action_accuracy = correct_actions / total
    confidence_accuracy = correct_confidences / total

    assert action_accuracy == 1.0, f"Top-1 action accuracy {action_accuracy:.2%} < 100%"
    assert confidence_accuracy == 1.0, f"Confidence accuracy {confidence_accuracy:.2%} < 100%"


def test_eval_trace_algebraic_reconciliation() -> None:
    """Case 13: Transaction trace algebraic reconciliation across complex multi-events."""
    records = [
        {"kind": "charge", "id": "c1", "amount": "100.00", "currency": "USD", "batch": "b_eval"},
        {"kind": "charge", "id": "c2", "amount": "250.00", "currency": "USD", "batch": "b_eval"},
        {"kind": "fee", "id": "f1", "amount": "10.50", "currency": "USD", "batch": "b_eval"},
        {"kind": "refund", "id": "r1", "amount": "50.00", "currency": "USD", "batch": "b_eval"},
        # Net expected = (100 + 250) - 10.50 - 50 = 289.50
        {"kind": "payout", "id": "p1", "amount": "280.00", "currency": "USD", "batch": "b_eval"},
        {"kind": "deposit", "id": "d1", "amount": "280.00", "currency": "USD", "batch": "b_eval"},
    ]
    disc = {"discrepancy_id": "d_trace", "type": "NET_GROSS_BREAK", "constituent_id": "p1"}
    trace = build_transaction_trace(disc, records=records)

    assert Decimal(trace.gross_amount) == Decimal("350.00")
    assert Decimal(trace.fee_amount) == Decimal("10.50")
    assert Decimal(trace.refund_amount) == Decimal("50.00")
    assert Decimal(trace.net_expected) == Decimal("289.50")
    assert Decimal(trace.net_paid) == Decimal("280.00")
    assert Decimal(trace.residual) == Decimal("9.50")
    assert trace.is_closed is False
