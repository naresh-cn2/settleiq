"""Exact monetary arithmetic."""

from __future__ import annotations

from .amount import Money
from .context import (
    AMOUNT_PRECISION,
    DEFAULT_CONTEXT,
    ROUNDING_MODE,
    ROUNDING_MODE_NAME,
    get_context,
    recorded_round,
)
from .currency import CURRENCY_EXPONENTS, CURRENCY_TABLE_VERSION, CurrencyCode
from .errors import (
    CurrencyMismatch,
    CurrencyNotSupported,
    CurrencyPrecisionExceeded,
    FloatProhibited,
    InvalidAmountError,
    MoneyError,
)

__all__ = [
    "AMOUNT_PRECISION",
    "CURRENCY_EXPONENTS",
    "CURRENCY_TABLE_VERSION",
    "DEFAULT_CONTEXT",
    "ROUNDING_MODE",
    "ROUNDING_MODE_NAME",
    "CurrencyCode",
    "CurrencyMismatch",
    "CurrencyNotSupported",
    "CurrencyPrecisionExceeded",
    "FloatProhibited",
    "InvalidAmountError",
    "Money",
    "MoneyError",
    "get_context",
    "recorded_round",
]
