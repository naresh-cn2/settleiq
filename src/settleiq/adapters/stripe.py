"""The concrete Stripe source adapter.

Normalizes Stripe financial events, exports, and balance transactions into the
canonical NormalizedBatch conforming strictly to the frozen SourceAdapter protocol.

Financial invariants preserved:
- Exact decimal money arithmetic; floats on monetary paths are strictly rejected.
- Deterministic, byte-identical output for identical payload inputs.
- Fail-closed: missing required fields or unknown currency codes raise SourceAdapterError.
- Duplicate detection within batches.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal
from typing import Final

from settleiq.adapters.interface import (
    ADAPTER_INTERFACE_VERSION,
    NormalizedBatch,
    SourceAdapterError,
)
from settleiq.model.entities import (
    Adjustment,
    BankDeposit,
    Charge,
    Fee,
    Payout,
    Refund,
    SettlementBatch,
    SourceRecordId,
)
from settleiq.model.provenance import DataProvenance, require_synthetic_or_authorized
from settleiq.money import CurrencyCode, Money

__all__ = ["STRIPE_API_VERSION", "StripeSourceAdapter"]

STRIPE_API_VERSION: Final[str] = "2024-06-20"


class StripeSourceAdapter:
    """Adapts Stripe payloads (JSON bytes) into canonical entities."""

    source_version: str = f"stripe-{STRIPE_API_VERSION}"
    schema_version: str = ADAPTER_INTERFACE_VERSION

    def normalize(self, payload: bytes, *, provenance: DataProvenance) -> NormalizedBatch:
        """Parse raw JSON bytes into canonical entities."""
        require_synthetic_or_authorized(provenance)

        # Fail-closed float guard: scan JSON text directly to prevent float smuggling
        text = payload.decode("utf-8")
        try:
            # parse_float=None or parse_float=Decimal so no Python float is constructed
            data = json.loads(text, parse_float=Decimal)
        except Exception as exc:
            raise SourceAdapterError(f"Malformed Stripe JSON payload: {exc}") from exc

        records = data if isinstance(data, list) else data.get("data", [data]) if isinstance(data, dict) else None
        if records is None or not isinstance(records, list):
            raise SourceAdapterError("Stripe payload must be a list of records or an object with a 'data' array")

        charges: list[Charge] = []
        fees: list[Fee] = []
        refunds: list[Refund] = []
        adjustments: list[Adjustment] = []
        payouts: list[Payout] = []
        batches: list[SettlementBatch] = []
        deposits: list[BankDeposit] = []

        seen_ids: set[str] = set()

        for item in records:
            if not isinstance(item, Mapping):
                raise SourceAdapterError(f"Expected record object, got {type(item).__name__}")

            rec_id = str(item.get("id", "")).strip()
            if not rec_id:
                raise SourceAdapterError("Stripe record missing required 'id' field")

            if rec_id in seen_ids:
                raise SourceAdapterError(f"Duplicate record id in batch: {rec_id}")
            seen_ids.add(rec_id)

            obj_type = str(item.get("object", "")).strip() or self._infer_type(rec_id)

            if obj_type in ("charge", "payment_intent"):
                self._parse_charge(item, rec_id, provenance, charges, fees)
            elif obj_type == "refund":
                self._parse_refund(item, rec_id, provenance, refunds)
            elif obj_type in ("fee", "application_fee"):
                self._parse_fee(item, rec_id, provenance, fees)
            elif obj_type in ("payout", "transfer"):
                self._parse_payout(item, rec_id, provenance, payouts, batches)
            elif obj_type in ("dispute", "adjustment"):
                self._parse_adjustment(item, rec_id, provenance, adjustments)
            elif obj_type in ("deposit", "bank_deposit"):
                self._parse_deposit(item, rec_id, provenance, deposits)
            else:
                raise SourceAdapterError(f"Unmapped Stripe object type: {obj_type!r}")

        return NormalizedBatch(
            charges=tuple(charges),
            fees=tuple(fees),
            refunds=tuple(refunds),
            adjustments=tuple(adjustments),
            payouts=tuple(payouts),
            batches=tuple(batches),
            deposits=tuple(deposits),
            provenance=provenance,
            source_version=self.source_version,
            schema_version=self.schema_version,
        )

    def _infer_type(self, rec_id: str) -> str:
        if rec_id.startswith("ch_") or rec_id.startswith("py_"):
            return "charge"
        if rec_id.startswith("re_"):
            return "refund"
        if rec_id.startswith("fee_"):
            return "fee"
        if rec_id.startswith("po_") or rec_id.startswith("tr_"):
            return "payout"
        if rec_id.startswith("dp_") or rec_id.startswith("adj_"):
            return "adjustment"
        if rec_id.startswith("bd_"):
            return "deposit"
        raise SourceAdapterError(f"Cannot infer Stripe object type from ID: {rec_id!r}")

    def _parse_amount(self, item: Mapping[str, object], currency: CurrencyCode) -> Money:
        raw_val = item.get("amount")
        if raw_val is None:
            raise SourceAdapterError("Record missing required 'amount' field")

        if isinstance(raw_val, float):
            raise SourceAdapterError("Float detected in monetary amount")

        # Stripe standard amounts in API are integer minor units (e.g. cents)
        # However, exports or custom transport may provide decimal string amounts ("50.00")
        if isinstance(raw_val, int):
            # Minor units to major decimal
            scale = Decimal(10) ** -currency.exponent
            dec = Decimal(raw_val) * scale
        elif isinstance(raw_val, Decimal):
            dec = raw_val
        elif isinstance(raw_val, str):
            clean = raw_val.strip()
            if not clean:
                raise SourceAdapterError("Empty string for monetary amount")
            dec = Decimal(clean)
        else:
            raise SourceAdapterError(f"Unsupported amount type: {type(raw_val).__name__}")

        return Money(dec, currency)

    def _parse_currency(self, item: Mapping[str, object]) -> CurrencyCode:
        curr_str = str(item.get("currency", "")).strip().upper()
        if not curr_str:
            raise SourceAdapterError("Record missing required 'currency' field")
        try:
            return CurrencyCode.parse(curr_str)
        except Exception as exc:
            raise SourceAdapterError(f"Unsupported currency: {curr_str!r}") from exc

    def _parse_charge(
        self,
        item: Mapping[str, object],
        rec_id: str,
        provenance: DataProvenance,
        charges: list[Charge],
        fees: list[Fee],
    ) -> None:
        curr = self._parse_currency(item)
        money_amt = self._parse_amount(item, curr)
        created = str(item.get("created", "")).strip() or "1970-01-01T00:00:00Z"
        ref = str(item.get("reference") or item.get("payment_intent") or rec_id)
        cust = str(item.get("customer") or item.get("customer_reference") or "")
        desc = str(item.get("description") or "")

        charges.append(
            Charge(
                source_id=SourceRecordId(rec_id),
                amount=money_amt,
                captured_at=created,
                reference=ref,
                provenance=provenance,
                customer_reference=cust or None,
                description=desc or None,
            )
        )

        # Embedded fee_details if present
        fee_details = item.get("fee_details")
        if isinstance(fee_details, list):
            for i, fd in enumerate(fee_details):
                if isinstance(fd, Mapping):
                    f_curr = self._parse_currency(fd) if "currency" in fd else curr
                    f_amt = self._parse_amount(fd, f_curr)
                    f_type = str(fd.get("type", "stripe_fee"))
                    fees.append(
                        Fee(
                            source_id=SourceRecordId(f"{rec_id}_fee_{i}"),
                            amount=f_amt,
                            fee_type=f_type,
                            charged_at=created,
                            provenance=provenance,
                        )
                    )

    def _parse_refund(
        self,
        item: Mapping[str, object],
        rec_id: str,
        provenance: DataProvenance,
        refunds: list[Refund],
    ) -> None:
        curr = self._parse_currency(item)
        money_amt = self._parse_amount(item, curr)
        charge_id = str(item.get("charge", "")).strip()
        if not charge_id:
            raise SourceAdapterError(f"Refund {rec_id} missing required 'charge' reference")
        created = str(item.get("created", "")).strip() or "1970-01-01T00:00:00Z"

        refunds.append(
            Refund(
                source_id=SourceRecordId(rec_id),
                amount=money_amt,
                refunded_at=created,
                charge_source_id=SourceRecordId(charge_id),
                provenance=provenance,
            )
        )

    def _parse_fee(
        self,
        item: Mapping[str, object],
        rec_id: str,
        provenance: DataProvenance,
        fees: list[Fee],
    ) -> None:
        curr = self._parse_currency(item)
        money_amt = self._parse_amount(item, curr)
        created = str(item.get("created", "")).strip() or "1970-01-01T00:00:00Z"
        fee_type = str(item.get("fee_type") or item.get("type") or "stripe_processing_fee")

        fees.append(
            Fee(
                source_id=SourceRecordId(rec_id),
                amount=money_amt,
                fee_type=fee_type,
                charged_at=created,
                provenance=provenance,
            )
        )

    def _parse_payout(
        self,
        item: Mapping[str, object],
        rec_id: str,
        provenance: DataProvenance,
        payouts: list[Payout],
        batches: list[SettlementBatch],
    ) -> None:
        curr = self._parse_currency(item)
        money_amt = self._parse_amount(item, curr)
        arrival = str(item.get("arrival_date") or item.get("created") or "").strip() or "1970-01-01T00:00:00Z"
        batch_id = str(item.get("batch_id") or item.get("batch") or "")
        ref = str(item.get("payout_reference") or item.get("reference") or rec_id)

        payouts.append(
            Payout(
                source_id=SourceRecordId(rec_id),
                amount=money_amt,
                batch_source_id=SourceRecordId(batch_id) if batch_id else None,
                paid_at=arrival,
                provenance=provenance,
                payout_reference=ref,
            )
        )

        if batch_id:
            batches.append(
                SettlementBatch(
                    source_id=SourceRecordId(batch_id),
                    batch_number=batch_id,
                    closed_at=arrival,
                    provenance=provenance,
                )
            )

    def _parse_adjustment(
        self,
        item: Mapping[str, object],
        rec_id: str,
        provenance: DataProvenance,
        adjustments: list[Adjustment],
    ) -> None:
        curr = self._parse_currency(item)
        money_amt = self._parse_amount(item, curr)
        created = str(item.get("created", "")).strip() or "1970-01-01T00:00:00Z"
        adj_type = str(item.get("adjustment_type") or item.get("reason") or "dispute")

        adjustments.append(
            Adjustment(
                source_id=SourceRecordId(rec_id),
                amount=money_amt,
                adjustment_type=adj_type,
                applied_at=created,
                provenance=provenance,
            )
        )

    def _parse_deposit(
        self,
        item: Mapping[str, object],
        rec_id: str,
        provenance: DataProvenance,
        deposits: list[BankDeposit],
    ) -> None:
        curr = self._parse_currency(item)
        money_amt = self._parse_amount(item, curr)
        posted = str(item.get("posted_at") or item.get("posted") or "").strip() or "1970-01-01T00:00:00Z"
        narr = str(item.get("narration") or item.get("description") or "STRIPE PAYOUT")
        last3 = str(item.get("bank_account_last3") or "999")

        deposits.append(
            BankDeposit(
                source_id=SourceRecordId(rec_id),
                amount=money_amt,
                posted_at=posted,
                narration=narr,
                bank_account_last3=last3,
                provenance=provenance,
            )
        )
