"""Run identity.

A run is identified by the tuple (input_digest, rule_version, schema_version).
`run_id` is derived from that tuple, never a random UUID, a client-supplied
value, or a database sequence (SETTLEIQ-M1-001 AC-4.01).

The observation window, when declared, is part of the input set and therefore
part of the digest. It is never sampled from ambient time — that is what makes
SETTLEIQ-REQ-013 compatible with REQ-012.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from settleiq.canonical.serialization import digest

__all__ = ["RunIdentity", "SCHEMA_VERSION"]

#: Bump when the canonical model or the persistence shape changes. Participates
#: in run identity, so two different schema versions are different runs.
SCHEMA_VERSION: Final[str] = "0.1.0"

#: Placeholder at M1: no rules exist yet, but the semantic is declared and the
#: identity tuple already carries it (AC-4.07).
RULE_VERSION: Final[str] = "0.0.0"


@dataclass(frozen=True, order=True)
class RunIdentity:
    """The declared identity of a reconciliation run."""

    input_digest: str
    rule_version: str
    schema_version: str

    @classmethod
    def derive(
        cls,
        *,
        inputs: dict[str, Any],
        rule_version: str = RULE_VERSION,
        schema_version: str = SCHEMA_VERSION,
    ) -> RunIdentity:
        input_digest = digest(inputs)
        return cls(
            input_digest=input_digest,
            rule_version=rule_version,
            schema_version=schema_version,
        )

    @property
    def run_id(self) -> str:
        """Derived, not generated. Identical tuple -> identical run_id."""
        return digest(
            {
                "input_digest": self.input_digest,
                "rule_version": self.rule_version,
                "schema_version": self.schema_version,
            }
        )

    def __str__(self) -> str:
        return f"{self.run_id[:16]}/{self.rule_version}/{self.schema_version}"
