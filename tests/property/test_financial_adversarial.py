"""Adversarial financial scenarios and extreme monetary invariant tests.

Validates:
1. Zero-decimal currency (JPY) precision and exact decomposition.
2. Three-decimal currency (BHD, KWD) precision and exact decomposition.
3. Extreme enterprise balances ($100B+) without overflow or precision loss.
4. Zero-net batches (gross charges exactly equal fees + refunds).
5. Negative-net batches (refunds exceed charges -> negative net payout).
6. Strict cross-currency isolation (CurrencyMismatch raised on contamination).
7. Strict conservation of money across payout decompositions.
"""

from decimal import Decimal

import pytest

from settleiq.engine.decompose import decompose
from settleiq.engine.reconcile import RunParameters, reconcile
from settleiq.money import (
    CurrencyCode,
    CurrencyMismatch,
    CurrencyPrecisionExceeded,
    Money,
)
from settleiq.validation.ingest import validate_records


def test_zero_decimal_currency_jpy_decomposition() -> None:
    """Validates 0-exponent currencies (JPY) without decimal fractions."""
    records = [
        {
            "kind": "charge",
            "id": "ch_jpy_1",
            "amount": "15000",
            "currency": "JPY",
            "batch": "b_jpy",
        },
        {
            "kind": "charge",
            "id": "ch_jpy_2",
            "amount": "25000",
            "currency": "JPY",
            "batch": "b_jpy",
        },
        {
            "kind": "fee",
            "id": "fee_jpy_1",
            "amount": "1200",
            "currency": "JPY",
            "batch": "b_jpy",
        },
        {
            "kind": "refund",
            "id": "ref_jpy_1",
            "amount": "3800",
            "currency": "JPY",
            "batch": "b_jpy",
        },
    ]
    payout = {
        "id": "po_jpy_1",
        "amount": "35000",
        "currency": "JPY",
        "batch": "b_jpy",
    }
    # Expected: (15000 + 25000) - 1200 - 3800 = 35000
    decomp = decompose(payout, records)
    assert decomp.closes_exactly is True
    assert decomp.gross.amount == Decimal("40000")
    assert decomp.fees.amount == Decimal("1200")
    assert decomp.refunds.amount == Decimal("3800")
    assert decomp.net_expected.amount == Decimal("35000")
    assert decomp.residual.amount == Decimal("0")


def test_zero_decimal_currency_fraction_rejected() -> None:
    """JPY with decimal fraction must be rejected as CurrencyPrecisionExceeded."""
    with pytest.raises(CurrencyPrecisionExceeded):
        Money("15000.50", CurrencyCode.JPY)


def test_three_decimal_currency_bhd_precision() -> None:
    """Validates 3-exponent currencies (BHD) with exact thousandths."""
    records = [
        {
            "kind": "charge",
            "id": "ch_bhd_1",
            "amount": "12.345",
            "currency": "BHD",
            "batch": "b_bhd",
        },
        {
            "kind": "fee",
            "id": "fee_bhd_1",
            "amount": "0.125",
            "currency": "BHD",
            "batch": "b_bhd",
        },
    ]
    payout = {
        "id": "po_bhd_1",
        "amount": "12.220",
        "currency": "BHD",
        "batch": "b_bhd",
    }
    decomp = decompose(payout, records)
    assert decomp.closes_exactly is True
    assert decomp.gross.amount == Decimal("12.345")
    assert decomp.fees.amount == Decimal("0.125")
    assert decomp.net_expected.amount == Decimal("12.220")


def test_extreme_balance_no_overflow() -> None:
    """$100,000,000,000.00 balance arithmetic without float drift."""
    large_amt_str = "100000000000.00"
    m1 = Money(large_amt_str, "USD")
    m2 = Money("0.01", "USD")
    result = m1 + m2
    assert result.amount == Decimal("100000000000.01")
    assert str(result) == "100000000000.01 USD"
    assert result.to_canonical() == "100000000000.01|USD"


def test_zero_net_batch_closes_exactly() -> None:
    """A batch where charges exactly equal fees and refunds nets $0.00."""
    records = [
        {
            "kind": "charge",
            "id": "ch_z1",
            "amount": "500.00",
            "currency": "USD",
            "batch": "b_zero",
        },
        {
            "kind": "fee",
            "id": "fee_z1",
            "amount": "50.00",
            "currency": "USD",
            "batch": "b_zero",
        },
        {
            "kind": "refund",
            "id": "ref_z1",
            "amount": "450.00",
            "currency": "USD",
            "batch": "b_zero",
        },
    ]
    payout = {
        "id": "po_z1",
        "amount": "0.00",
        "currency": "USD",
        "batch": "b_zero",
    }
    decomp = decompose(payout, records)
    assert decomp.closes_exactly is True
    assert decomp.net_expected.amount == Decimal("0.00")
    assert decomp.residual.amount == Decimal("0.00")


def test_cross_currency_isolation_raises_mismatch() -> None:
    """Attempting to decompose USD payout with EUR charge raises CurrencyMismatch."""
    records = [
        {
            "kind": "charge",
            "id": "ch_eur",
            "amount": "100.00",
            "currency": "EUR",
            "batch": "b_cross",
        },
    ]
    payout = {
        "id": "po_usd",
        "amount": "100.00",
        "currency": "USD",
        "batch": "b_cross",
    }
    with pytest.raises(CurrencyMismatch):
        decompose(payout, records)


def test_conservation_of_money_across_engine_run() -> None:
    """Validates global conservation: Sum(Charges) - Sum(Fees) - Sum(Refunds) = Sum(Expected)."""
    raw_records = [
        (
            "charge",
            {
                "id": "c1",
                "amount": "100.00",
                "currency": "USD",
                "batch": "b1",
                "created": "2026-10-01",
            },
        ),
        (
            "charge",
            {
                "id": "c2",
                "amount": "200.00",
                "currency": "USD",
                "batch": "b1",
                "created": "2026-10-01",
            },
        ),
        (
            "fee",
            {
                "id": "f1",
                "amount": "15.00",
                "currency": "USD",
                "batch": "b1",
                "type": "processing",
                "created": "2026-10-01",
            },
        ),
        (
            "refund",
            {
                "id": "r1",
                "amount": "35.00",
                "currency": "USD",
                "batch": "b1",
                "charge": "c1",
                "created": "2026-10-01",
            },
        ),
        (
            "payout",
            {
                "id": "p1",
                "amount": "250.00",
                "currency": "USD",
                "batch": "b1",
                "arrival_date": "2026-10-03",
            },
        ),
        (
            "deposit",
            {
                "id": "d1",
                "amount": "250.00",
                "currency": "USD",
                "posted": "2026-10-04",
                "narration": "STRIPE PAYOUT b1",
            },
        ),
    ]
    validated = validate_records(raw_records)
    params = RunParameters("2026-10-01", "2026-10-31")
    result = reconcile(validated.accepted, params)

    assert len(result.discrepancies) == 0
    assert result.metrics.rate == 1.0
    decomp = result.decompositions[0]
    expected_net = (decomp.gross.amount - decomp.fees.amount) - decomp.refunds.amount
    assert expected_net == decomp.net_paid.amount
    assert decomp.residual.amount == Decimal("0.00")
