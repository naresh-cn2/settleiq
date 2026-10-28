"""Canonical financial data model."""

from __future__ import annotations

from .entities import (
    Adjustment,
    BankDeposit,
    Charge,
    ConstituentType,
    Fee,
    Payout,
    ReconciliationRun,
    Refund,
    Residual,
    SettlementBatch,
    SourceRecordId,
    stable_digest,
)
from .provenance import (
    DataProvenance,
    is_real_data_authorized,
    require_synthetic_or_authorized,
)
from .run_identity import RULE_VERSION, SCHEMA_VERSION, RunIdentity

__all__ = [
    "RULE_VERSION",
    "SCHEMA_VERSION",
    "Adjustment",
    "BankDeposit",
    "Charge",
    "ConstituentType",
    "DataProvenance",
    "Fee",
    "Payout",
    "ReconciliationRun",
    "Refund",
    "Residual",
    "RunIdentity",
    "SettlementBatch",
    "SourceRecordId",
    "is_real_data_authorized",
    "require_synthetic_or_authorized",
    "stable_digest",
]
