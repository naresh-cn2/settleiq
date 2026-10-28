"""The matching engine.

Implements the evaluation semantics resolved in `16` §B.1 and §B.5:

1. every applicable rule is evaluated;
2. a rule yields a candidate set, never a decision;
3. exactly one deterministic rule -> DETERMINISTIC;
4. two or more deterministic rules that agree -> DETERMINISTIC, agreement recorded;
5. two or more deterministic rules that disagree -> RULE_CONFLICT, a typed break,
   and the engine does **not** choose;
6. no deterministic rule, but a multi-candidate rule fired -> AMBIGUOUS with the
   complete surviving set and nothing selected;
7. no applicable rule -> INSUFFICIENT_EVIDENCE.

Fail-closed throughout (SETTLEIQ-REQ-009).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Final, Mapping, Sequence

from settleiq.canonical.serialization import digest
from settleiq.money import Money

__all__ = [
    "Confidence",
    "MatchDecision",
    "MatchRule",
    "RuleRegistry",
    "RULE_VERSION",
    "default_registry",
    "evaluate",
]

#: Bump when any rule, its precedence, or its eligible fields change.
RULE_VERSION: Final[str] = "1.0.0"


class Confidence(str, Enum):
    """A classification, never a numeric score.

    A numeric score is prohibited: it would create a false ordering among
    candidates the engine cannot distinguish (`16` §B.1).
    """

    DETERMINISTIC = "DETERMINISTIC"
    AMBIGUOUS = "AMBIGUOUS"
    RULE_CONFLICT = "RULE_CONFLICT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class Candidate:
    """A candidate record, in canonical form."""

    candidate_id: str
    kind: str
    amount: str
    currency: str
    date: str
    reference: str

    def to_canonical(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "kind": self.kind,
            "amount": self.amount,
            "currency": self.currency,
            "date": self.date,
            "reference": self.reference,
        }

    def key(self) -> tuple[str, str]:
        """Identity of the candidate for agreement comparison."""
        return (self.amount, self.reference)


@dataclass(frozen=True)
class MatchRule:
    """A versioned, precedence-ranked matching rule.

    The predicate receives the constituent and the candidate in canonical form
    and returns a bool. ``consumed_fields`` is declared so provenance names the
    fields a match actually depended on.
    """

    rule_id: str
    version: str
    precedence_rank: int
    consumed_fields: tuple[str, ...]
    predicate: Callable[[Mapping[str, object], Candidate], bool]

    def matches(self, constituent: Mapping[str, object], candidate: Candidate) -> bool:
        try:
            return bool(self.predicate(constituent, candidate))
        except Exception:  # noqa: BLE001 - a malformed pair simply does not match
            return False


@dataclass(frozen=True)
class RuleRegistry:
    """An explicitly ordered rule set.

    Duplicate precedence ranks are rejected at load (AC-B5-01): an ambiguous
    ordering would make results depend on insertion order.
    """

    version: str
    rules: tuple[MatchRule, ...]

    def __post_init__(self) -> None:
        ranks = [rule.precedence_rank for rule in self.rules]
        duplicates = sorted({r for r in ranks if ranks.count(r) > 1})
        if duplicates:
            raise ValueError(
                f"rule registry has duplicate precedence rank(s): {duplicates}; "
                "ordering must be total"
            )
        object.__setattr__(
            self, "rules", tuple(sorted(self.rules, key=lambda r: r.precedence_rank))
        )

    def ordered(self) -> tuple[MatchRule, ...]:
        return self.rules


def _reference(constituent: Mapping[str, object]) -> str:
    return str(constituent.get("reference", ""))


def _amount(constituent: Mapping[str, object]) -> Money | None:
    raw = constituent.get("amount")
    currency = constituent.get("currency")
    if raw is None or currency is None:
        return None
    return Money(str(raw), str(currency))


def _make_rules() -> tuple[MatchRule, ...]:
    def same_reference(c: Mapping[str, object], x: Candidate) -> bool:
        left = _reference(c)
        return bool(left) and left == x.reference

    def same_amount(c: Mapping[str, object], x: Candidate) -> bool:
        left = _amount(c)
        if left is None or not x.amount:
            return False
        return left.to_canonical() == f"{x.amount}|{x.currency}"

    return (
        MatchRule(
            rule_id="R-EXACT-REFERENCE",
            version="1.0.0",
            precedence_rank=10,
            consumed_fields=("reference",),
            predicate=same_reference,
        ),
        MatchRule(
            rule_id="R-EXACT-AMOUNT",
            version="1.0.0",
            precedence_rank=20,
            consumed_fields=("amount", "currency"),
            predicate=same_amount,
        ),
    )


RULES: Final[tuple[MatchRule, ...]] = _make_rules()


def default_registry() -> RuleRegistry:
    return RuleRegistry(version=RULE_VERSION, rules=RULES)


@dataclass(frozen=True)
class MatchDecision:
    """The provenance-carrying record of one comparison.

    Carries the complete surviving candidate set when ambiguous, with **no**
    member marked selected (`16` §B.1).
    """

    constituent_kind: str
    constituent_id: str
    confidence: Confidence
    applied_rule_ids: tuple[str, ...] = ()
    applied_rule_version: str = ""
    consumed_fields: tuple[str, ...] = ()
    surviving_candidates: tuple[Candidate, ...] = ()
    matched_candidate: Candidate | None = None

    def to_canonical(self) -> dict[str, object]:
        return {
            "constituent_kind": self.constituent_kind,
            "constituent_id": self.constituent_id,
            "confidence": self.confidence.value,
            "applied_rule_ids": list(self.applied_rule_ids),
            "applied_rule_version": self.applied_rule_version,
            "consumed_fields": list(self.consumed_fields),
            "surviving_candidates": [c.to_canonical() for c in self.surviving_candidates],
            "matched_candidate": (
                self.matched_candidate.to_canonical() if self.matched_candidate else None
            ),
        }

    def provenance_digest(self) -> str:
        return digest(self.to_canonical())


def evaluate(
    constituent: Mapping[str, object],
    candidates: Sequence[Candidate],
    registry: RuleRegistry,
) -> MatchDecision:
    """Evaluate one constituent against its candidates under the declared semantics."""
    applied: list[str] = []
    consumed: list[str] = []
    deterministic_winner: Candidate | None = None
    deterministic_winners: list[Candidate] = []
    ambiguous_set: tuple[Candidate, ...] = ()

    for rule in registry.ordered():
        matching = [c for c in candidates if rule.matches(constituent, c)]
        if not matching:
            continue
        applied.append(rule.rule_id)
        consumed.extend(rule.consumed_fields)
        if len(matching) == 1:
            deterministic_winners.append(matching[0])
        else:
            # More than one candidate survived this rule. Preserve the set whole;
            # select nothing (`16` §B.1).
            ambiguous_set = tuple(matching)

    kind = str(constituent.get("kind", ""))
    identifier = str(constituent.get("id", ""))

    # Two deterministic rules that disagree.
    distinct_winners = {c.key() for c in deterministic_winners}
    if len(distinct_winners) > 1:
        return MatchDecision(
            constituent_kind=kind,
            constituent_id=identifier,
            confidence=Confidence.RULE_CONFLICT,
            applied_rule_ids=tuple(applied),
            applied_rule_version=registry.version,
            consumed_fields=tuple(consumed),
            surviving_candidates=tuple(deterministic_winners),
        )

    # One deterministic outcome, possibly agreed by several rules.
    if len(distinct_winners) == 1:
        deterministic_winner = deterministic_winners[0]
        return MatchDecision(
            constituent_kind=kind,
            constituent_id=identifier,
            confidence=Confidence.DETERMINISTIC,
            applied_rule_ids=tuple(applied),
            applied_rule_version=registry.version,
            consumed_fields=tuple(consumed),
            surviving_candidates=(deterministic_winner,),
            matched_candidate=deterministic_winner,
        )

    # No deterministic outcome, but a multi-candidate rule fired.
    if ambiguous_set:
        return MatchDecision(
            constituent_kind=kind,
            constituent_id=identifier,
            confidence=Confidence.AMBIGUOUS,
            applied_rule_ids=tuple(applied),
            applied_rule_version=registry.version,
            consumed_fields=tuple(consumed),
            surviving_candidates=ambiguous_set,
        )

    return MatchDecision(
        constituent_kind=kind,
        constituent_id=identifier,
        confidence=Confidence.INSUFFICIENT_EVIDENCE,
        applied_rule_ids=tuple(applied),
        applied_rule_version=registry.version,
        consumed_fields=tuple(consumed),
    )
