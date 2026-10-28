"""Money-domain error taxonomy.

Every error is typed. A generic ``ValueError`` crossing a component boundary is
a defect: it destroys the caller's ability to fail closed with an actionable
message (SETTLEIQ-M1-001 AC-5).
"""

from __future__ import annotations

from decimal import Decimal

__all__ = [
    "CurrencyMismatch",
    "CurrencyNotSupported",
    "CurrencyPrecisionExceeded",
    "FloatProhibited",
    "InvalidAmountError",
    "MoneyError",
]


class MoneyError(Exception):
    """Base class for every money-domain failure."""


class InvalidAmountError(MoneyError):
    """An amount could not be parsed as a decimal.

    Typed rather than a bare ``ValueError`` so that a component boundary can
    distinguish a malformed amount from an unrelated ``ValueError``.
    """


class FloatProhibited(MoneyError):
    """A binary float reached a monetary path.

    Raised by construction and by parsing. This is the runtime expression of
    SETTLEIQ-REQ-005; the static gate that also enforces it is separate.
    """


class CurrencyNotSupported(MoneyError):
    """A currency code is not in the declared supported set."""

    def __init__(self, code: str, supported: tuple[str, ...] = ()) -> None:
        self.code = code
        suffix = f"; supported codes are {list(supported)}" if supported else ""
        super().__init__(f"currency {code!r} is not supported{suffix}")


class CurrencyPrecisionExceeded(MoneyError):
    """An amount carries more decimal places than its currency permits.

    Raised rather than rounded. Silently rounding here would either reject
    valid JPY data or accept invalid USD data.
    """

    def __init__(self, value: Decimal, exponent: int, code: str) -> None:
        self.value = value
        self.exponent = exponent
        self.code = code
        super().__init__(
            f"{value} has more than {exponent} decimal places for currency {code}"
        )


class CurrencyMismatch(MoneyError):
    """An operation combined amounts of different currencies.

    Arithmetic never converts implicitly. Conversion is an explicit recorded
    operation, not a property of addition.
    """

    def __init__(self, left: str, right: str, operation: str) -> None:
        self.left = left
        self.right = right
        self.operation = operation
        super().__init__(
            f"cannot {operation} {left} and {right}; currency conversion is explicit "
            "and never implicit"
        )
