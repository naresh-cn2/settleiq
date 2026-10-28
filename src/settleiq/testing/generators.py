"""Deterministic property-test generators.

Hypothesis could not be used: its native extension is blocked by an Application
Control policy on the build machine (recorded as an environment constraint, not
hidden). A seeded pure-Python generator is used instead, which has the advantage
that the generated population is fully reproducible from the repository alone.
"""

from __future__ import annotations

import random
from collections.abc import Iterator
from decimal import Decimal
from typing import Final

from settleiq.money import CurrencyCode, CurrencyPrecisionExceeded, Money

__all__ = [
    "PROPERTY_SEED",
    "amounts",
    "money_amounts",
    "seeded",
]

#: The single recorded seed. Every property test draws from a generator seeded
#: with this value, so the population is reproducible (SETTLEIQ-M1-001 AC-7.03).
PROPERTY_SEED: Final[int] = 20261028


def seeded(seed: int = PROPERTY_SEED) -> random.Random:
    return random.Random(seed)


def amounts(rng: random.Random, *, limit: int = 200) -> Iterator[Decimal]:
    """Yield representable amounts for a randomly chosen supported currency."""
    codes = list(CurrencyCode)
    for _ in range(limit):
        currency = rng.choice(codes)
        quantum = Decimal(1).scaleb(-currency.exponent)
        units = rng.randint(-10**9, 10**9)
        yield (Decimal(units) * quantum).quantize(quantum)


def money_amounts(rng: random.Random, *, limit: int = 200) -> Iterator[Money]:
    """Yield valid Money values, skipping any generated value the policy rejects."""
    for value in amounts(rng, limit=limit * 2):
        try:
            yield Money(value, value.as_tuple().exponent and _code_for(value))
        except (CurrencyPrecisionExceeded, ValueError):
            continue


def _code_for(value: Decimal) -> CurrencyCode:
    """Choose a currency whose exponent admits this value's scale."""
    scale = -value.as_tuple().exponent
    for code in CurrencyCode:
        if code.exponent >= scale:
            return code
    return CurrencyCode.KWD  # widest supported scale
