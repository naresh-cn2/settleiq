"""Instrumented metrics with a published methodology.

The rate is computed from recorded counts and the methodology is code, not
prose. SettleIQ does not claim any vendor lacks such a methodology — it
*demonstrates the practice on itself*, on data a third party can inspect
(SETTLEIQ-REQ-013/014).

The methodology deliberately separates:
* the **denominator** — records eligible, defined below;
* the **numerator** — records matched deterministically;
* **human-confirmed** matches, counted separately and never merged in.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

__all__ = [
    "DENOMINATOR_DEFINITION",
    "METHODOLOGY_VERSION",
    "Metrics",
    "compute",
]

METHODOLOGY_VERSION: Final[str] = "1.0.0"

#: The denominator definition, stated in code so it can be audited and changed
#: only as a versioned act.
DENOMINATOR_DEFINITION: Final[str] = (
    "eligible records: every charge and payout constituent presented to the "
    "matching engine, plus every bank deposit and processor-side record that "
    "produced a presence/absence break. A record quarantined at ingestion is "
    "excluded from the denominator and reported separately."
)

NUMERATOR_DEFINITION: Final[str] = (
    "deterministic matches: records for which exactly one candidate survived a "
    "declared rule, or two or more rules resolved to the same candidate."
)


@dataclass(frozen=True)
class Metrics:
    """A computed metric set with its methodology attached."""

    numerator: int
    denominator: int
    human_confirmed: int
    ambiguous: int
    conflict: int
    insufficient: int
    quarantined: int
    rate: float
    methodology_version: str = METHODOLOGY_VERSION
    denominator_definition: str = DENOMINATOR_DEFINITION
    numerator_definition: str = NUMERATOR_DEFINITION
    human_confirmation_treatment: str = (
        "human-confirmed matches are counted separately and are never included "
        "in the numerator"
    )

    def to_canonical(self) -> dict[str, object]:
        return {
            "numerator": self.numerator,
            "denominator": self.denominator,
            "rate": self.rate,
            "human_confirmed": self.human_confirmed,
            "ambiguous": self.ambiguous,
            "conflict": self.conflict,
            "insufficient": self.insufficient,
            "quarantined": self.quarantined,
            "methodology_version": METHODOLOGY_VERSION,
            "denominator_definition": DENOMINATOR_DEFINITION,
            "numerator_definition": NUMERATOR_DEFINITION,
            "human_confirmation_treatment": (
                "human-confirmed matches are counted separately and are never "
                "included in the numerator"
            ),
        }


def compute(counts: Mapping[str, int]) -> Metrics:
    """Compute the rate from instrumented counts.

    Returns a rate of 0.0 when the denominator is 0, because an empty run has no
    match rate — a division that would otherwise raise.
    """
    denominator = int(counts.get("eligible", 0))
    numerator = int(counts.get("deterministic", 0))
    human_confirmed = int(counts.get("human_confirmed", 0))
    rate = (numerator / denominator) if denominator else 0.0
    return Metrics(
        numerator=numerator,
        denominator=denominator,
        human_confirmed=human_confirmed,
        ambiguous=int(counts.get("ambiguous", 0)),
        conflict=int(counts.get("conflict", 0)),
        insufficient=int(counts.get("insufficient", 0)),
        quarantined=int(counts.get("quarantined", 0)),
        rate=rate,
    )
