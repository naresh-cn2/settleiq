"""The append-only, hash-chained audit journal.

The chain makes unauthorised modification *detectable* under stated assumptions.
It does not prevent a determined attacker with database write access from
rebuilding the chain from genesis. `chain.Journal` documents the boundary, and
`tests/integration/test_journal_integrity.py` demonstrates it with a test rather
than asserting it in prose.
"""

from __future__ import annotations

from .chain import (
    GENESIS_DIGEST,
    JOURNAL_SCHEMA,
    Journal,
    JournalEntry,
    TamperReport,
    TamperType,
    open_journal,
)

__all__ = [
    "GENESIS_DIGEST",
    "JOURNAL_SCHEMA",
    "Journal",
    "JournalEntry",
    "TamperReport",
    "TamperType",
    "open_journal",
]
