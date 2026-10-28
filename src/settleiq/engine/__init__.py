"""The deterministic reconciliation and discrepancy engine."""

from __future__ import annotations

from .decompose import Constituent, Decomposition, decompose, extract_reference
from .discrepancy import (
    Discrepancy,
    DiscrepancyStatus,
    DiscrepancyType,
    Severity,
    classify,
    classify_break,
    severity_for,
)
from .metrics import (
    DENOMINATOR_DEFINITION,
    METHODOLOGY_VERSION,
    Metrics,
    compute,
)
from .reconcile import ReconciliationResult, RunParameters, reconcile
from .rules import (
    Candidate,
    Confidence,
    MatchDecision,
    MatchRule,
    RULE_VERSION,
    RuleRegistry,
    default_registry,
    evaluate,
)

__all__ = [
    "DENOMINATOR_DEFINITION",
    "METHODOLOGY_VERSION",
    "RULE_VERSION",
    "Candidate",
    "Confidence",
    "Constituent",
    "Decomposition",
    "Discrepancy",
    "DiscrepancyStatus",
    "DiscrepancyType",
    "MatchDecision",
    "MatchRule",
    "Metrics",
    "ReconciliationResult",
    "RunParameters",
    "RuleRegistry",
    "Severity",
    "classify",
    "classify_break",
    "compute",
    "default_registry",
    "decompose",
    "evaluate",
    "extract_reference",
    "reconcile",
    "severity_for",
]
