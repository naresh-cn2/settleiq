"""The declared decimal context and rounding mode.

Set once, reused everywhere. A component that reaches for the ambient default
context is a defect, because its rounding behaviour would depend on wherever it
happened to run (SETTLEIQ-M1-001 AC-1.02).
"""

from __future__ import annotations

import decimal
from typing import Final

__all__ = [
    "AMOUNT_PRECISION",
    "DEFAULT_CONTEXT",
    "ROUNDING_MODE",
    "get_context",
    "recorded_round",
]

#: Digits of precision retained for monetary arithmetic. Comfortably above any
#: realistic settlement amount times any realistic fee percentage.
AMOUNT_PRECISION: Final[int] = 60

#: The single rounding mode used for money. ROUND_HALF_UP is the conventional
#: commercial mode and, more importantly, it is declared rather than assumed.
ROUNDING_MODE: Final[str] = decimal.ROUND_HALF_UP
ROUNDING_MODE_NAME: Final[str] = "ROUND_HALF_UP"

#: The one context. Every monetary computation uses this and nothing else.
DEFAULT_CONTEXT: Final[decimal.Context] = decimal.Context(
    prec=AMOUNT_PRECISION,
    rounding=ROUNDING_MODE,
    # Money errors on overflow rather than producing Infinity, which cannot be
    # represented in any ledger.
    traps=[decimal.InvalidOperation, decimal.Overflow, decimal.DivisionByZero],
)


def get_context() -> decimal.Context:
    """Return the declared context. Never the ambient one."""
    return DEFAULT_CONTEXT


def recorded_round(value: decimal.Decimal, exponent: int) -> decimal.Decimal:
    """Round to a currency's exponent, explicitly, under the declared context.

    Rounding is a deliberate act with a recorded mode. This function exists so
    that rounding never happens by accident.
    """
    quantum = decimal.Decimal(1).scaleb(-exponent)
    return value.quantize(quantum, rounding=ROUNDING_MODE, context=DEFAULT_CONTEXT)
