"""Unit tests for exact monetary arithmetic.

Every test cites the acceptance criterion it satisfies. AC-1.01…AC-2.04 map to
SETTLEIQ-M1-001 §4.
"""

from __future__ import annotations

import decimal
from decimal import Decimal

import pytest

from settleiq.money import (
    CurrencyCode,
    CurrencyMismatch,
    CurrencyNotSupported,
    CurrencyPrecisionExceeded,
    FloatProhibited,
    Money,
    get_context,
)


# AC-1.01 — immutable, explicit currency, rejects binary float.
def test_rejects_float_construction() -> None:
    with pytest.raises(FloatProhibited):
        Money(10.5, "USD")


def test_rejects_float_from_json_parse() -> None:
    import json

    payload = json.loads('{"amount": 10.5}')
    with pytest.raises(FloatProhibited):
        Money(payload["amount"], "USD")


def test_immutable() -> None:
    money = Money("10.00", "USD")
    with pytest.raises(AttributeError):
        money._amount = Decimal("20.00")  # type: ignore[misc]


def test_trailing_zeros_equal_but_distinct_text() -> None:
    assert Money("10.5", "USD") == Money("10.50", "USD")


def test_declared_context_is_not_the_ambient_default() -> None:
    import decimal as _d

    assert get_context() is not _d.getcontext()
    assert get_context().prec == 60
    assert get_context().rounding == _d.ROUND_HALF_UP
    assert _d.InvalidOperation in get_context().traps


# AC-1.03 — mixed-currency arithmetic raises rather than converting.
def test_mixed_currency_addition_raises() -> None:
    with pytest.raises(CurrencyMismatch):
        Money("1", "USD") + Money("1", "EUR")


def test_mixed_currency_comparison_raises() -> None:
    with pytest.raises(CurrencyMismatch):
        Money("1", "USD") < Money("1", "EUR")


# AC-2.01…AC-2.03 — currency exponent validation, raise not round.
def test_jpy_rejects_fractional() -> None:
    with pytest.raises(CurrencyPrecisionExceeded):
        Money("100.5", "JPY")


def test_usd_rejects_three_places() -> None:
    with pytest.raises(CurrencyPrecisionExceeded):
        Money("1043.275", "USD")


def test_bhd_accepts_three_places() -> None:
    assert Money("1043.275", "BHD").amount == Decimal("1043.275")


# AC-2.04 — unknown currency never defaults to 2.
def test_unknown_currency_raises() -> None:
    with pytest.raises(CurrencyNotSupported):
        Money("10.00", "XYZ")


def test_currency_parse_normalises_case() -> None:
    assert CurrencyCode.parse("usd") is CurrencyCode.USD


def test_exponents_are_declared() -> None:
    assert CurrencyCode.JPY.exponent == 0
    assert CurrencyCode.USD.exponent == 2
    assert CurrencyCode.BHD.exponent == 3


# AC-1.02 — arithmetic is exact under the declared context.
def test_large_sum_is_exact() -> None:
    values = [Money("0.01", "USD") for _ in range(1000)]
    total = values[0]
    for value in values[1:]:
        total = total + value
    assert total.amount == Decimal("10.00")


def test_canonical_round_trip_is_exact() -> None:
    for text in ("0", "1043.27", "-3.50", "1000000000.99"):
        money = Money(text, "USD")
        assert Money.from_canonical(money.to_canonical(), "USD") == money


def test_canonical_round_trip_jpy_and_bhd() -> None:
    for text, code in (("100", "JPY"), ("1043.275", "BHD"), ("0", "JPY")):
        money = Money(text, code)
        assert Money.from_canonical(money.to_canonical(), code) == money


# `16` §B.2 — a non-terminating quotient raises; the remainder must be explicit.
def test_non_terminating_division_raises() -> None:
    with pytest.raises(decimal.InvalidOperation):
        Money("1.00", "USD").divide("3")


def test_terminating_division_succeeds() -> None:
    assert Money("1.00", "USD").divide("4").amount == Decimal("0.25")


def test_allocate_non_terminating_raises() -> None:
    # 1.00 split three ways does not terminate. The engine must refuse rather
    # than distribute a 0.003333... approximation (`16` §B.2).
    with pytest.raises(decimal.InvalidOperation):
        Money("1.00", "USD").allocate([1, 1, 1])


def test_allocate_terminating_keeps_residual_explicit() -> None:
    parts = Money("10.00", "USD").allocate([7, 3])
    assert len(parts) == 3
    assert parts[0].amount == Decimal("7.00")
    assert parts[1].amount == Decimal("3.00")
    assert parts[2].amount == Decimal("0.00")


def test_allocation_invariant_holds() -> None:
    parts = Money("10.00", "USD").allocate([2, 3])
    assert parts[0].amount == Decimal("4.00")
    assert parts[1].amount == Decimal("6.00")
    assert parts[2].amount == Decimal("0.00")


def test_multiply_returns_computation_value_requiring_rounding() -> None:
    # 1043.27 * 0.029 = 30.25483. This is a legitimate intermediate, not a
    # persisted amount, so it is representable but flagged for rounding.
    product = Money("1043.27", "USD").multiply("0.029")
    assert product.amount == Decimal("30.25483")
    assert product.requires_rounding


def test_unrounded_value_cannot_be_persisted() -> None:
    product = Money("1043.27", "USD").multiply("0.029")
    with pytest.raises(CurrencyPrecisionExceeded):
        product.to_canonical()


def test_rounded_applies_the_declared_mode_explicitly() -> None:
    rounded = Money("1043.27", "USD").multiply("0.029").rounded()
    assert rounded.code == "USD"
    assert rounded.amount == Decimal("30.25")
    assert not rounded.requires_rounding


def test_rounded_usd_half_up() -> None:
    rounded = Money("10.00", "USD").multiply("1.0005").rounded()
    assert rounded.amount == Decimal("10.01")


def test_multiply_within_precision_is_exact() -> None:
    product = Money("100.00", "USD").multiply("0.10")
    assert product.amount == Decimal("10.0000")
    assert not product.requires_rounding
    assert product.to_canonical() == "10.0000|USD"


def test_trailing_zeros_are_not_precision_loss() -> None:
    # 10.0000 is exactly 10.00 and must be accepted at ingest.
    assert Money("10.0000", "USD").amount == Decimal("10.0000")
    assert not Money("10.0000", "USD").requires_rounding


def test_division_by_zero_raises() -> None:
    with pytest.raises(ZeroDivisionError):
        Money("1.00", "USD").divide("0")


def test_multiply_rejects_float() -> None:
    with pytest.raises(FloatProhibited):
        Money("1.00", "USD").multiply(1.5)


def test_multiply_is_exact() -> None:
    assert Money("1043.27", "USD").multiply("0.029").amount == Decimal("30.25483")


def test_negative_and_refund_representation() -> None:
    refund = Money("-3.00", "USD")
    assert refund.is_negative()
    assert (-refund).amount == Decimal("3.00")
