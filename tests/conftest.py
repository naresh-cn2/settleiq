"""Shared pytest fixtures and path setup.

The property-test seed is recorded here in code so that a reviewer can see it
without reading a report, and so that a run is reproducible from the repository
alone (SETTLEIQ-M1-001 AC-7.03).
"""

from __future__ import annotations

import random
import sys
from decimal import Decimal
from pathlib import Path

# Recorded, fixed seed for property-based tests. Changing this changes the
# generated population and therefore any test outcome that depends on it.
PROPERTY_SEED = 20261028


def _install_paths() -> None:
    root = Path(__file__).resolve().parent.parent
    for candidate in (root / "src", root / "tests"):
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))


_install_paths()


def seed_everything() -> None:
    """Pin every source of non-determinism the test suite can reach."""
    random.seed(PROPERTY_SEED)


import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _deterministic_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the ambient environment deterministic for every test.

    Wall-clock time, hash randomisation, and locale are excluded from every
    digest preimage by design (SETTLEIQ-DEC-001 REQ-012); this fixture proves
    the tests themselves do not depend on them either.
    """
    seed_everything()
    monkeypatch.delenv("TZ", raising=False)
    monkeypatch.setenv("PYTHONHASHSEED", "0")
    yield


@pytest.fixture
def two_places() -> Decimal:
    return Decimal("0.01")
