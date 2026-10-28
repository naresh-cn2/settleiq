"""The discrepancy engine.

The taxonomy is **closed with an explicit UNKNOWN** (`16` §B.4). A break that
cannot be named is surfaced, never forced into the nearest type.

Presence/absence breaks distinguish **which side** holds the record, because
those are different investigations. A processor vendor publishes the same
distinction in its own open-settlement documentation.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Final

from settleiq.engine.rules import Candidate, Confidence, MatchDecision

__all__ = [
    "Discrepancy",
    "DiscrepancyStatus",
    "DiscrepancyType",
    "RESOLUTION_STATUSES",
    "Severity",
    "classify",
    "classify_break",
    "severity_for",
]


class DiscrepancyType(str, Enum):
    """The closed taxonomy. UNKNOWN is a first-class, countable outcome."""

    # presence and absence
    PHANTOM_PROCESSOR = "PHANTOM_PROCESSOR"
    PHANTOM_BANK = "PHANTOM_BANK"
    PHANTOM_LEDGER = "PHANTOM_LEDGER"
    LOST = "LOST"
    SIDE_MISMATCH = "SIDE_MISMATCH"

    # amount
    AMOUNT_BREAK = "AMOUNT_BREAK"
    ROUNDING_RESIDUAL = "ROUNDING_RESIDUAL"
    CURRENCY_BREAK = "CURRENCY_BREAK"

    # fee and composition
    FEE_MISATTRIBUTION = "FEE_MISATTRIBUTION"
    FEE_MISSING = "FEE_MISSING"
    NET_GROSS_BREAK = "NET_GROSS_BREAK"

    # timing
    TIMING_BREAK = "TIMING_BREAK"
    SETTLEMENT_LAG_BREAK = "SETTLEMENT_LAG_BREAK"

    # ambiguity and sufficiency
    AMBIGUOUS_MATCH = "AMBIGUOUS_MATCH"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    RULE_CONFLICT = "RULE_CONFLICT"

    # unclassified
    UNKNOWN = "UNKNOWN"


class Severity(str, Enum):
    """Derived from a declared matrix, never a manual judgement (`16` §B.6)."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DiscrepancyStatus(str, Enum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    RESOLVED = "RESOLVED"
    UNRESOLVABLE = "UNRESOLVABLE"


RESOLUTION_STATUSES: Final[tuple[DiscrepancyStatus, ...]] = tuple(DiscrepancyStatus)

#: Declared amount bands. The boundaries are a business judgement (OQ-10) and
#: are versioned with the taxonomy; changing them is a versioned change.
_AMOUNT_BANDS: Final[tuple[tuple[str, str, str], ...]] = (
    # (type prefix, band label, severity)
    ("AMOUNT_BREAK", "ANY", "HIGH"),
    ("NET_GROSS_BREAK", "ANY", "HIGH"),
    ("RULE_CONFLICT", "ANY", "HIGH"),
    ("CURRENCY_BREAK", "ANY", "HIGH"),
    # An unclassifiable break is high severity: the engine is telling us it does
    # not understand the data, which is the case that most needs a human.
    ("UNKNOWN", "ANY", "HIGH"),
    ("TIMING_BREAK", "ANY", "MEDIUM"),
    ("SETTLEMENT_LAG_BREAK", "ANY", "MEDIUM"),
    ("PHANTOM_", "ANY", "HIGH"),
    ("FEE_", "ANY", "MEDIUM"),
    ("AMBIGUOUS_MATCH", "ANY", "MEDIUM"),
    ("INSUFFICIENT_EVIDENCE", "ANY", "MEDIUM"),
    ("SIDE_MISMATCH", "ANY", "MEDIUM"),
)


def severity_for(discrepancy_type: DiscrepancyType, amount_band: str = "ANY") -> Severity:
    """Derive severity from the declared matrix.

    An unknown (type, band) pair raises rather than defaulting (AC-B6-03).
    """
    value = discrepancy_type.value
    for prefix, band, severity in _AMOUNT_BANDS:
        if value.startswith(prefix) and band == amount_band:
            return Severity(severity)
    raise KeyError(f"no declared severity for ({value}, {amount_band})")


@dataclass(frozen=True)
class Discrepancy:
    """One classified break, with its evidence and resolution state.

    ``age_days`` is derived from the run's declared clock, never ambient time
    (AC-B8-03 / `08` DSC-R12).
    """

    discrepancy_id: str
    type: DiscrepancyType
    severity: Severity
    constituent_kind: str
    constituent_id: str
    contributing_records: tuple[Candidate, ...] = ()
    decision: MatchDecision | None = None
    reason: str = ""
    age_days: int = 0
    status: DiscrepancyStatus = DiscrepancyStatus.OPEN
    resolution_history: tuple[Mapping[str, object], ...] = ()

    def to_canonical(self) -> dict[str, object]:
        return {
            "discrepancy_id": self.discrepancy_id,
            "type": self.type.value,
            "severity": self.severity.value,
            "constituent_kind": self.constituent_kind,
            "constituent_id": self.constituent_id,
            "contributing_records": [c.to_canonical() for c in self.contributing_records],
            "reason": self.reason,
            "age_days": self.age_days,
            "status": self.status.value,
        }


def classify(decision: MatchDecision, *, run_declared_day: int = 0) -> Discrepancy:
    """Turn a non-deterministic decision into a typed discrepancy.

    Only the non-deterministic classes reach here; a DETERMINISTIC decision is
    not a break.
    """
    type_for_confidence = {
        Confidence.AMBIGUOUS: DiscrepancyType.AMBIGUOUS_MATCH,
        Confidence.RULE_CONFLICT: DiscrepancyType.RULE_CONFLICT,
        Confidence.INSUFFICIENT_EVIDENCE: DiscrepancyType.INSUFFICIENT_EVIDENCE,
    }
    try:
        discrepancy_type = type_for_confidence[decision.confidence]
    except KeyError as exc:
        raise ValueError(
            f"cannot classify a {decision.confidence.value} decision as a discrepancy"
        ) from exc

    reason = {
        Confidence.AMBIGUOUS: (
            f"{len(decision.surviving_candidates)} candidates survived; "
            "the engine does not select among them"
        ),
        Confidence.RULE_CONFLICT: "two rules resolved deterministically to different records",
        Confidence.INSUFFICIENT_EVIDENCE: "no applicable rule resolved this record",
    }[decision.confidence]

    return Discrepancy(
        discrepancy_id=f"dsc:{decision.constituent_kind}:{decision.constituent_id}",
        type=discrepancy_type,
        severity=severity_for(discrepancy_type),
        constituent_kind=decision.constituent_kind,
        constituent_id=decision.constituent_id,
        contributing_records=decision.surviving_candidates,
        decision=decision,
        reason=reason,
        age_days=run_declared_day,
    )


def classify_break(
    *,
    kind: str,
    side_holding: str,
    record: Mapping[str, object],
    detail: str,
    run_declared_day: int = 0,
) -> Discrepancy:
    """Classify a presence/absence break, preserving which side holds the record.

    ``side_holding`` is ``PROCESSOR`` or ``BANK``. Collapsing the two would lose
    the investigation.
    """
    if side_holding == "PROCESSOR":
        discrepancy_type = DiscrepancyType.PHANTOM_PROCESSOR
    elif side_holding == "BANK":
        discrepancy_type = DiscrepancyType.PHANTOM_BANK
    else:
        raise ValueError(f"unknown side {side_holding!r}")

    candidate = Candidate(
        candidate_id=str(record.get("id", "")),
        kind=kind,
        amount=str(record.get("amount", "")),
        currency=str(record.get("currency", "")),
        date=str(record.get("arrival_date") or record.get("posted") or ""),
        reference=str(record.get("batch") or record.get("narration") or ""),
    )
    return Discrepancy(
        discrepancy_id=f"dsc:{discrepancy_type.value}:{candidate.candidate_id}",
        type=discrepancy_type,
        severity=severity_for(discrepancy_type),
        constituent_kind=kind,
        constituent_id=candidate.candidate_id,
        contributing_records=(candidate,),
        reason=detail,
        age_days=run_declared_day,
    )
