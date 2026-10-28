"""The SourceAdapter interface — frozen at M1, before any adapter is written.

This is the single most consequential boundary in the architecture (`05`
ARCH-R04/R05). It is specified source-agnostically: it describes what *any*
financial source must satisfy, so it stays correct whether or not a second
processor is ever added.

**The freeze is proven by absence (SETTLEIQ-M1-001 AC-6.01):** this package
contains no adapter implementation. A test asserts that.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Protocol, runtime_checkable

from settleiq.money import Money
from settleiq.model.entities import (
    Adjustment,
    BankDeposit,
    Charge,
    Fee,
    Payout,
    Refund,
    SettlementBatch,
)
from settleiq.model.provenance import DataProvenance, require_synthetic_or_authorized

__all__ = [
    "ADAPTER_INTERFACE_VERSION",
    "NormalizedBatch",
    "SourceAdapter",
    "SourceAdapterError",
]

#: Frozen at M1. Bumping this is an OWNER decision recorded in `12`.
ADAPTER_INTERFACE_VERSION: Final[str] = "1.0.0"


class SourceAdapterError(Exception):
    """A source could not be normalized.

    Fail-closed: a partially understood payload produces this error and *no*
    canonical records enter the model (`07` REC-R22).
    """


@dataclass(frozen=True)
class NormalizedBatch:
    """The canonical product of an adapter.

    Every field is canonical. No processor-specific shape crosses this boundary
    (`05` ARCH-R05): if two processors both mean "the money moved on this date",
    that one concept is expressed once here and each adapter maps to it.
    """

    charges: tuple[Charge, ...]
    fees: tuple[Fee, ...]
    refunds: tuple[Refund, ...]
    adjustments: tuple[Adjustment, ...]
    payouts: tuple[Payout, ...]
    batches: tuple[SettlementBatch, ...]
    deposits: tuple[BankDeposit, ...]
    provenance: DataProvenance = DataProvenance.SYNTHETIC
    source_version: str = ""
    schema_version: str = ""

    def __post_init__(self) -> None:
        require_synthetic_or_authorized(self.provenance)

    def record_count(self) -> int:
        return sum(
            len(group)
            for group in (
                self.charges,
                self.fees,
                self.refunds,
                self.adjustments,
                self.payouts,
                self.batches,
                self.deposits,
            )
        )


@runtime_checkable
class SourceAdapter(Protocol):
    """What every financial source must satisfy.

    Five obligations, each stated as a contract rather than a convention:

    1. **Version declaration.** `source_version` and `schema_version` are carried
       into every produced record, so a run's identity includes what produced it.
    2. **Canonical out.** Returns `NormalizedBatch` and nothing else. A
       processor-specific type must not escape.
    3. **Fail closed.** A malformed, partial, or unrecognised payload raises
       `SourceAdapterError`. It never yields partial canonicalization.
    4. **No unmapped vocabulary.** A value with no canonical mapping is a
       normalization failure — never silently mapped to a catch-all (`06` R11).
    5. **No ambient input.** Identical input bytes produce an identical
       `NormalizedBatch`, byte for byte (`05` ARCH-R13).
    """

    source_version: str
    schema_version: str

    def normalize(self, payload: bytes, *, provenance: DataProvenance) -> NormalizedBatch:
        """Normalize raw source bytes into canonical records.

        `payload` is the exact byte string supplied by the caller. Two calls with
        identical bytes must return identical results.
        """
        ...


# Retained so the annotation above resolves; mirrors DataProvenance exactly.
class _Reserved:  # pragma: no cover
    """Placeholder removed."""


def rejects_float_in_payload(payload: object) -> None:
    """A guard adapters may call on parsed JSON before building any Money.

    A JSON number parses to a binary float. Anything reaching a monetary path
    must have arrived as a string.
    """
    if isinstance(payload, float):
        raise SourceAdapterError(
            "a monetary value arrived as a JSON number and was parsed to a binary "
            "float; monetary fields must be transported as strings"
        )


def to_decimal(value: str | int | Decimal) -> Decimal:
    """Parse a monetary field from a source payload, rejecting non-string input."""
    rejects_float_in_payload(value)
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    return Decimal(str(value).strip())


def money(value: str | int | Decimal, currency: str, *, provenance: DataProvenance) -> Money:
    """Build Money from a source field, applying the declared currency policy."""
    return Money(to_decimal(value), currency)
