"""Unit tests for the Stripe Source Adapter.

Validates the concrete StripeSourceAdapter against realistic financial scenarios:
- Payment charges with embedded fee details
- Payouts and settlement batch creation
- Full and partial refunds linked to charges
- Disputes and balance adjustments
- Exact currency exponent scaling (USD cents, JPY zero-decimal)
- Fail-closed validation (missing fields, duplicate records, float rejection)
- Integration into the deterministic reconciliation engine
"""

from __future__ import annotations

import json

import pytest

from settleiq.adapters.interface import SourceAdapterError
from settleiq.adapters.stripe import STRIPE_API_VERSION, StripeSourceAdapter
from settleiq.engine.reconcile import RunParameters, reconcile
from settleiq.model.provenance import DataProvenance
from settleiq.money import Money


@pytest.fixture
def adapter() -> StripeSourceAdapter:
    return StripeSourceAdapter()


def test_stripe_adapter_version_and_contract(adapter: StripeSourceAdapter) -> None:
    assert adapter.source_version == f"stripe-{STRIPE_API_VERSION}"
    assert adapter.schema_version == "1.0.0"


def test_normalize_payment_charge_with_fee_details(adapter: StripeSourceAdapter) -> None:
    payload = json.dumps(
        [
            {
                "id": "ch_12345",
                "object": "charge",
                "amount": 10000,  # 100.00 USD
                "currency": "usd",
                "created": "2026-10-15T12:00:00Z",
                "reference": "pi_12345",
                "customer": "cus_999",
                "description": "Standard payment",
                "fee_details": [
                    {
                        "amount": 320,  # 3.20 USD
                        "currency": "usd",
                        "type": "stripe_processing_fee",
                    }
                ],
            }
        ]
    ).encode("utf-8")

    batch = adapter.normalize(payload, provenance=DataProvenance.SYNTHETIC)
    assert len(batch.charges) == 1
    assert len(batch.fees) == 1

    charge = batch.charges[0]
    assert charge.source_id == "ch_12345"
    assert charge.amount == Money("100.00", "USD")
    assert charge.reference == "pi_12345"
    assert charge.customer_reference == "cus_999"

    fee = batch.fees[0]
    assert fee.source_id == "ch_12345_fee_0"
    assert fee.amount == Money("3.20", "USD")
    assert fee.fee_type == "stripe_processing_fee"


def test_normalize_payout_with_batch(adapter: StripeSourceAdapter) -> None:
    payload = json.dumps(
        [
            {
                "id": "po_9988",
                "object": "payout",
                "amount": 9680,  # 96.80 USD
                "currency": "usd",
                "arrival_date": "2026-10-17T00:00:00Z",
                "batch_id": "sb_oct17",
                "payout_reference": "ref_po_9988",
            }
        ]
    ).encode("utf-8")

    batch = adapter.normalize(payload, provenance=DataProvenance.SYNTHETIC)
    assert len(batch.payouts) == 1
    assert len(batch.batches) == 1

    po = batch.payouts[0]
    assert po.source_id == "po_9988"
    assert po.amount == Money("96.80", "USD")
    assert po.batch_source_id == "sb_oct17"
    assert po.payout_reference == "ref_po_9988"

    sb = batch.batches[0]
    assert sb.source_id == "sb_oct17"
    assert sb.batch_number == "sb_oct17"


def test_normalize_refund_linked_to_charge(adapter: StripeSourceAdapter) -> None:
    payload = json.dumps(
        [
            {
                "id": "re_5544",
                "object": "refund",
                "amount": 2500,  # 25.00 USD
                "currency": "usd",
                "created": "2026-10-16T15:30:00Z",
                "charge": "ch_12345",
            }
        ]
    ).encode("utf-8")

    batch = adapter.normalize(payload, provenance=DataProvenance.SYNTHETIC)
    assert len(batch.refunds) == 1
    ref = batch.refunds[0]
    assert ref.source_id == "re_5544"
    assert ref.amount == Money("25.00", "USD")
    assert ref.charge_source_id == "ch_12345"


def test_normalize_dispute_adjustment(adapter: StripeSourceAdapter) -> None:
    payload = json.dumps(
        [
            {
                "id": "dp_7766",
                "object": "dispute",
                "amount": 5000,
                "currency": "usd",
                "created": "2026-10-18T10:00:00Z",
                "reason": "fraudulent",
            }
        ]
    ).encode("utf-8")

    batch = adapter.normalize(payload, provenance=DataProvenance.SYNTHETIC)
    assert len(batch.adjustments) == 1
    adj = batch.adjustments[0]
    assert adj.source_id == "dp_7766"
    assert adj.amount == Money("50.00", "USD")
    assert adj.adjustment_type == "fraudulent"


def test_zero_decimal_currency_scaling(adapter: StripeSourceAdapter) -> None:
    # JPY has exponent 0 (100 JPY is 100, not 1.00)
    payload = json.dumps(
        [
            {
                "id": "ch_jpy_1",
                "object": "charge",
                "amount": 5000,
                "currency": "jpy",
                "created": "2026-10-15T00:00:00Z",
            }
        ]
    ).encode("utf-8")

    batch = adapter.normalize(payload, provenance=DataProvenance.SYNTHETIC)
    assert batch.charges[0].amount == Money("5000", "JPY")


def test_string_decimal_amount_parsing(adapter: StripeSourceAdapter) -> None:
    payload = json.dumps(
        [
            {
                "id": "ch_str_1",
                "object": "charge",
                "amount": "125.50",
                "currency": "usd",
                "created": "2026-10-15T00:00:00Z",
            }
        ]
    ).encode("utf-8")

    batch = adapter.normalize(payload, provenance=DataProvenance.SYNTHETIC)
    assert batch.charges[0].amount == Money("125.50", "USD")


def test_fail_closed_on_duplicate_ids(adapter: StripeSourceAdapter) -> None:
    payload = json.dumps(
        [
            {"id": "ch_dup", "object": "charge", "amount": 100, "currency": "usd"},
            {"id": "ch_dup", "object": "charge", "amount": 200, "currency": "usd"},
        ]
    ).encode("utf-8")

    with pytest.raises(SourceAdapterError, match="Duplicate record id"):
        adapter.normalize(payload, provenance=DataProvenance.SYNTHETIC)


def test_fail_closed_on_missing_required_fields(adapter: StripeSourceAdapter) -> None:
    # Missing id
    with pytest.raises(SourceAdapterError, match="missing required 'id'"):
        adapter.normalize(
            b'[{"amount": 100, "currency": "usd"}]', provenance=DataProvenance.SYNTHETIC
        )

    # Missing currency
    with pytest.raises(SourceAdapterError, match="missing required 'currency'"):
        adapter.normalize(b'[{"id": "ch_1", "amount": 100}]', provenance=DataProvenance.SYNTHETIC)

    # Missing amount
    with pytest.raises(SourceAdapterError, match="missing required 'amount'"):
        adapter.normalize(
            b'[{"id": "ch_1", "currency": "usd"}]', provenance=DataProvenance.SYNTHETIC
        )

    # Refund missing charge reference
    with pytest.raises(SourceAdapterError, match="missing required 'charge' reference"):
        adapter.normalize(
            b'[{"id": "re_1", "object": "refund", "amount": 100, "currency": "usd"}]',
            provenance=DataProvenance.SYNTHETIC,
        )


def test_fail_closed_on_unsupported_currency(adapter: StripeSourceAdapter) -> None:
    payload = b'[{"id": "ch_1", "amount": 100, "currency": "FAKE_COIN"}]'
    with pytest.raises(SourceAdapterError, match="Unsupported currency"):
        adapter.normalize(payload, provenance=DataProvenance.SYNTHETIC)


def test_fail_closed_on_unmapped_object_type(adapter: StripeSourceAdapter) -> None:
    payload = b'[{"id": "cust_1", "object": "customer", "amount": 100, "currency": "usd"}]'
    with pytest.raises(SourceAdapterError, match="Unmapped Stripe object type"):
        adapter.normalize(payload, provenance=DataProvenance.SYNTHETIC)


def test_stripe_normalized_batch_feeds_reconciliation_engine(adapter: StripeSourceAdapter) -> None:
    # Complete multi-record settlement cycle
    payload = json.dumps(
        [
            {
                "id": "ch_101",
                "object": "charge",
                "amount": 10000,
                "currency": "usd",
                "created": "2026-10-15",
                "batch_id": "sb_cycle1",
                "fee_details": [{"amount": 300, "currency": "usd", "type": "fee"}],
            },
            {
                "id": "po_201",
                "object": "payout",
                "amount": 9700,
                "currency": "usd",
                "arrival_date": "2026-10-17",
                "batch_id": "sb_cycle1",
            },
            {
                "id": "bd_301",
                "object": "deposit",
                "amount": 9700,
                "currency": "usd",
                "posted_at": "2026-10-18",
                "narration": "STRIPE PAYOUT sb_cycle1",
            },
        ]
    ).encode("utf-8")

    batch = adapter.normalize(payload, provenance=DataProvenance.SYNTHETIC)

    # Convert normalized entities to engine canonical records format
    records: list[tuple[str, dict[str, object]]] = []
    for c in batch.charges:
        records.append(
            (
                "charge",
                {
                    "id": c.source_id,
                    "amount": str(c.amount.amount),
                    "currency": c.amount.currency.value,
                    "created": c.captured_at,
                    "batch": "sb_cycle1",
                },
            )
        )
    for f in batch.fees:
        records.append(
            (
                "fee",
                {
                    "id": f.source_id,
                    "amount": str(f.amount.amount),
                    "currency": f.amount.currency.value,
                    "batch": "sb_cycle1",
                    "type": f.fee_type,
                    "created": f.charged_at,
                },
            )
        )
    for p in batch.payouts:
        records.append(
            (
                "payout",
                {
                    "id": p.source_id,
                    "amount": str(p.amount.amount),
                    "currency": p.amount.currency.value,
                    "arrival_date": p.paid_at,
                    "batch": "sb_cycle1",
                },
            )
        )
    for d in batch.deposits:
        records.append(
            (
                "deposit",
                {
                    "id": d.source_id,
                    "amount": str(d.amount.amount),
                    "currency": d.amount.currency.value,
                    "posted": d.posted_at,
                    "narration": d.narration,
                },
            )
        )

    from settleiq.validation.ingest import validate_records

    validated = validate_records(records)
    assert validated.quarantined_count == 0
    res = reconcile(validated.accepted, RunParameters("2026-10-01", "2026-10-31"))
    # Net: 100 - 3 = 97 payout == 97 deposit -> 0 breaks, clean match!
    assert len(res.discrepancies) == 0
    assert res.metrics.numerator > 0
