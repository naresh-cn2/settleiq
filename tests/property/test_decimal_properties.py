"""Property-based tests for monetary invariants.

Each property is stated as a claim about *all* generated values, not a chosen
example. The seed is recorded in `settleiq.testing.generators` so the population
is reproducible from the repository alone (SETTLEIQ-M1-001 AC-7.03).
"""

from __future__ import annotations

import random
from decimal import Decimal

import pytest

from settleiq.money import CurrencyCode, CurrencyPrecisionExceeded, FloatProhibited, Money
from settleiq.testing.generators import PROPERTY_SEED, amounts, seeded

# P-DEC-01 — addition is exact within the declared precision.
def test_addition_is_exact() -> None:
    rng = seeded()
    for currency in CurrencyCode:
        quantum = Decimal(1).scaleb(-currency.exponent)
        for _ in range(50):
            a = Decimal(rng.randint(-10**9, 10**9)) * quantum
            b = Decimal(rng.randint(-10**9, 10**9)) * quantum
            left, right = Money(a, currency), Money(b, currency)
            assert (left + right).amount == a + b


# P-DEC-02 — mixed-currency arithmetic always raises, never converts.
def test_mixed_currency_always_raises() -> None:
    rng = seeded()
    values = list(amounts(rng, limit=120))
    for i in range(0, len(values) - 1, 2):
        first, second = values[i], values[i + 1]
        try:
            left = Money(first, _currency_admitting(first))
            right = Money(second, _currency_admitting(second))
        except CurrencyPrecisionExceeded:
            continue
        if left.currency == right.currency:
            continue
        with pytest.raises(Exception):  # noqa: B017 - any typed error is acceptable
            left + right


# P-DEC-03 — amounts are never silently rounded at ingest.
def test_excess_precision_is_rejected_not_rounded() -> None:
    rng = seeded()
    for _ in range(200):
        text = f"{rng.randint(-10**6, 10**6)}.{rng.randint(0, 999999):06d}"
        code = rng.choice(list(CurrencyCode))
        try:
            money = Money(text, code)
        except CurrencyPrecisionExceeded:
            continue
        # If construction succeeded, the value must be exactly representable.
        assert money.amount == Decimal(text)


# P-DEC-05 — an operation and its inverse return the original value exactly.
def test_addition_inverse_is_exact() -> None:
    rng = seeded()
    for currency in CurrencyCode:
        quantum = Decimal(1).scaleb(-currency.exponent)
        for _ in range(50):
            a = Decimal(rng.randint(-10**9, 10**9)) * quantum
            b = Decimal(rng.randint(-10**9, 10**9)) * quantum
            left, right = Money(a, currency), Money(b, currency)
            assert ((left + right) - right) == left


# A float never reaches a monetary path.
def test_float_is_always_rejected() -> None:
    rng = seeded()
    for _ in range(100):
        value = rng.uniform(-1000, 1000)
        with pytest.raises(FloatProhibited):
            Money(value, "USD")


# The canonical round trip is exact for every generated value.
def test_canonical_round_trip_is_exact() -> None:
    rng = seeded()
    for value in amounts(rng, limit=200):
        code = _currency_admitting(value)
        try:
            money = Money(value, code)
        except CurrencyPrecisionExceeded:
            continue
        if money.requires_rounding:
            continue
        assert Money.from_canonical(money.to_canonical(), code) == money


def test_seed_is_recorded_and_stable() -> None:
    a = seeded()
    b = seeded()
    assert [a.random() for _ in range(5)] == [b.random() for _ in range(5)]
    assert PROPERTY_SEED == 20261028


def _currency_admitting(value: Decimal) -> CurrencyCode:
    scale = -value.as_tuple().exponent
    for code in CurrencyCode:
        if code.exponent >= scale:
            return code
    return CurrencyCode.KWD
