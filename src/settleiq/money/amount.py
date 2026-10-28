"""The Money type.

An amount is a :class:`decimal.Decimal` paired with a declared currency. It is
immutable, it refuses construction from a binary float, and it refuses
cross-currency arithmetic.

Design commitments, each traceable to an acceptance criterion:

* Construction from ``float`` raises ``FloatProhibited`` (AC-1.01).
* Mixed-currency arithmetic raises ``CurrencyMismatch`` (AC-1.03).
* ``from_string`` / ``from_canonical`` enforce the currency's exponent and
  raise ``CurrencyPrecisionExceeded`` rather than rounding (AC-2.01…02.03).
* Equality compares the *numeric value*, not the textual form, so
  ``Money("10.5") == Money("10.50")`` for USD but ``Money("100", JPY)`` has no
  fractional part to be equivalent to.
"""

from __future__ import annotations

import decimal
from decimal import Decimal
from typing import Final, Self

from .context import DEFAULT_CONTEXT, ROUNDING_MODE_NAME, get_context
from .currency import CURRENCY_TABLE_VERSION, CurrencyCode
from .errors import (
    CurrencyMismatch,
    CurrencyPrecisionExceeded,
    FloatProhibited,
    InvalidAmountError,
)

__all__ = ["CURRENCY_TABLE_VERSION", "Decimal", "Money"]

_ZERO: Final[Decimal] = Decimal(0)


class Money:
    """An exact monetary amount in a single declared currency."""

    __slots__ = ("_amount", "_currency", "_requires_rounding")

    def __init__(self, amount: Decimal | str | int, currency: CurrencyCode | str) -> None:
        if isinstance(amount, float):
            raise FloatProhibited(
                "Money cannot be constructed from a binary float; pass a str, "
                "int, or Decimal. A float has already lost the value."
            )
        if isinstance(currency, str):
            currency = CurrencyCode.parse(currency)
        parsed = self._to_decimal(amount)
        self._validate_exponent(parsed, currency, strict=True)
        object.__setattr__(self, "_amount", parsed)
        object.__setattr__(self, "_currency", currency)
        object.__setattr__(self, "_requires_rounding", False)

    # ------------------------------------------------------------------ construction

    @staticmethod
    def _to_decimal(amount: Decimal | str | int) -> Decimal:
        ctx = get_context()
        if isinstance(amount, Decimal):
            return +amount  # normalise under the declared context
        if isinstance(amount, int):
            return Decimal(amount, context=ctx)
        if isinstance(amount, str):
            text = amount.strip()
            if not text:
                raise InvalidAmountError("Money cannot be constructed from an empty string")
            try:
                return Decimal(text, context=ctx)
            except decimal.InvalidOperation as exc:
                raise InvalidAmountError(f"{amount!r} is not a valid decimal amount") from exc
        raise InvalidAmountError(f"unsupported amount type: {type(amount).__name__}")

    @staticmethod
    def _validate_exponent(value: Decimal, currency: CurrencyCode, *, strict: bool) -> bool:
        """Check that ``value`` is representable at the currency's scale.

        The test is numerical, not textual: ``10.0000`` is exactly ``10.00`` and
        is fine, while ``10.005`` in USD is not representable and is rejected.

        ``strict`` is used on ingest and serialization boundaries, where a value
        carrying excess precision is malformed input. A computed intermediate is
        built through :meth:`from_computation`, which is deliberately permissive
        so that an explicit rounding decision is forced before persistence.
        """
        quantum = Decimal(1).scaleb(-currency.exponent)
        representable = value == value.quantize(quantum)
        if not representable and strict:
            raise CurrencyPrecisionExceeded(value, currency.exponent, currency.value)
        return representable

    @classmethod
    def from_canonical(cls, text: str, code: str) -> Money:
        """Build from the canonical string form ``"<amount>|<CUR>"``.

        This is the inverse of :meth:`to_canonical` and is the only supported
        path for values that have crossed a serialization boundary. It is strict:
        a persisted value must be representable at the currency's scale.
        """
        amount_text, _, currency_text = text.partition("|")
        if not currency_text:
            raise ValueError(f"canonical money must be '<amount>|<CUR>', got {text!r}")
        return cls(amount_text, CurrencyCode.parse(currency_text))

    @classmethod
    def from_computation(cls, value: Decimal, currency: CurrencyCode) -> Money:
        """Build from the result of an arithmetic operation.

        Permits precision beyond the currency's minor unit, because a computed
        fee or share legitimately has one. Such a value carries
        :attr:`requires_rounding` and cannot be persisted until it is explicitly
        rounded via :meth:`rounded`. This is the mechanism that stops a residual
        from disappearing into a silent round.
        """
        if isinstance(value, float):
            raise FloatProhibited("a computed monetary value must not be a float")
        instance = cls.__new__(cls)
        representable = cls._validate_exponent(value, currency, strict=False)
        object.__setattr__(instance, "_amount", +value)
        object.__setattr__(instance, "_currency", currency)
        object.__setattr__(instance, "_requires_rounding", not representable)
        return instance

    @classmethod
    def zero(cls, currency: CurrencyCode | str) -> Money:
        """Zero at the currency's own exponent, so it renders consistently."""
        if isinstance(currency, str):
            currency = CurrencyCode.parse(currency)
        quantum = Decimal(1).scaleb(-currency.exponent)
        return cls(Decimal(0).quantize(quantum), currency)

    # ------------------------------------------------------------------ accessors

    @property
    def amount(self) -> Decimal:
        return self._amount

    @property
    def currency(self) -> CurrencyCode:
        return self._currency

    @property
    def code(self) -> str:
        return self._currency.value

    @property
    def exponent(self) -> int:
        return self._currency.exponent

    def is_zero(self) -> bool:
        return self._amount == _ZERO

    @property
    def requires_rounding(self) -> bool:
        """True when this value carries precision beyond its currency's minor unit."""
        return self._requires_rounding

    def is_negative(self) -> bool:
        return self._amount < _ZERO

    # ------------------------------------------------------------------ arithmetic

    def _require_same_currency(self, other: Money, operation: str) -> None:
        if self._currency != other._currency:
            raise CurrencyMismatch(self.code, other.code, operation)

    def __add__(self, other: Money) -> Money:
        self._require_same_currency(other, "add")
        return Money(self._amount + other._amount, self._currency)

    def __sub__(self, other: Money) -> Money:
        self._require_same_currency(other, "subtract")
        return Money(self._amount - other._amount, self._currency)

    def __neg__(self) -> Money:
        return Money(-self._amount, self._currency)

    def __abs__(self) -> Money:
        return Money(abs(self._amount), self._currency)

    def _scaled(self, factor: Decimal) -> Money:
        """Multiply by a pure ratio. The ratio is not money and carries no currency."""
        if isinstance(factor, float):
            raise FloatProhibited("a monetary multiplier must not be a float")
        product = self._amount * Decimal(factor, context=get_context())
        # Deliberately built via from_computation: a product may carry more
        # precision than the currency's minor unit, and forcing an explicit
        # rounding decision is the point (`16` §B.3).
        return Money.from_computation(product, self._currency)

    def rounded(self) -> Money:
        """Round to this currency's exponent under the declared, recorded mode.

        Rounding is a deliberate act with a recorded mode. This method exists so
        that rounding never happens by accident, and every caller of it is a
        place a reviewer can point to.
        """
        from .context import recorded_round

        return Money(recorded_round(self._amount, self._currency.exponent), self._currency)

    @staticmethod
    def _reject_float(value: object, role: str) -> None:
        if isinstance(value, float):
            raise FloatProhibited(f"a {role} must not be a binary float")

    def multiply(self, factor: str | Decimal | int) -> Money:
        self._reject_float(factor, "monetary multiplier")
        return self._scaled(factor)

    def divide(self, divisor: str | Decimal | int) -> Money:
        """Divide, returning an exact quotient where possible.

        A quotient that does not terminate raises rather than rounding, because
        a silently rounded quotient is how residuals disappear (SETTLEIQ-M1-001
        AC-2 / `16` §B.2).
        """
        self._reject_float(divisor, "monetary divisor")
        denominator = Decimal(divisor) if not isinstance(divisor, Decimal) else divisor
        if denominator == _ZERO:
            raise ZeroDivisionError("cannot divide money by zero")
        try:
            quotient = self._amount / denominator
        except decimal.DivisionByZero as exc:  # pragma: no cover
            raise ZeroDivisionError from exc
        # Detect a non-terminating quotient: with the declared precision, a
        # repeating quotient will have been rounded.
        if quotient * denominator != self._amount:
            raise decimal.InvalidOperation(
                f"{self._amount}/{denominator} does not terminate; the remainder must "
                "be modelled explicitly as a residual, never absorbed"
            )
        return Money(quotient, self._currency)

    def allocate(self, weights: list[int]) -> list[Money]:
        """Split into parts proportional to integer weights, with the remainder kept explicit.

        Returns ``weights + 1`` items: the final item is the unallocated
        remainder. This is the allocation primitive required by `16` §B.2 — the
        residual is never distributed and never rounded away.
        """
        if not weights:
            raise ValueError("allocation requires at least one weight")
        if any(w < 0 for w in weights):
            raise ValueError("allocation weights must be non-negative")
        total_weight = sum(weights)
        if total_weight == 0:
            raise ValueError("allocation weights must not sum to zero")
        exact = self._amount
        allocated: list[Money] = []
        running = _ZERO
        for weight in weights:
            share = (exact * Decimal(weight)) / Decimal(total_weight)
            if share * Decimal(total_weight) != exact * Decimal(weight):
                raise decimal.InvalidOperation(
                    "allocation does not terminate; the residual must be explicit"
                )
            allocated.append(Money(share, self._currency))
            running += share
        allocated.append(Money(exact - running, self._currency))
        return allocated

    # ------------------------------------------------------------------ comparison

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self._amount == other._amount and self._currency == other._currency

    def __hash__(self) -> int:
        return hash((self._amount, self._currency))

    def _compare(self, other: Money) -> int:
        self._require_same_currency(other, "compare")
        if self._amount < other._amount:
            return -1
        if self._amount > other._amount:
            return 1
        return 0

    def __lt__(self, other: Money) -> bool:
        return self._compare(other) < 0

    def __le__(self, other: Money) -> bool:
        return self._compare(other) <= 0

    def __gt__(self, other: Money) -> bool:
        return self._compare(other) > 0

    def __ge__(self, other: Money) -> bool:
        return self._compare(other) >= 0

    # ------------------------------------------------------------------ serialization

    def to_canonical(self) -> str:
        """Canonical string form: ``"<amount>|<CUR>"``.

        The amount is rendered from the Decimal, never through a float, so the
        round trip is exact. Refuses to serialize a value that still requires
        rounding: persisting an unrounded intermediate is how residuals vanish.
        """
        if self._requires_rounding:
            raise CurrencyPrecisionExceeded(
                self._amount, self._currency.exponent, self._currency.value
            )
        return f"{format(self._amount, 'f')}|{self._currency.value}"

    def __str__(self) -> str:
        return f"{format(self._amount, 'f')} {self._currency.value}"

    def __repr__(self) -> str:
        return f"Money({self.to_canonical()!r})"

    # ------------------------------------------------------------------ immutability

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("Money is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("Money is immutable")


# Re-exported so callers can construct Decimals without importing decimal.
__all__.append("DEFAULT_CONTEXT")
__all__.append("ROUNDING_MODE_NAME")
DEFAULT_CONTEXT = DEFAULT_CONTEXT
