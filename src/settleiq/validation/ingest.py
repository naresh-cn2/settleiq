"""Ingestion validation.

Fail-closed: a malformed record produces a typed error and contributes *no*
canonical record. Input processing never silently discards an invalid record
(`06` §A; SETTLEIQ-M1-001 AC-5).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Final

from settleiq.canonical.serialization import digest
from settleiq.model.provenance import DataProvenance
from settleiq.money import CurrencyCode, Money, MoneyError

__all__ = [
    "IngestionError",
    "IngestionResult",
    "MissingFieldError",
    "QuarantineReason",
    "validate_amount_field",
    "validate_required",
]


class IngestionError(Exception):
    """Base class for every ingestion failure."""


class MissingFieldError(IngestionError):
    """A required field is absent. The error names the field."""

    def __init__(self, record_index: int, field_name: str) -> None:
        self.record_index = record_index
        self.field_name = field_name
        super().__init__(f"record {record_index}: required field {field_name!r} is missing")


class MalformedRecordError(IngestionError):
    """A record could not be parsed into its declared shape."""

    def __init__(self, record_index: int, detail: str) -> None:
        self.record_index = record_index
        self.detail = detail
        super().__init__(f"record {record_index}: {detail}")


class CurrencyError(IngestionError):
    """A currency field is absent, unknown, or malformed."""


class QuarantineReason(str):
    """Why a record was quarantined. A quarantined record is preserved, not dropped."""

    MALFORMED = "MALFORMED"
    MISSING_FIELD = "MISSING_FIELD"
    PRECISION = "PRECISION"
    DUPLICATE = "DUPLICATE"
    UNSUPPORTED_CURRENCY = "UNSUPPORTED_CURRENCY"


@dataclass(frozen=True)
class IngestionResult:
    """The outcome of validating a record set.

    Counts are reported, not inferred: accepted, quarantined, and duplicate.
    A quarantined record is retained with its reason so it can be investigated.
    """

    accepted: tuple[dict[str, object], ...]
    quarantined: tuple[tuple[int, str, str], ...] = field(default_factory=tuple)
    duplicates: tuple[str, ...] = field(default_factory=tuple)

    @property
    def accepted_count(self) -> int:
        return len(self.accepted)

    @property
    def quarantined_count(self) -> int:
        return len(self.quarantined)

    @property
    def duplicate_count(self) -> int:
        return len(self.duplicates)


REQUIRED_FIELDS: Final[dict[str, tuple[str, ...]]] = {
    "charge": ("id", "amount", "currency", "created"),
    "fee": ("id", "amount", "currency", "type", "created"),
    "refund": ("id", "amount", "currency", "charge", "created"),
    "payout": ("id", "amount", "currency", "arrival_date"),
    "deposit": ("id", "amount", "currency", "posted", "narration"),
}

#: A record of an unmodelled kind is validated against this generic shape rather
#: than being discarded at ingestion. It is the engine's job to classify it
#: UNKNOWN, and discarding it here would make that outcome unreachable
#: (`16` section B.4).
GENERIC_FIELDS: Final[tuple[str, ...]] = ("id", "amount", "currency")


def validate_required(record: dict[str, object], kind: str, index: int) -> None:
    """Raise naming the first missing required field for this record kind."""
    required = REQUIRED_FIELDS.get(kind, GENERIC_FIELDS)
    for name in required:
        if name not in record or record[name] in (None, ""):
            raise MissingFieldError(index, name)


def validate_amount_field(record: dict[str, object], kind: str, index: int) -> Money:
    """Validate the `amount`/`currency` pair against the declared policy.

    Raises rather than rounding, and raises on an unknown currency rather than
    defaulting to exponent 2 (AC-5.05, AC-5.06).
    """
    validate_required(record, kind, index)
    raw_amount = record["amount"]
    if isinstance(raw_amount, float):
        raise MalformedRecordError(
            index, "amount arrived as a JSON number; monetary fields must be strings"
        )
    raw_currency = record["currency"]
    if not isinstance(raw_currency, str):
        raise CurrencyError(f"record {index}: currency must be a string code")
    try:
        currency = CurrencyCode.parse(raw_currency)
    except MoneyError as exc:
        raise CurrencyError(f"record {index}: {exc}") from exc
    try:
        return Money(str(raw_amount), currency)
    except MoneyError as exc:
        raise MalformedRecordError(index, str(exc)) from exc


def record_digest(kind: str, record: dict[str, object]) -> str:
    """A stable content digest for duplicate detection, independent of ordering."""
    return digest({"kind": kind, "record": {str(k): v for k, v in sorted(record.items())}})


def validate_records(
    records: list[tuple[str, dict[str, object]]],
    *,
    provenance: DataProvenance = DataProvenance.SYNTHETIC,
) -> IngestionResult:
    """Validate a record set, quarantining failures with a reason per record.

    Repeated submissions are detected by content digest and reported as
    duplicates, not silently deduplicated: deduplication is itself a
    reconciliation fact worth seeing (`07` REC-R20).
    """
    accepted: list[dict[str, object]] = []
    quarantined: list[tuple[int, str, str]] = []
    duplicates: list[str] = []
    seen: dict[str, int] = {}

    for index, (kind, record) in enumerate(records):
        try:
            validate_required(record, kind, index)
            validate_amount_field(record, kind, index)
        except MissingFieldError as exc:
            quarantined.append((index, QuarantineReason.MISSING_FIELD, str(exc)))
            continue
        except (MalformedRecordError, CurrencyError) as exc:
            reason = (
                QuarantineReason.UNSUPPORTED_CURRENCY
                if isinstance(exc, CurrencyError)
                else QuarantineReason.MALFORMED
            )
            quarantined.append((index, reason, str(exc)))
            continue
        except MoneyError as exc:
            quarantined.append((index, QuarantineReason.PRECISION, str(exc)))
            continue

        fingerprint = record_digest(kind, record)
        if fingerprint in seen:
            duplicates.append(f"{kind}:{record.get('id', '')}")
            continue
        seen[fingerprint] = index
        accepted.append({"kind": kind, "record": record, "index": index, "digest": fingerprint})

    return IngestionResult(
        accepted=tuple(accepted), quarantined=tuple(quarantined), duplicates=tuple(duplicates)
    )


__all__.extend(
    [
        "CurrencyError",
        "MalformedRecordError",
        "REQUIRED_FIELDS",
        "record_digest",
        "validate_records",
    ]
)


def _unused(value: Decimal) -> Decimal:  # pragma: no cover
    """Retained to keep the Decimal import meaningful for type checkers."""
    return value
