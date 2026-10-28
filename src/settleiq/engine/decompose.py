"""Payout decomposition.

A payout is reconciled by decomposing it into its constituents and matching each
one — never by comparing payout totals (SETTLEIQ-REQ-006).

The decomposition must **close exactly**: gross minus fees minus refunds equals
the net paid, in Decimal, with no unexplained residual. When it does not close,
the shortfall is modelled explicitly as a `RESIDUAL` and reported as a typed
break (`16` section B.2).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Mapping, Sequence

from settleiq.canonical.serialization import digest
from settleiq.money import CurrencyMismatch, Money
from settleiq.model.entities import Residual

__all__ = [
    "Constituent",
    "Decomposition",
    "decompose",
    "extract_reference",
]


@dataclass(frozen=True)
class Constituent:
    """One component of a payout's composition."""

    kind: str
    source_id: str
    amount: Money
    contribution: Decimal  # +1 for charges, -1 for fees and refunds

    def to_canonical(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "source_id": self.source_id,
            "amount": self.amount.to_canonical(),
            "contribution": str(self.contribution),
        }


@dataclass(frozen=True)
class Decomposition:
    """The result of decomposing one payout."""

    payout_id: str
    batch_reference: str
    gross: Money
    fees: Money
    refunds: Money
    adjustments: Money
    net_expected: Money
    net_paid: Money
    residual: Money
    closes_exactly: bool
    constituents: tuple[Constituent, ...]

    def to_canonical(self) -> dict[str, object]:
        return {
            "payout_id": self.payout_id,
            "batch_reference": self.batch_reference,
            "gross": self.gross.to_canonical(),
            "fees": self.fees.to_canonical(),
            "refunds": self.refunds.to_canonical(),
            "adjustments": self.adjustments.to_canonical(),
            "net_expected": self.net_expected.to_canonical(),
            "net_paid": self.net_paid.to_canonical(),
            "residual": self.residual.to_canonical(),
            "closes_exactly": self.closes_exactly,
            "constituents": [c.to_canonical() for c in self.constituents],
        }

    def provenance_digest(self) -> str:
        return digest(self.to_canonical())


#: Which record kinds contribute to a payout, and with what sign.
_CONTRIBUTIONS: Final[dict[str, Decimal]] = {
    "charge": Decimal(1),
    "fee": Decimal(-1),
    "refund": Decimal(-1),
    "adjustment": Decimal(-1),
}


def extract_reference(narration: str) -> str:
    """Pull the trailing settlement reference out of a bank narration.

    Deliberately narrow: it takes the final whitespace-separated token. A
    narration with no reference yields an empty string, which cannot match
    anything — the engine fails closed rather than guessing from free text.
    """
    tokens = narration.split()
    return tokens[-1] if tokens else ""


def _money(record: Mapping[str, object]) -> Money:
    return Money(str(record["amount"]), str(record["currency"]))


def _batch(record: Mapping[str, object]) -> str:
    return str(record.get("batch") or extract_reference(str(record.get("narration", ""))))


def decompose(
    payout: Mapping[str, object],
    records: Sequence[Mapping[str, object]],
    *,
    allocation_rule_id: str = "explicit-residual",
    rule_version: str = "1.0.0",
) -> Decomposition:
    """Decompose one payout into its constituents and verify the composition closes.

    Constituents are selected by their settlement-batch reference. The gross,
    fees, refunds, and adjustments are summed separately, and
    ``gross - fees - refunds - adjustments`` must equal the net paid exactly.
    Any shortfall is an explicit residual, never absorbed.
    """
    batch = _batch(payout)
    paid = _money(payout)
    currency = paid.currency

    constituents: list[Constituent] = []
    for entry in records:
        record = entry.get("record") if isinstance(entry, Mapping) else entry
        kind = str((entry.get("kind") if isinstance(entry, Mapping) else "") or "")
        if kind not in _CONTRIBUTIONS:
            continue
        if _batch(record) != batch:
            continue
        amount = _money(record)
        if amount.currency != currency:
            raise CurrencyMismatch(amount.code, currency.value, "decompose")
        constituents.append(
            Constituent(
                kind=kind,
                source_id=str(record.get("id", "")),
                amount=amount,
                contribution=_CONTRIBUTIONS[kind],
            )
        )

    gross = Money.zero(currency)
    fees = Money.zero(currency)
    refunds = Money.zero(currency)
    adjustments = Money.zero(currency)
    for constituent in constituents:
        if constituent.kind == "charge":
            gross = gross + constituent.amount
        elif constituent.kind == "fee":
            fees = fees + constituent.amount
        elif constituent.kind == "refund":
            refunds = refunds + constituent.amount
        else:
            adjustments = adjustments + constituent.amount

    net_expected = (((gross - fees) - refunds) - adjustments)
    residual = net_expected - paid
    closes = residual.is_zero()

    residual_money = (
        residual
        if not closes
        else Residual(
            amount=Money.zero(currency),
            allocation_rule_id=allocation_rule_id,
            rule_version=rule_version,
        ).amount
    )

    return Decomposition(
        payout_id=str(payout.get("id", "")),
        batch_reference=batch,
        gross=gross,
        fees=fees,
        refunds=refunds,
        adjustments=adjustments,
        net_expected=net_expected,
        net_paid=paid,
        residual=residual_money,
        closes_exactly=closes,
        constituents=tuple(constituents),
    )
