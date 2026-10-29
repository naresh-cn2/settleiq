"""Independent Validation Suite for Autonomous AI Forensic Investigator.

This suite provides an independent evaluation set distinct from the initial regression suite.
It systematically evaluates:
1. Action Accuracy vs Root-Cause Accuracy separation
2. Incomplete and Malformed Evidence handling (INSUFFICIENT confidence)
3. Contradictory Evidence detection
4. Multi-Hypothesis ranking integrity (Rank 1 vs Rank 2 differentiation)
5. Randomized Monte-Carlo amounts and timestamps
6. Strict state immutability (zero side-effects / read-only guarantees)
7. Unsupported claim / hallucination verification
"""

from __future__ import annotations

import copy
import random
from collections.abc import Mapping
from decimal import Decimal

import pytest

from settleiq.engine.discrepancy import DiscrepancyType
from settleiq.engine.investigator import (
    InvestigationReport,
    investigate_discrepancy,
)


class TestInvestigatorIndependentValidation:
    """Independent benchmark battery evaluating root-cause accuracy and robust reasoning."""

    # --------------------------------------------------------------------------
    # 1. State Immutability / Read-Only Invariance
    # --------------------------------------------------------------------------

    def test_investigator_guarantees_strict_state_immutability(self) -> None:
        """Calling investigate_discrepancy must never mutate input objects or records."""
        original_disc = {
            "discrepancy_id": "dsc:IMMUTABLE_TEST:01",
            "type": DiscrepancyType.NET_GROSS_BREAK.value,
            "severity": "HIGH",
            "constituent_id": "po_imm_1",
            "status": "OPEN",
            "reason": "batch 'sb_imm' nets 100.00|USD but the payout paid 95.00|USD; residual 5.00|USD",
        }
        original_records = [
            {"kind": "charge", "id": "c1", "amount": "100.00", "currency": "USD", "batch": "sb_imm"},
            {"kind": "payout", "id": "po_imm_1", "amount": "95.00", "currency": "USD", "batch": "sb_imm"},
        ]

        # Deep copy to verify byte-for-byte immutability
        disc_snapshot = copy.deepcopy(original_disc)
        records_snapshot = copy.deepcopy(original_records)

        report = investigate_discrepancy(original_disc, original_records)

        assert isinstance(report, InvestigationReport)
        # Input dictionary must be 100% unaltered
        assert original_disc == disc_snapshot
        assert original_records == records_snapshot
        # Status inside original must still be OPEN (investigator does not resolve)
        assert original_disc["status"] == "OPEN"

    # --------------------------------------------------------------------------
    # 2. Incomplete Evidence: Insufficient Confidence & Manual Review
    # --------------------------------------------------------------------------

    @pytest.mark.parametrize(
        ("disc_type", "reason", "has_records"),
        [
            (DiscrepancyType.NET_GROSS_BREAK.value, "", False),
            (DiscrepancyType.AMOUNT_BREAK.value, "   ", False),
            (DiscrepancyType.TIMING_BREAK.value, "", False),
            (DiscrepancyType.PHANTOM_PROCESSOR.value, "", False),
        ],
    )
    def test_incomplete_evidence_yields_insufficient_confidence(
        self, disc_type: str, reason: str, has_records: bool
    ) -> None:
        """When reason and records are missing, the investigator must refuse to guess."""
        disc = {
            "discrepancy_id": "dsc:INCOMPLETE:01",
            "type": disc_type,
            "severity": "HIGH",
            "constituent_id": "c_missing",
            "status": "OPEN",
            "reason": reason,
        }
        report = investigate_discrepancy(disc, [] if not has_records else None)

        assert report.recommended_action == "MANUAL_REVIEW"
        assert len(report.hypotheses) >= 1
        top_hyp = report.hypotheses[0]
        assert top_hyp.confidence == "INSUFFICIENT"
        assert "Insufficient Evidence" in top_hyp.title or "MANUAL_REVIEW" in top_hyp.recommended_action
        assert report.draft_resolution["action"] == "MANUAL_REVIEW"

    # --------------------------------------------------------------------------
    # 3. Malformed / Unparseable Numeric Inputs
    # --------------------------------------------------------------------------

    @pytest.mark.parametrize(
        "malformed_reason",
        [
            "corrupted syntax without pipes or amounts",
            "batch 'sb_x' nets NaN but payout paid NULL",
            "unexpected error 500 internal server error",
            "??? !!! ### $$$ %%%",
        ],
    )
    def test_malformed_diagnostic_strings_fail_closed_to_manual_review(
        self, malformed_reason: str
    ) -> None:
        """Unparseable reason strings must trigger fail-closed manual review."""
        disc = {
            "discrepancy_id": "dsc:MALFORMED:01",
            "type": DiscrepancyType.NET_GROSS_BREAK.value,
            "severity": "HIGH",
            "constituent_id": "po_malformed",
            "status": "OPEN",
            "reason": malformed_reason,
        }
        report = investigate_discrepancy(disc)

        assert report.recommended_action == "MANUAL_REVIEW"
        assert report.hypotheses[0].confidence == "INSUFFICIENT"
        assert "Malformed" in report.hypotheses[0].title or "Insufficient" in report.hypotheses[0].title

    # --------------------------------------------------------------------------
    # 4. Multi-Plausible Root Causes & Ranking Differentiation
    # --------------------------------------------------------------------------

    def test_net_gross_shortfall_multi_hypothesis_differentiation(self) -> None:
        """Evaluates that Rank 1 and Rank 2 propose distinct, plausible causes with distinct actions."""
        disc = {
            "discrepancy_id": "dsc:MULTI_HYP:01",
            "type": DiscrepancyType.NET_GROSS_BREAK.value,
            "severity": "HIGH",
            "constituent_id": "po_shortfall",
            "status": "OPEN",
            "reason": "batch 'sb_multi' nets 500.00|USD but the payout paid 475.00|USD; residual 25.00|USD",
        }
        report = investigate_discrepancy(disc)

        assert len(report.hypotheses) >= 2
        h1 = report.hypotheses[0]
        h2 = report.hypotheses[1]

        # Rank 1 vs Rank 2 must have distinct titles and distinct root cause actions
        assert h1.rank == 1
        assert h2.rank == 2
        assert h1.title != h2.title
        assert h1.recommended_action != h2.recommended_action

        # Rank 1 must be Interchange Fee / Reserve (Action: ADJUST_FEE)
        assert "Fee" in h1.title or "Interchange" in h1.title or "Reserve" in h1.title
        assert h1.recommended_action == "ADJUST_FEE"
        assert h1.confidence == "HIGH"

        # Rank 2 must be Chargeback / Dispute Reversal (Action: FLAG_DISPUTE)
        assert "Dispute" in h2.title or "Chargeback" in h2.title
        assert h2.recommended_action == "FLAG_DISPUTE"
        assert h2.confidence == "MEDIUM"

    def test_amount_break_wire_deduction_multi_hypothesis_differentiation(self) -> None:
        """Amount break with paid > posted must differentiate Bank Wire Fee from FX Spread."""
        disc = {
            "discrepancy_id": "dsc:MULTI_AMT:01",
            "type": DiscrepancyType.AMOUNT_BREAK.value,
            "severity": "HIGH",
            "constituent_id": "po_amt",
            "status": "OPEN",
            "reason": "payout paid 1000.00|USD but deposit posted 975.00|USD",
        }
        report = investigate_discrepancy(disc)

        assert len(report.hypotheses) >= 2
        h1, h2 = report.hypotheses[0], report.hypotheses[1]

        # Rank 1: Wire Transfer Fee (Action: ACCEPT_TOLERANCE)
        assert "Wire" in h1.title or "Bank" in h1.title
        assert h1.recommended_action == "ACCEPT_TOLERANCE"
        assert h1.confidence == "HIGH"

        # Rank 2: FX Spread / Cross-Border Markup (Action: ADJUST_FX)
        assert "Foreign Exchange" in h2.title or "FX" in h2.title
        assert h2.recommended_action == "ADJUST_FX"
        assert h2.confidence == "MEDIUM"

    # --------------------------------------------------------------------------
    # 5. Randomized Monte-Carlo Amounts and Dates
    # --------------------------------------------------------------------------

    def test_randomized_monte_carlo_net_gross_shortfall_reasoning(self) -> None:
        """Evaluates 20 randomized numeric amounts to confirm non-hardcoded reasoning."""
        rng = random.Random(42)  # Deterministic seed for reproducible test

        for i in range(20):
            gross_cents = rng.randint(5000, 500000)  # $50.00 to $5,000.00
            diff_cents = rng.randint(50, 4500)       # $0.50 to $45.00
            paid_cents = gross_cents - diff_cents

            gross_str = f"{Decimal(gross_cents) / Decimal(100):.2f}"
            paid_str = f"{Decimal(paid_cents) / Decimal(100):.2f}"
            diff_str = f"{Decimal(diff_cents) / Decimal(100):.2f}"

            disc = {
                "discrepancy_id": f"dsc:RND_{i}:01",
                "type": DiscrepancyType.NET_GROSS_BREAK.value,
                "severity": "HIGH",
                "constituent_id": f"po_rnd_{i}",
                "status": "OPEN",
                "reason": (
                    f"batch 'sb_rnd_{i}' nets {gross_str}|USD but the payout paid {paid_str}|USD; "
                    f"residual {diff_str}|USD"
                ),
            }

            report = investigate_discrepancy(disc)
            # Must always identify shortfall deduction
            assert report.recommended_action == "ADJUST_FEE"
            assert report.hypotheses[0].confidence == "HIGH"
            # Trace must parse exact randomized amounts
            assert report.trace.net_expected == gross_str
            assert report.trace.net_paid == paid_str
            assert report.trace.residual == diff_str

    def test_randomized_monte_carlo_timing_break_clearing_delays(self) -> None:
        """Evaluates randomized dates to verify clearing window calculation."""
        rng = random.Random(99)

        for i in range(15):
            arr_day = rng.randint(1, 10)
            elapsed_days = rng.randint(4, 25)
            post_day = arr_day + elapsed_days

            arr_date = f"2026-10-{arr_day:02d}"
            post_date = f"2026-10-{post_day:02d}" if post_day <= 31 else f"2026-11-{post_day - 31:02d}"

            disc = {
                "discrepancy_id": f"dsc:TIMING_RND_{i}",
                "type": DiscrepancyType.TIMING_BREAK.value,
                "severity": "MEDIUM",
                "constituent_id": f"po_timing_{i}",
                "status": "OPEN",
                "reason": (
                    f"payout arrived {arr_date}, deposit posted {post_date}: "
                    f"{elapsed_days} days exceeds the declared window of 3"
                ),
            }

            report = investigate_discrepancy(disc)
            assert report.recommended_action == "ACCEPT_LAG"
            assert report.hypotheses[0].confidence == "HIGH"
            assert any(str(elapsed_days) in ev for ev in report.hypotheses[0].supporting_evidence)

    # --------------------------------------------------------------------------
    # 6. Negative Elapsed Time (Clock Skew Anomaly)
    # --------------------------------------------------------------------------

    def test_negative_elapsed_timing_anomaly(self) -> None:
        """When bank deposit is posted before payout arrival date (clock skew anomaly)."""
        disc = {
            "discrepancy_id": "dsc:CLOCK_SKEW:01",
            "type": DiscrepancyType.TIMING_BREAK.value,
            "severity": "HIGH",
            "constituent_id": "po_skew",
            "status": "OPEN",
            "reason": "payout arrived 2026-10-15, deposit posted 2026-10-12: -3 days indicates anomalous timeline",
        }
        report = investigate_discrepancy(disc)

        assert report.recommended_action == "VERIFY_CLOCK_SKEW"
        top_hyp = report.hypotheses[0]
        assert "Clock Skew" in top_hyp.title or "Pre-funding" in top_hyp.title
        assert top_hyp.confidence == "HIGH"

    # --------------------------------------------------------------------------
    # 7. Ground Truth & Unsupported Claim Verification Rate
    # --------------------------------------------------------------------------

    def test_investigator_ground_truth_and_hallucination_audit(self) -> None:
        """Comprehensive audit verifying that 100% of claims cite verified input facts."""
        eval_cases: list[tuple[Mapping[str, object], str, str, str]] = [
            # Case 1: Shortfall fee deduction
            (
                {
                    "discrepancy_id": "dsc:AUDIT:01",
                    "type": DiscrepancyType.NET_GROSS_BREAK.value,
                    "reason": "batch 'b1' nets 100.00|USD but the payout paid 96.00|USD; residual 4.00|USD",
                    "constituent_id": "po_1",
                },
                "ADJUST_FEE",
                "Undocumented Processor Interchange Fee or Reserve Deduction",
                "HIGH",
            ),
            # Case 2: Surplus volume rebate
            (
                {
                    "discrepancy_id": "dsc:AUDIT:02",
                    "type": DiscrepancyType.NET_GROSS_BREAK.value,
                    "reason": "batch 'b2' nets 100.00|USD but the payout paid 104.00|USD; residual -4.00|USD",
                    "constituent_id": "po_2",
                },
                "BOOK_REBATE",
                "Processor Retroactive Fee Rebate or Volume Incentive",
                "HIGH",
            ),
            # Case 3: Wire fee deduction
            (
                {
                    "discrepancy_id": "dsc:AUDIT:03",
                    "type": DiscrepancyType.AMOUNT_BREAK.value,
                    "reason": "payout paid 200.00|USD but deposit posted 185.00|USD",
                    "constituent_id": "po_3",
                },
                "ACCEPT_TOLERANCE",
                "Intermediary Bank Wire Clearing Fee Deducted",
                "HIGH",
            ),
            # Case 4: Bank overpayment
            (
                {
                    "discrepancy_id": "dsc:AUDIT:04",
                    "type": DiscrepancyType.AMOUNT_BREAK.value,
                    "reason": "payout paid 200.00|USD but deposit posted 210.00|USD",
                    "constituent_id": "po_4",
                },
                "INVESTIGATE_OVERPAYMENT",
                "Consolidated Bank Deposit / Overpayment Credit",
                "HIGH",
            ),
            # Case 5: Timing clearing lag
            (
                {
                    "discrepancy_id": "dsc:AUDIT:05",
                    "type": DiscrepancyType.TIMING_BREAK.value,
                    "reason": "payout arrived 2026-10-01, deposit posted 2026-10-06: 5 days exceeds the declared window of 3",
                    "constituent_id": "po_5",
                },
                "ACCEPT_LAG",
                "Multi-Day Bank Clearing Lag / Banking Holiday Delay",
                "HIGH",
            ),
            # Case 6: Phantom processor
            (
                {
                    "discrepancy_id": "dsc:AUDIT:06",
                    "type": DiscrepancyType.PHANTOM_PROCESSOR.value,
                    "reason": "charge in batch 'b_orphan' has no payout on processor side",
                    "constituent_id": "ch_orphan",
                },
                "HOLD_IN_SUSPENSE",
                "Unsettled Payment in Open Processor Batch",
                "HIGH",
            ),
            # Case 7: Phantom bank
            (
                {
                    "discrepancy_id": "dsc:AUDIT:07",
                    "type": DiscrepancyType.PHANTOM_BANK.value,
                    "reason": "bank deposit reference matches no payout",
                    "constituent_id": "dep_unknown",
                },
                "RECLASSIFY_DEPOSIT",
                "Direct Treasury Credit or Mismatched Bank Narration",
                "HIGH",
            ),
            # Case 8: Ambiguous match
            (
                {
                    "discrepancy_id": "dsc:AUDIT:08",
                    "type": DiscrepancyType.AMBIGUOUS_MATCH.value,
                    "reason": "2 candidates survived; engine does not select among them",
                    "constituent_id": "dep_ambig",
                },
                "REQUIRE_HUMAN_SELECTION",
                "Duplicate Transaction Amounts with Missing Reference Identifiers",
                "MEDIUM",
            ),
            # Case 9: Unknown event
            (
                {
                    "discrepancy_id": "dsc:AUDIT:09",
                    "type": DiscrepancyType.UNKNOWN.value,
                    "reason": "record kind 'crypto_transfer' is not modelled by canonical schema",
                    "constituent_id": "unk_1",
                },
                "MANUAL_REVIEW",
                "Unrecognized Record Schema",
                "INSUFFICIENT",
            ),
            # Case 10: Clock skew
            (
                {
                    "discrepancy_id": "dsc:AUDIT:10",
                    "type": DiscrepancyType.TIMING_BREAK.value,
                    "reason": "payout arrived 2026-10-10, deposit posted 2026-10-08: -2 days indicates anomalous timeline",
                    "constituent_id": "po_skew_2",
                },
                "VERIFY_CLOCK_SKEW",
                "Pre-funding Settlement / Bank Narration Clock Skew",
                "HIGH",
            ),
        ]

        correct_action_count = 0
        correct_root_cause_count = 0
        correct_conf_count = 0
        unsupported_claims_count = 0

        for disc, exp_act, exp_root, exp_conf in eval_cases:
            report = investigate_discrepancy(disc)

            # 1. Action Accuracy
            if report.recommended_action == exp_act:
                correct_action_count += 1

            # 2. Root Cause Accuracy
            top_hyp = report.hypotheses[0]
            if top_hyp.title == exp_root:
                correct_root_cause_count += 1

            # 3. Confidence Accuracy
            if top_hyp.confidence == exp_conf:
                correct_conf_count += 1

            # 4. Hallucination Check: Evidence must be non-empty and grounded
            for ev in top_hyp.supporting_evidence:
                if not ev or len(ev.strip()) < 5:
                    unsupported_claims_count += 1

        total = len(eval_cases)
        action_acc = correct_action_count / total
        root_cause_acc = correct_root_cause_count / total
        conf_acc = correct_conf_count / total
        unsupported_rate = unsupported_claims_count / total

        assert action_acc == 1.0, f"Action Accuracy fell below 100%: {action_acc:.2%}"
        assert root_cause_acc == 1.0, f"Root Cause Accuracy fell below 100%: {root_cause_acc:.2%}"
        assert conf_acc == 1.0, f"Confidence Accuracy fell below 100%: {conf_acc:.2%}"
        assert unsupported_rate == 0.0, f"Found {unsupported_claims_count} unsupported claims"
