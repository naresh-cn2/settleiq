"""Data provenance.

Every canonical record carries its provenance. `SYNTHETIC` is the only value the
first-build generator produces. `AUTHORIZED_REAL` cannot be set by any
production code path without an explicit authorization record
(SETTLEIQ-M1-001 AC-8-01/02, `16` §B.8).
"""

from __future__ import annotations

from enum import Enum

__all__ = ["DataProvenance", "is_real_data_authorized"]


class DataProvenance(str, Enum):
    """Where a record came from.

    Provenance is metadata, never a branch: the engine's behaviour is identical
    for both values, and a test asserts that (AC-B8-02).
    """

    SYNTHETIC = "SYNTHETIC"
    AUTHORIZED_REAL = "AUTHORIZED_REAL"

    @property
    def is_synthetic(self) -> bool:
        return self is DataProvenance.SYNTHETIC


class _AuthorizationLedger:
    """Holds real-data authorizations.

    Deliberately in-memory and empty. A real authorization would require a
    documented data-governance decision by the OWNER; nothing in the first build
    grants one, and the class exists so that the gate is visible rather than
    inferred.
    """

    __slots__ = ("_tokens",)

    def __init__(self) -> None:
        self._tokens: set[str] = set()

    def grant(self, token: str) -> None:
        if not token or not token.strip():
            raise ValueError("an authorization token must be non-empty")
        self._tokens.add(token.strip())

    def is_granted(self) -> bool:
        return bool(self._tokens)


_AUTHORIZATIONS = _AuthorizationLedger()


def is_real_data_authorized() -> bool:
    """True only when the OWNER has granted a real-data authorization."""
    return _AUTHORIZATIONS.is_granted()


def require_synthetic_or_authorized(provenance: DataProvenance) -> None:
    """Fail closed when real data is requested without authorization."""
    if provenance is DataProvenance.AUTHORIZED_REAL and not is_real_data_authorized():
        raise PermissionError(
            "AUTHORIZED_REAL provenance requires an explicit data-governance "
            "authorization, which has not been granted"
        )
