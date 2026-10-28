"""Canonical financial entities.

Every entity is immutable, carries an explicit currency on every amount, and
carries its DataProvenance. A correction is a superseding record, never an
in-place update (SETTLEIQ-M1-001 AC-3.01/AC-3.04).

The entity set is fixed at M1 (AC-3.05). `RESIDUAL` and the candidate-set shape
on decisions are present specifically because `16` §B.1 and §B.2 land in the
model rather than in the engine.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import NewType

from settleiq.canonical.serialization import digest
from settleiq.model.provenance import DataProvenance
from settleiq.money import Money

__all__ = [
    "Adjustment",
    "BankDeposit",
    "Charge",
    "ConstituentType",
    "Fee",
    "Payout",
    "ReconciliationRun",
    "Refund",
    "SettlementBatch",
    "SourceRecordId",
    "stable_digest",
]

#: Opaque source identifier. Parsing its structure is prohibited.
SourceRecordId = NewType("SourceRecordId", str)


class ConstituentType(str, Enum):
    """What a payout constituent is.

    `RESIDUAL` is a first-class type, not a rounding bucket
    (SETTLEIQ-16 §B.2). `UNATTRIBUTED` preserves a constituent that cannot be
    assigned, rather than absorbing it into another to make a sum work.
    """

    CHARGE = "CHARGE"
    FEE = "FEE"
    REFUND = "REFUND"
    ADJUSTMENT = "ADJUSTMENT"
    RESIDUAL = "RESIDUAL"
    UNATTRIBUTED = "UNATTRIBUTED"


@dataclass(frozen=True)
class Charge:
    """A customer payment captured by the processor."""

    source_id: SourceRecordId
    amount: Money
    captured_at: str
    reference: str
    provenance: DataProvenance = DataProvenance.SYNTHETIC
    customer_reference: str | None = None
    description: str | None = None

    def to_canonical(self) -> dict[str, object]:
        return {
            "kind": "Charge",
            "source_id": self.source_id,
            "amount": self.amount.to_canonical(),
            "captured_at": self.captured_at,
            "reference": self.reference,
            "provenance": self.provenance.value,
            "customer_reference": self.customer_reference or "",
        }


@dataclass(frozen=True)
class Fee:
    """A processor fee. Typed, never aggregated (`16` §B — fee breaks by type)."""

    source_id: SourceRecordId
    amount: Money
    fee_type: str
    charged_at: str
    provenance: DataProvenance = DataProvenance.SYNTHETIC

    def to_canonical(self) -> dict[str, object]:
        return {
            "kind": "Fee",
            "source_id": self.source_id,
            "amount": self.amount.to_canonical(),
            "fee_type": self.fee_type,
            "charged_at": self.charged_at,
            "provenance": self.provenance.value,
        }


@dataclass(frozen=True)
class Refund:
    """A refund of a charge, possibly arriving mid-payout."""

    source_id: SourceRecordId
    amount: Money
    refunded_at: str
    charge_source_id: SourceRecordId
    provenance: DataProvenance = DataProvenance.SYNTHETIC

    def to_canonical(self) -> dict[str, object]:
        return {
            "kind": "Refund",
            "source_id": self.source_id,
            "amount": self.amount.to_canonical(),
            "refunded_at": self.refunded_at,
            "charge_source_id": self.charge_source_id,
            "provenance": self.provenance.value,
        }


@dataclass(frozen=True)
class Adjustment:
    """An adjustment applied by the processor (dispute, correction, write-off)."""

    source_id: SourceRecordId
    amount: Money
    adjustment_type: str
    applied_at: str
    provenance: DataProvenance = DataProvenance.SYNTHETIC

    def to_canonical(self) -> dict[str, object]:
        return {
            "kind": "Adjustment",
            "source_id": self.source_id,
            "amount": self.amount.to_canonical(),
            "adjustment_type": self.adjustment_type,
            "applied_at": self.applied_at,
            "provenance": self.provenance.value,
        }


@dataclass(frozen=True)
class Residual:
    """An explicitly modelled, never-allocated remainder (`16` §B.2).

    Carries the allocation rule and version that produced it, so a residual is
    a countable, investigable object rather than an absorption bucket.
    """

    amount: Money
    allocation_rule_id: str
    rule_version: str
    provenance: DataProvenance = DataProvenance.SYNTHETIC

    def to_canonical(self) -> dict[str, object]:
        return {
            "kind": "Residual",
            "amount": self.amount.to_canonical(),
            "allocation_rule_id": self.allocation_rule_id,
            "rule_version": self.rule_version,
            "provenance": self.provenance.value,
        }


@dataclass(frozen=True)
class SettlementBatch:
    """The processor's grouping of activity that produces a payout."""

    source_id: SourceRecordId
    batch_number: str
    closed_at: str
    provenance: DataProvenance = DataProvenance.SYNTHETIC

    def to_canonical(self) -> dict[str, object]:
        return {
            "kind": "SettlementBatch",
            "source_id": self.source_id,
            "batch_number": self.batch_number,
            "closed_at": self.closed_at,
            "provenance": self.provenance.value,
        }


@dataclass(frozen=True)
class Payout:
    """Money the processor moved to the business bank account.

    The composition is a tuple of constituents; a payout's total is a bridge
    target, never the reconciliation unit (SETTLEIQ-REQ-006).
    """

    source_id: SourceRecordId
    amount: Money
    batch_source_id: SourceRecordId | None
    paid_at: str
    provenance: DataProvenance = DataProvenance.SYNTHETIC
    payout_reference: str | None = None

    def to_canonical(self) -> dict[str, object]:
        return {
            "kind": "Payout",
            "source_id": self.source_id,
            "amount": self.amount.to_canonical(),
            "batch_source_id": self.batch_source_id or "",
            "paid_at": self.paid_at,
            "provenance": self.provenance.value,
            "payout_reference": self.payout_reference or "",
        }


@dataclass(frozen=True)
class BankDeposit:
    """The bank-side record of money arriving."""

    source_id: SourceRecordId
    amount: Money
    posted_at: str
    narration: str
    bank_account_last3: str
    provenance: DataProvenance = DataProvenance.SYNTHETIC

    def to_canonical(self) -> dict[str, object]:
        return {
            "kind": "BankDeposit",
            "source_id": self.source_id,
            "amount": self.amount.to_canonical(),
            "posted_at": self.posted_at,
            "narration": self.narration,
            "bank_account_last3": self.bank_account_last3,
            "provenance": self.provenance.value,
        }


@dataclass(frozen=True)
class ReconciliationRun:
    """A completed or failed reconciliation run, with its declared identity."""

    run_id: str
    input_digest: str
    rule_version: str
    schema_version: str
    status: str
    declared_window_start: str | None = None
    declared_window_end: str | None = None

    def to_canonical(self) -> dict[str, object]:
        return {
            "kind": "ReconciliationRun",
            "run_id": self.run_id,
            "input_digest": self.input_digest,
            "rule_version": self.rule_version,
            "schema_version": self.schema_version,
            "status": self.status,
            "declared_window_start": self.declared_window_start or "",
            "declared_window_end": self.declared_window_end or "",
        }


def stable_digest(records: Mapping[str, object]) -> str:
    """Digest a record set canonically.

    Every value must already be canonical. No ambient value reaches here
    (AC-4.04).
    """
    return digest({"records": dict(records)})
