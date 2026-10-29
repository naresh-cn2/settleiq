"""Unit tests for the autonomous discrepancy investigator and transaction trace engine."""

from decimal import Decimal

from fastapi.testclient import TestClient

from settleiq.api.app import app
from settleiq.engine.discrepancy import DiscrepancyType
from settleiq.engine.investigator import (
    build_transaction_trace,
    investigate_discrepancy,
)


def test_investigate_net_gross_break() -> None:
    discrepancy = {
        "discrepancy_id": "disc_ng_01",
        "type": DiscrepancyType.NET_GROSS_BREAK.value,
        "severity": "HIGH",
        "constituent_id": "po_batch_42",
        "status": "OPEN",
        "reason": (
            "batch 'po_batch_42' nets 100.00|USD but the payout paid 96.00|USD; "
            "residual 4.00|USD"
        ),
    }
    report = investigate_discrepancy(discrepancy)
    assert report.discrepancy_id == "disc_ng_01"
    assert report.recommended_action == "ADJUST_FEE"
    assert len(report.hypotheses) == 2
    assert report.hypotheses[0].rank == 1
    assert "Processor Interchange Fee" in report.hypotheses[0].title
    assert report.hypotheses[0].confidence == "HIGH"
    assert any("po_batch_42" in ev for ev in report.hypotheses[0].supporting_evidence)

    canonical = report.to_canonical()
    assert canonical["recommended_action"] == "ADJUST_FEE"
    assert canonical["draft_resolution"]["action"] == "ADJUST_FEE"
    assert "trace" in canonical
    assert len(canonical["trace"]["nodes"]) == 3


def test_investigate_amount_break() -> None:
    discrepancy = {
        "discrepancy_id": "disc_ab_01",
        "type": DiscrepancyType.AMOUNT_BREAK.value,
        "severity": "MEDIUM",
        "constituent_id": "po_99",
        "status": "OPEN",
        "reason": "payout paid 80.00|USD but deposit posted 78.50|USD",
    }
    report = investigate_discrepancy(discrepancy)
    assert report.recommended_action == "ACCEPT_TOLERANCE"
    assert report.hypotheses[0].rank == 1
    assert "Wire Clearing Fee" in report.hypotheses[0].title
    assert report.draft_resolution["action"] == "ACCEPT_TOLERANCE"


def test_investigate_timing_break() -> None:
    discrepancy = {
        "discrepancy_id": "disc_tb_01",
        "type": DiscrepancyType.TIMING_BREAK.value,
        "severity": "LOW",
        "constituent_id": "po_timing",
        "status": "OPEN",
        "reason": "payout arrived 2026-10-08, deposit posted 2026-10-20: 12 days exceeds window",
    }
    report = investigate_discrepancy(discrepancy)
    assert report.recommended_action == "ACCEPT_LAG"
    assert "Clearing Lag" in report.hypotheses[0].title
    assert report.draft_resolution["action"] == "ACCEPT_LAG"


def test_investigate_phantom_processor() -> None:
    discrepancy = {
        "discrepancy_id": "disc_pp_01",
        "type": DiscrepancyType.PHANTOM_PROCESSOR.value,
        "severity": "MEDIUM",
        "constituent_id": "ch_orphan",
        "status": "OPEN",
        "reason": "charge ch_orphan was never associated with a payout",
    }
    report = investigate_discrepancy(discrepancy)
    assert report.recommended_action == "HOLD_IN_SUSPENSE"
    assert report.hypotheses[0].confidence == "HIGH"
    assert report.draft_resolution["action"] == "HOLD_IN_SUSPENSE"


def test_investigate_phantom_bank() -> None:
    discrepancy = {
        "discrepancy_id": "disc_pb_01",
        "type": DiscrepancyType.PHANTOM_BANK.value,
        "severity": "HIGH",
        "constituent_id": "dep_unknown",
        "status": "OPEN",
        "reason": "deposit dep_unknown matches no known payout",
    }
    report = investigate_discrepancy(discrepancy)
    assert report.recommended_action == "RECLASSIFY_DEPOSIT"
    assert report.hypotheses[0].confidence == "HIGH"
    assert report.draft_resolution["action"] == "RECLASSIFY_DEPOSIT"


def test_investigate_ambiguous_match() -> None:
    discrepancy = {
        "discrepancy_id": "disc_am_01",
        "type": DiscrepancyType.AMBIGUOUS_MATCH.value,
        "severity": "HIGH",
        "constituent_id": "dep_ambiguous",
        "status": "OPEN",
        "reason": "deposit dep_ambiguous matches 2 candidates: po_1, po_2",
    }
    report = investigate_discrepancy(discrepancy)
    assert report.recommended_action == "REQUIRE_HUMAN_SELECTION"
    assert report.draft_resolution["action"] == "MANUAL_MATCH"


def test_reconstruct_trace_with_explicit_records() -> None:
    records = [
        {"kind": "charge", "id": "ch_1", "amount": "100.00", "currency": "USD", "batch": "b1"},
        {"kind": "charge", "id": "ch_2", "amount": "50.00", "currency": "USD", "batch": "b1"},
        {"kind": "fee", "id": "fee_1", "amount": "4.50", "currency": "USD", "batch": "b1"},
        {"kind": "refund", "id": "ref_1", "amount": "10.00", "currency": "USD", "batch": "b1"},
        {"kind": "payout", "id": "po_1", "amount": "135.50", "currency": "USD", "reference": "b1"},
        {
            "kind": "deposit",
            "id": "dep_1",
            "amount": "135.50",
            "currency": "USD",
            "reference": "b1",
        },
    ]
    discrepancy = {
        "discrepancy_id": "disc_test",
        "type": "NONE",
        "constituent_id": "po_1",
    }
    trace = build_transaction_trace(discrepancy, records=records)
    assert Decimal(trace.gross_amount) == Decimal("150.00")
    assert Decimal(trace.fee_amount) == Decimal("4.50")
    assert Decimal(trace.refund_amount) == Decimal("10.00")
    assert Decimal(trace.net_expected) == Decimal("135.50")
    assert Decimal(trace.net_paid) == Decimal("135.50")
    assert Decimal(trace.bank_deposited) == Decimal("135.50")
    assert Decimal(trace.residual) == Decimal("0.00")
    assert trace.is_closed is True
    assert len(trace.nodes) == 6


def test_api_investigate_and_trace_endpoints(monkeypatch) -> None:
    monkeypatch.setenv("SETTLEIQ_API_TOKEN", "test-token")
    client = TestClient(app)
    headers = {"Authorization": "Bearer test-token"}

    # Test seed demo run
    seed_resp = client.post("/v1/demo/seed", headers=headers)
    assert seed_resp.status_code == 201
    seed_data = seed_resp.json()
    assert seed_data["status"] == "seeded"
    run_id = seed_data["run_id"]
    assert seed_data["discrepancy_count"] > 0

    # Retrieve discrepancies for seeded run
    disc_resp = client.get(f"/v1/runs/{run_id}/discrepancies", headers=headers)
    assert disc_resp.status_code == 200
    discrepancies = disc_resp.json()["discrepancies"]
    assert len(discrepancies) > 0
    first_disc = discrepancies[0]
    disc_id = first_disc["discrepancy_id"]

    # Test autonomous AI investigation endpoint
    inv_resp = client.get(f"/v1/discrepancies/{disc_id}/investigate", headers=headers)
    assert inv_resp.status_code == 200
    inv_data = inv_resp.json()
    assert inv_data["discrepancy_id"] == disc_id
    assert "hypotheses" in inv_data
    assert len(inv_data["hypotheses"]) > 0
    assert "trace" in inv_data
    assert "draft_resolution" in inv_data

    # Test constituent trace endpoint
    cid = first_disc["constituent_id"]
    trace_resp = client.get(f"/v1/runs/{run_id}/trace/{cid}", headers=headers)
    assert trace_resp.status_code == 200
    trace_data = trace_resp.json()
    assert "nodes" in trace_data
    assert "net_expected" in trace_data
