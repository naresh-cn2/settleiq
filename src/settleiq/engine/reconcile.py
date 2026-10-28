"""The reconciliation driver.

Takes a validated record set, decomposes each payout into its constituents,
matches at constituent level, and produces typed discrepancies plus
instrumented counts from which the auto-match rate is computed.

The observation window is a **declared input** recorded in the run identity. It
is never sampled from ambient time — that is what makes SETTLEIQ-REQ-013
compatible with REQ-012.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from settleiq.engine.decompose import Decomposition, decompose, extract_reference
from settleiq.engine.discrepancy import Discrepancy, classify, classify_break
from settleiq.engine.rules import (
    Candidate,
    Confidence,
    MatchDecision,
    RuleRegistry,
    default_registry,
    evaluate,
)
from settleiq.model.run_identity import RunIdentity

__all__ = ["ReconciliationResult", "RunParameters", "reconcile"]

#: The maximum permitted days between a payout's arrival date and its bank
#: deposit's posting date. A declared input, part of run identity.
DEFAULT_SETTLEMENT_WINDOW_DAYS: Final[int] = 3

#: Record kinds the canonical model understands. A validated record whose kind
#: is absent here is surfaced as UNKNOWN rather than silently dropped
#: (`16` section B.4).
_MODELLED_KINDS: Final[frozenset[str]] = frozenset(
    {"charge", "fee", "refund", "adjustment", "payout", "deposit"}
)


@dataclass(frozen=True)
class RunParameters:
    """Declared execution parameters, hashed into the run identity."""

    window_start: str
    window_end: str
    settlement_window_days: int = DEFAULT_SETTLEMENT_WINDOW_DAYS
    tolerance_amount: str = "0.00"
    registry: RuleRegistry | None = None

    def to_canonical(self) -> dict[str, object]:
        registry = self.registry or default_registry()
        return {
            "window_start": self.window_start,
            "window_end": self.window_end,
            "settlement_window_days": self.settlement_window_days,
            "tolerance_amount": self.tolerance_amount,
            "rule_version": registry.version,
        }

    def resolved_registry(self) -> RuleRegistry:
        return self.registry or default_registry()


def _kind_of(entry: Mapping[str, object]) -> str:
    return str(entry.get("kind", ""))


def _record_of(entry: Mapping[str, object]) -> Mapping[str, object]:
    record = entry.get("record")
    if not isinstance(record, Mapping):
        raise ValueError(f"validated entry has no record mapping: {entry!r}")
    return record


def _digest_of(entry: Mapping[str, object]) -> str:
    return str(entry.get("digest", ""))


def _by_kind(records: Sequence[Mapping[str, object]], kind: str) -> list[Mapping[str, object]]:
    return [_record_of(r) for r in records if _kind_of(r) == kind]


def _candidate(record: Mapping[str, object], kind: str) -> Candidate:
    return Candidate(
        candidate_id=str(record.get("id", "")),
        kind=kind,
        amount=str(record.get("amount", "")),
        currency=str(record.get("currency", "")),
        date=str(record.get("arrival_date") or record.get("posted") or ""),
        reference=str(record.get("batch") or extract_reference(str(record.get("narration", "")))),
    )


def _raw(record: Mapping[str, object], kind: str) -> dict[str, object]:
    """Canonical comparison view of a record.

    A deposit carries its settlement reference inside its narration, not in a
    `batch` field. Omitting that extraction would make the reference rule
    inapplicable to deposits and leave them resolved only by amount — which is
    exactly how two unrelated payouts of equal amounts create a false ambiguity.
    """
    return {
        "kind": kind,
        "id": str(record.get("id", "")),
        "amount": str(record.get("amount", "")),
        "currency": str(record.get("currency", "")),
        "reference": str(
            record.get("batch")
            or extract_reference(str(record.get("narration", "")))
        ),
        "date": str(record.get("arrival_date") or record.get("posted") or ""),
    }


def _days_between(start: str, end: str) -> int:
    from datetime import date

    left = date.fromisoformat(start)
    right = date.fromisoformat(end)
    return (right - left).days


@dataclass
class ReconciliationResult:
    """The outcome of one run, with instrumented counts."""

    identity: RunIdentity
    decisions: list[MatchDecision]
    discrepancies: list[Discrepancy]
    decompositions: list[Decomposition]
    counts: dict[str, int]

    @property
    def metrics(self):
        from settleiq.engine.metrics import compute

        return compute(self.counts)


def reconcile(
    records: Sequence[Mapping[str, object]],
    parameters: RunParameters,
) -> ReconciliationResult:
    """Reconcile a validated record set at constituent level."""
    registry = parameters.resolved_registry()

    charges = _by_kind(records, "charge")
    fees = _by_kind(records, "fee")
    refunds = _by_kind(records, "refund")
    adjustments = _by_kind(records, "adjustment")
    payouts = _by_kind(records, "payout")
    deposits = _by_kind(records, "deposit")

    all_records: list[Mapping[str, object]] = [
        {"kind": k, "record": r}
        for k, group in (
            ("charge", charges),
            ("fee", fees),
            ("refund", refunds),
            ("adjustment", adjustments),
        )
        for r in group
    ]

    decompositions: list[Decomposition] = []
    discrepancies: list[Discrepancy] = []
    # A payout/deposit pair whose amounts disagree is reported once, not once per
    # direction, so the discrepancy count is not inflated.
    reported_amount_breaks: set[str] = set()
    counts: dict[str, int] = {
        "eligible": 0,
        "deterministic": 0,
        "ambiguous": 0,
        "conflict": 0,
        "insufficient": 0,
        "human_confirmed": 0,
        "quarantined": 0,
        "rejected": 0,
    }

    # --- 1. decompose every payout and verify the composition closes
    payout_by_reference: dict[str, Mapping[str, object]] = {}
    for payout in payouts:
        reference = str(payout.get("batch", ""))
        payout_by_reference[reference] = payout
        decomposition = decompose(payout, all_records, rule_version=registry.version)
        decompositions.append(decomposition)
        counts["eligible"] += len(decomposition.constituents)

        if decomposition.closes_exactly:
            counts["deterministic"] += len(decomposition.constituents)
        else:
            counts["conflict"] += 1
            discrepancies.append(
                _composition_break(decomposition, parameters, registry)
            )

    # --- 2. a constituent whose batch has no payout is a phantom
    compositions = {d.batch_reference for d in decompositions}
    for kind, group in (
        ("charge", charges),
        ("fee", fees),
        ("refund", refunds),
        ("adjustment", adjustments),
    ):
        for record in group:
            reference = str(record.get("batch", ""))
            if reference in compositions:
                continue
            discrepancies.append(
                classify_break(
                    kind=kind,
                    side_holding="PROCESSOR",
                    record=record,
                    detail=(
                        f"{kind} in batch {reference!r} has no payout on the "
                        "processor side"
                    ),
                )
            )
            counts["eligible"] += 1
            counts["phantom_processor"] = counts.get("phantom_processor", 0) + 1

    # --- 3. payout -> bank deposit, with a declared settlement window
    deposit_candidates = [_candidate(d, "deposit") for d in deposits]
    for payout in payouts:
        decision = evaluate(_raw(payout, "payout"), deposit_candidates, registry)
        counts["eligible"] += 1

        if decision.confidence is Confidence.DETERMINISTIC:
            counts["deterministic"] += 1
            _check_settlement_timing(
                payout, decision.matched_candidate, parameters, discrepancies
            )
            _check_matched_amount(
                payout, decision.matched_candidate, parameters, discrepancies
            )
            if decision.matched_candidate is not None:
                reported_amount_breaks.add(
                    _pair_key(
                        str(payout.get("id", "")), decision.matched_candidate.candidate_id
                    )
                )
            continue

        counts[_key_for(decision.confidence)] += 1
        discrepancies.append(classify(decision))

    # --- 4. a deposit whose reference matches no payout
    payout_references = {str(p.get("batch", "")) for p in payouts}
    payout_candidates = [_candidate(p, "payout") for p in payouts]
    for deposit in deposits:
        reference = extract_reference(str(deposit.get("narration", "")))
        if reference not in payout_references:
            discrepancies.append(
                classify_break(
                    kind="deposit",
                    side_holding="BANK",
                    record=deposit,
                    detail="bank deposit reference matches no payout",
                )
            )
            counts["eligible"] += 1
            counts["phantom_bank"] = counts.get("phantom_bank", 0) + 1
            continue

        # The deposit also has candidates of its own. Two payouts sharing a
        # reference is an ambiguity the deposit must report, not resolve.
        decision = evaluate(_raw(deposit, "deposit"), payout_candidates, registry)
        counts["eligible"] += 1
        if decision.confidence is Confidence.DETERMINISTIC:
            counts["deterministic"] += 1
            # The payout->deposit pass already checked this pair's amounts.
            # Reporting the same break from both directions would inflate the
            # discrepancy count, so the pair key is tracked and skipped.
            pair = _pair_key(
                decision.matched_candidate.candidate_id
                if decision.matched_candidate
                else "",
                str(deposit.get("id", "")),
            )
            if pair in reported_amount_breaks:
                continue
            _check_matched_amount_for_deposit(
                decision.matched_candidate, deposit, parameters, discrepancies
            )
            reported_amount_breaks.add(pair)
        else:
            counts[_key_for(decision.confidence)] += 1
            discrepancies.append(classify(decision))

    # --- 5. a record kind the model does not model: UNKNOWN, not the nearest type
    for entry in records:
        kind = _kind_of(entry)
        if kind in _MODELLED_KINDS:
            continue
        record = _record_of(entry)
        discrepancies.append(
            _unknown_break(kind, str(record.get("id", "")), registry.version)
        )
        counts["eligible"] += 1
        counts["unknown"] = counts.get("unknown", 0) + 1

    identity = RunIdentity.derive(
        inputs={
            "records": [
                {"kind": _kind_of(r), "record": dict(_record_of(r)), "digest": _digest_of(r)}
                for r in records
            ],
            "parameters": parameters.to_canonical(),
        },
        rule_version=registry.version,
    )

    return ReconciliationResult(
        identity=identity,
        decisions=[],
        discrepancies=discrepancies,
        decompositions=decompositions,
        counts=counts,
    )


def _composition_break(
    decomposition: Decomposition, parameters: RunParameters, registry: RuleRegistry
) -> list[Discrepancy]:
    from settleiq.engine.discrepancy import Discrepancy, DiscrepancyType, severity_for

    return Discrepancy(
        discrepancy_id=f"dsc:NET_GROSS_BREAK:{decomposition.payout_id}",
        type=DiscrepancyType.NET_GROSS_BREAK,
        severity=severity_for(DiscrepancyType.NET_GROSS_BREAK),
        constituent_kind="payout",
        constituent_id=decomposition.payout_id,
        contributing_records=(),
        reason=(
            f"batch {decomposition.batch_reference!r} nets "
            f"{decomposition.net_expected.to_canonical()} but the payout paid "
            f"{decomposition.net_paid.to_canonical()}; residual "
            f"{decomposition.residual.to_canonical()}"
        ),
        age_days=0,
    )


def _check_settlement_timing(
    payout: Mapping[str, object],
    matched: Candidate | None,
    parameters: RunParameters,
    discrepancies: list[Discrepancy],
) -> None:
    if matched is None:
        return
    arrival = str(payout.get("arrival_date", ""))
    posted = matched.date
    if not arrival or not posted:
        return
    lag = _days_between(arrival, posted)
    if lag > parameters.settlement_window_days:
        from settleiq.engine.discrepancy import Discrepancy, DiscrepancyType, severity_for

        discrepancies.append(
            Discrepancy(
                discrepancy_id=f"dsc:TIMING_BREAK:{payout.get('id', '')}",
                type=DiscrepancyType.TIMING_BREAK,
                severity=severity_for(DiscrepancyType.TIMING_BREAK),
                constituent_kind="payout",
                constituent_id=str(payout.get("id", "")),
                contributing_records=(matched,),
                reason=(
                    f"payout arrived {arrival}, deposit posted {posted}: "
                    f"{lag} days exceeds the declared window of "
                    f"{parameters.settlement_window_days}"
                ),
                age_days=0,
            )
        )


_KEY: Final[Mapping[Confidence, str]] = {
    Confidence.AMBIGUOUS: "ambiguous",
    Confidence.RULE_CONFLICT: "conflict",
    Confidence.INSUFFICIENT_EVIDENCE: "insufficient",
}


def _key_for(confidence: Confidence) -> str:
    return _KEY[confidence]


def _check_matched_amount(
    payout: Mapping[str, object],
    matched: Candidate | None,
    parameters: RunParameters,
    discrepancies: list[Discrepancy],
) -> None:
    """A reference match whose amounts disagree is an AMOUNT_BREAK.

    Matching by reference establishes *which* records correspond; it does not
    establish that the money agrees. Checking both is what distinguishes a
    matched pair from a reconciled pair.
    """
    if matched is None or not matched.amount:
        return
    from settleiq.engine.discrepancy import DiscrepancyType, severity_for
    from settleiq.money import Money

    paid = Money(str(payout.get("amount", "")), str(payout.get("currency", "")))
    deposited = Money.from_canonical(f"{matched.amount}|{matched.currency}", matched.currency)
    if paid == deposited:
        return

    discrepancies.append(
        Discrepancy(
            discrepancy_id=f"dsc:AMOUNT_BREAK:{payout.get('id', '')}",
            type=DiscrepancyType.AMOUNT_BREAK,
            severity=severity_for(DiscrepancyType.AMOUNT_BREAK),
            constituent_kind="payout",
            constituent_id=str(payout.get("id", "")),
            contributing_records=(matched,),
            reason=(
                f"payout paid {paid.to_canonical()} but deposit posted "
                f"{deposited.to_canonical()}"
            ),
            age_days=0,
        )
    )


def _check_matched_amount_for_deposit(
    matched: Candidate | None,
    deposit: Mapping[str, object],
    parameters: RunParameters,
    discrepancies: list[Discrepancy],
) -> None:
    """The deposit-side counterpart of `_check_matched_amount`."""
    if matched is None or not matched.amount:
        return
    from settleiq.engine.discrepancy import DiscrepancyType, severity_for
    from settleiq.money import Money

    paid = Money.from_canonical(f"{matched.amount}|{matched.currency}", matched.currency)
    deposited = Money(str(deposit.get("amount", "")), str(deposit.get("currency", "")))
    if paid == deposited:
        return

    discrepancies.append(
        Discrepancy(
            discrepancy_id=f"dsc:AMOUNT_BREAK:{deposit.get('id', '')}",
            type=DiscrepancyType.AMOUNT_BREAK,
            severity=severity_for(DiscrepancyType.AMOUNT_BREAK),
            constituent_kind="deposit",
            constituent_id=str(deposit.get("id", "")),
            contributing_records=(matched,),
            reason=(
                f"deposit posted {deposited.to_canonical()} but its payout paid "
                f"{paid.to_canonical()}"
            ),
            age_days=0,
        )
    )


def _pair_key(payout_id: str, deposit_id: str) -> str:
    """Identify a payout/deposit pair independently of which side reported it."""
    return f"{payout_id}::{deposit_id}"


def _unknown_break(kind: str, record_id: str, rule_version: str) -> Discrepancy:
    from settleiq.engine.discrepancy import DiscrepancyType, severity_for

    return Discrepancy(
        discrepancy_id=f"dsc:UNKNOWN:{record_id}",
        type=DiscrepancyType.UNKNOWN,
        severity=severity_for(DiscrepancyType.UNKNOWN),
        constituent_kind=kind,
        constituent_id=record_id,
        reason=(
            f"record kind {kind!r} is not modelled by the canonical data model; "
            "classified UNKNOWN rather than forced into a named type"
        ),
        age_days=0,
    )
