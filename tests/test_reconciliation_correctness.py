"""Regression tests for reconciliation correctness.

Tests the three-record synthetic dataset:
- REF-001: charge $100 + fee $10 = payout $90 (should match exactly)
- REF-002: charge $200 + fee $20 = payout $150 expected $180 ($30 short payment)
- REF-003: charge $300 + fee $30 = no payout (missing payout, PHANTOM_PROCESSOR)
"""

from __future__ import annotations

from settleiq.engine.discrepancy import DiscrepancyType
from settleiq.engine.reconcile import reconcile, RunParameters
from settleiq.money import Money

SYNTHETIC_RECORDS = [
    {"kind": "charge", "record": {
        "id": "chg-001", "amount": "100.00", "currency": "USD",
        "batch": "BATCH-001", "reference": "REF-001",
        "created": "2026-10-01", "narration": "Charge REF-001",
    }},
    {"kind": "fee", "record": {
        "id": "fee-001", "amount": "10.00", "currency": "USD",
        "batch": "BATCH-001", "reference": "REF-001",
        "created": "2026-10-01", "narration": "Fee REF-001",
    }},
    {"kind": "charge", "record": {
        "id": "chg-002", "amount": "200.00", "currency": "USD",
        "batch": "BATCH-001", "reference": "REF-002",
        "created": "2026-10-02", "narration": "Charge REF-002",
    }},
    {"kind": "fee", "record": {
        "id": "fee-002", "amount": "20.00", "currency": "USD",
        "batch": "BATCH-001", "reference": "REF-002",
        "created": "2026-10-02", "narration": "Fee REF-002",
    }},
    {"kind": "charge", "record": {
        "id": "chg-003", "amount": "300.00", "currency": "USD",
        "batch": "BATCH-002", "reference": "REF-003",
        "created": "2026-10-03", "narration": "Charge REF-003",
    }},
    {"kind": "fee", "record": {
        "id": "fee-003", "amount": "30.00", "currency": "USD",
        "batch": "BATCH-002", "reference": "REF-003",
        "created": "2026-10-03", "narration": "Fee REF-003",
    }},
    {"kind": "payout", "record": {
        "id": "pay-001", "amount": "90.00", "currency": "USD",
        "batch": "BATCH-001", "reference": "REF-001",
        "created": "2026-10-05", "narration": "Payout REF-001",
    }},
    {"kind": "payout", "record": {
        "id": "pay-002", "amount": "150.00", "currency": "USD",
        "batch": "BATCH-001", "reference": "REF-002",
        "created": "2026-10-06", "narration": "Payout REF-002 (short paid)",
    }},
]

PARAMETERS = RunParameters(
    window_start="2026-10-01",
    window_end="2026-10-31",
    settlement_window_days=3,
)


def test_ref001_matches_exactly():
    """REF-001: charge $100 - fee $10 = net $90 = payout $90 → closes exactly."""
    result = reconcile(SYNTHETIC_RECORDS, PARAMETERS)

    net_gross_breaks = [
        d for d in result.discrepancies
        if d.type == DiscrepancyType.NET_GROSS_BREAK
        and d.constituent_id == "pay-001"
    ]
    assert len(net_gross_breaks) == 0, (
        f"REF-001 should close exactly (100-10=90), "
        f"but got NET_GROSS_BREAK: {[d.reason for d in net_gross_breaks]}"
    )

    pay001_decomp = [d for d in result.decompositions if d.payout_id == "pay-001"]
    assert len(pay001_decomp) == 1, (
        f"Expected 1 decomposition for pay-001, got {len(pay001_decomp)}"
    )
    decomp = pay001_decomp[0]
    constituent_ids = {c.source_id for c in decomp.constituents}
    assert constituent_ids == {"chg-001", "fee-001"}, (
        f"pay-001 decomposition should only include REF-001 records, "
        f"got constituents: {constituent_ids}"
    )
    assert decomp.closes_exactly is True, (
        f"REF-001 should close exactly: gross={decomp.gross} fees={decomp.fees} "
        f"net_expected={decomp.net_expected} net_paid={decomp.net_paid}"
    )
    assert decomp.net_expected == Money("90.00", "USD"), (
        f"Expected net_expected $90.00, got {decomp.net_expected}"
    )
    assert decomp.residual.is_zero(), (
        f"Expected zero residual, got {decomp.residual}"
    )


def test_ref002_detects_short_payment():
    """REF-002: charge $200 - fee $20 = net $180 expected, payout paid $150 → $30 short."""
    result = reconcile(SYNTHETIC_RECORDS, PARAMETERS)

    net_gross_breaks = [
        d for d in result.discrepancies
        if d.type == DiscrepancyType.NET_GROSS_BREAK
        and d.constituent_id == "pay-002"
    ]
    assert len(net_gross_breaks) == 1, (
        f"REF-002 should have exactly 1 NET_GROSS_BREAK, got {len(net_gross_breaks)}: "
        f"{[(d.discrepancy_id, d.reason) for d in net_gross_breaks]}"
    )

    break_disc = net_gross_breaks[0]
    assert break_disc.severity.value == "HIGH", (
        f"NET_GROSS_BREAK should be HIGH severity, got {break_disc.severity}"
    )
    assert "30.00" in break_disc.reason or "$30" in break_disc.reason, (
        f"Reason should mention $30 shortfall, got: {break_disc.reason}"
    )

    pay002_decomp = [d for d in result.decompositions if d.payout_id == "pay-002"]
    assert len(pay002_decomp) == 1
    decomp = pay002_decomp[0]
    constituent_ids = {c.source_id for c in decomp.constituents}
    assert constituent_ids == {"chg-002", "fee-002"}, (
        f"pay-002 decomposition should only include REF-002 records, "
        f"got constituents: {constituent_ids}"
    )
    assert decomp.net_expected == Money("180.00", "USD"), (
        f"Expected net_expected $180.00, got {decomp.net_expected}"
    )
    assert decomp.net_paid == Money("150.00", "USD"), (
        f"Expected net_paid $150.00, got {decomp.net_paid}"
    )
    assert decomp.residual == Money("30.00", "USD"), (
        f"Expected residual $30.00, got {decomp.residual}"
    )
    assert decomp.closes_exactly is False


def test_ref003_detects_missing_payout():
    """REF-003: charge $300 + fee $30 → no payout → PHANTOM_PROCESSOR for each."""
    result = reconcile(SYNTHETIC_RECORDS, PARAMETERS)

    phantom_chg = [
        d for d in result.discrepancies
        if d.type == DiscrepancyType.PHANTOM_PROCESSOR
        and d.constituent_id == "chg-003"
    ]
    assert len(phantom_chg) == 1, (
        f"chg-003 should be PHANTOM_PROCESSOR, got: "
        f"{[(d.discrepancy_id, d.type.value, d.constituent_id) for d in phantom_chg]}"
    )
    assert phantom_chg[0].severity.value == "HIGH"
    assert phantom_chg[0].constituent_kind == "charge"

    phantom_fee = [
        d for d in result.discrepancies
        if d.type == DiscrepancyType.PHANTOM_PROCESSOR
        and d.constituent_id == "fee-003"
    ]
    assert len(phantom_fee) == 1, (
        f"fee-003 should be PHANTOM_PROCESSOR, got: "
        f"{[(d.discrepancy_id, d.type.value, d.constituent_id) for d in phantom_fee]}"
    )
    assert phantom_fee[0].severity.value == "HIGH"
    assert phantom_fee[0].constituent_kind == "fee"

    assert "BATCH-002" in phantom_chg[0].reason, (
        f"Reason should mention BATCH-002, got: {phantom_chg[0].reason}"
    )


def test_reconciliation_rate_formula():
    """Verify the auto-match rate formula and denominator definition."""
    result = reconcile(SYNTHETIC_RECORDS, PARAMETERS)
    counts = result.counts

    eligible = counts["eligible"]
    deterministic = counts["deterministic"]

    if eligible > 0:
        expected_rate = deterministic / eligible
    else:
        expected_rate = 0.0

    assert counts["rate"] == expected_rate, (
        f"Rate {counts['rate']} != {deterministic}/{eligible} = {expected_rate}"
    )


def test_discrepancy_mapping_preserves_source_records():
    """Each discrepancy must map to its actual source record, not a batch aggregate."""
    result = reconcile(SYNTHETIC_RECORDS, PARAMETERS)

    input_ids = {r["record"]["id"] for r in SYNTHETIC_RECORDS}
    for d in result.discrepancies:
        assert d.constituent_id in input_ids, (
            f"Discrepancy {d.discrepancy_id} maps to constituent_id={d.constituent_id} "
            f"which is not an input record ID. Valid IDs: {input_ids}"
        )
        if d.type in (DiscrepancyType.PHANTOM_PROCESSOR, DiscrepancyType.PHANTOM_BANK):
            assert len(d.contributing_records) >= 1, (
                f"{d.type.value} for {d.constituent_id} has no contributing records"
            )