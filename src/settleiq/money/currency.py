"""Declared currency policy.

The supported set is deliberately small and explicit. Every entry carries its
ISO 4217 minor-unit exponent. An unknown currency is a hard error, never a
default to 2 (SETTLEIQ-M1-001 AC-2.04).

The exponents below are load-bearing: JPY is 0, USD/EUR/GBP/INR are 2, and
BHD/KWD are 3. A single fixed decimal scale cannot express all three, which is
why a declared table rather than a column width carries the money-safety rule.
"""

from __future__ import annotations

from enum import Enum
from typing import Final

from .errors import CurrencyNotSupported

__all__ = ["CURRENCY_EXPONENTS", "CurrencyCode", "SUPPORTED_CURRENCIES"]

#: ISO 4217 minor-unit exponent per supported currency code.
CURRENCY_EXPONENTS: Final[dict[str, int]] = {
    "USD": 2,
    "EUR": 2,
    "GBP": 2,
    "INR": 2,
    "JPY": 0,
    "BHD": 3,
    "KWD": 3,
}

#: Bump when the supported set or an exponent changes. Participates in the
#: schema version and therefore in run identity (AC-2.05).
CURRENCY_TABLE_VERSION: Final[str] = "1.0.0"


class CurrencyCode(str, Enum):
    """A supported currency, identified by its ISO 4217 alphabetic code."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"
    JPY = "JPY"
    BHD = "BHD"
    KWD = "KWD"

    @classmethod
    def parse(cls, raw: str) -> CurrencyCode:
        """Parse a currency code, failing closed on anything unsupported.

        Raises :class:`CurrencyNotSupported` — never a default to exponent 2.
        """
        code = raw.strip().upper()
        if code not in CURRENCY_EXPONENTS:
            raise CurrencyNotSupported(code, tuple(CURRENCY_EXPONENTS))
        return cls(code)

    @property
    def exponent(self) -> int:
        """Minor-unit exponent: 0 for JPY, 3 for BHD, 2 for the rest."""
        return CURRENCY_EXPONENTS[self.value]


SUPPORTED_CURRENCIES: Final[tuple[CurrencyCode, ...]] = tuple(CurrencyCode)
