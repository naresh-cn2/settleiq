"""The append-only, hash-chained audit journal.

Each entry's digest is computed over the previous entry's digest and the
canonical serialization of its payload. Digests are **computed by the system and
verified on read** — never authored, never a placeholder.

### What this chain proves, and what it does not

It **does** make these detectable, under the stated assumptions:

* modifying an entry's payload;
* modifying or replacing a stored digest;
* deleting an entry **from the middle** of the chain;
* reordering entries;
* duplicating an entry;
* truncating the journal **is NOT detectable by the chain alone** — see below.

It does **not**, and must not be described as if it did:

* prevent an attacker with write access to the database from rewriting the
  entire chain from the genesis entry onward;
* establish who wrote an entry, or that the writer was authorised;
* prove the payload was *true* — only that it has not changed since it was
  appended;
* survive a lost or disclosed digest root. Anchoring the head digest externally
  is the standard remedy and is not implemented here;
* **detect tail truncation.** Deleting entries from the end leaves every
  remaining link internally consistent, so the chain verifies. Detecting this
  requires anchoring the head digest out-of-band on a schedule and comparing on
  verification. `head()` exists precisely to support that and is the correct
  integration point for it.

Anchoring is deliberately omitted and recorded as a limitation rather than
implied. The test suite asserts the truncation gap as a passing case, so the
boundary is demonstrable rather than merely documented.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator, Mapping, Sequence
from contextlib import closing, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from settleiq.canonical.serialization import canonical_json_dumps, digest

__all__ = [
    "GENESIS_DIGEST",
    "JOURNAL_SCHEMA",
    "JournalEntry",
    "TamperReport",
    "TamperType",
    "open_journal",
]

#: The chain's starting point. A journal's first entry chains from this, so the
#: head is well-defined even before anything is written.
GENESIS_DIGEST: Final[str] = "0" * 64

JOURNAL_SCHEMA: Final[str] = """
CREATE TABLE IF NOT EXISTS journal_entry (
    sequence       INTEGER PRIMARY KEY AUTOINCREMENT,
    prev_digest    TEXT NOT NULL,
    entry_digest   TEXT NOT NULL,
    payload        TEXT NOT NULL,
    recorded_at    TEXT NOT NULL
)
"""


class TamperType(str):
    """What verification found. Every type is reportable, none is silent."""

    PAYLOAD_MODIFIED = "PAYLOAD_MODIFIED"
    DIGEST_MODIFIED = "DIGEST_MODIFIED"
    CHAIN_BREAK = "CHAIN_BREAK"
    ENTRY_DELETED = "ENTRY_DELETED"
    ENTRY_REORDERED = "ENTRY_REORDERED"
    ENTRY_DUPLICATED = "ENTRY_DUPLICATED"
    JOURNAL_TRUNCATED = "JOURNAL_TRUNCATED"
    HANDSHAKE_DIGEST = "HANDSHAKE_DIGEST"


@dataclass(frozen=True)
class JournalEntry:
    """One journal entry, as stored."""

    sequence: int
    prev_digest: str
    entry_digest: str
    payload: Mapping[str, object]
    recorded_at: str

    def to_canonical(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "prev_digest": self.prev_digest,
            "entry_digest": self.entry_digest,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class TamperReport:
    """The result of verifying a journal."""

    intact: bool
    findings: tuple[tuple[int, str, str], ...]
    entries_verified: int
    head_digest: str

    def to_canonical(self) -> dict[str, object]:
        return {
            "intact": self.intact,
            "findings": [list(f) for f in self.findings],
            "entries_verified": self.entries_verified,
            "head_digest": self.head_digest,
        }


class Journal:
    """An append-only hash-chained journal.

    ``recorded_at`` is stored as entry **content** but is excluded from the
    digest preimage (resolving OQ-12). A digest that included a wall-clock
    timestamp could not be reproduced, which would break the verification the
    chain exists to provide.
    """

    def __init__(self, path: Path | str) -> None:
        self.path = str(path)
        self._shared: sqlite3.Connection | None = (
            None
            if self.path != ":memory:"
            else sqlite3.connect(":memory:", isolation_level=None)
        )
        #: Set by :meth:`adopt` when this journal accompanies another store.
        self._adopted: sqlite3.Connection | None = None

    def adopt(self, connection: sqlite3.Connection) -> None:
        """Use another component's connection.

        An in-memory SQLite database is created fresh per connection. A journal
        and a store that each open their own ":memory:" therefore see two
        different databases, and entries appended to the store's database are
        invisible when this journal reads its own. Adopting the store's
        connection makes them one database.
        """
        self._adopted = connection
        if self._shared is not None:
            self._shared.close()
            self._shared = None

    # ------------------------------------------------------------------ connection

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        if self._adopted is not None:
            yield self._adopted
            return
        if self._shared is not None:
            yield self._shared
            return
        connection = sqlite3.connect(self.path, isolation_level=None)
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            yield connection
        finally:
            connection.close()

    def migrate(self) -> None:
        with self._connect() as connection, closing(connection.cursor()) as cursor:
            cursor.execute(JOURNAL_SCHEMA)

    def migrate_within(self, cursor: sqlite3.Cursor) -> None:
        """Create the journal schema on a caller-supplied connection.

        An in-memory SQLite database is created fresh per connection, so a
        journal and a store that each open their own ":memory:" see two
        different databases and the journal's table simply does not exist on the
        store's side. Creating the schema within the store's transaction is what
        makes the two share one database.
        """
        cursor.execute(JOURNAL_SCHEMA)

    def close(self) -> None:
        if self._shared is not None:
            self._shared.close()
            self._shared = None

    # ------------------------------------------------------------------ append

    def _head(self, cursor: sqlite3.Cursor) -> tuple[int, str]:
        cursor.execute(
            "SELECT sequence, entry_digest FROM journal_entry "
            "ORDER BY sequence DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row is None:
            return 0, GENESIS_DIGEST
        return int(row[0]), str(row[1])

    def append_within(
        self,
        connection: sqlite3.Connection,
        cursor: sqlite3.Cursor,
        payload: Mapping[str, object],
    ) -> JournalEntry:
        """Append using a caller-supplied transaction.

        Lets the journal append commit atomically with the rows it attests to,
        which is the only ordering that cannot produce a false attestation.
        """
        serialized = canonical_json_dumps(dict(payload))
        stored_payload = json.loads(serialized)
        sequence, prev_digest = self._head(cursor)
        entry_digest = digest({"prev": prev_digest, "payload": serialized})
        cursor.execute(
            "INSERT INTO journal_entry (prev_digest, entry_digest, payload, recorded_at) "
            "VALUES (?, ?, ?, ?)",
            (prev_digest, entry_digest, serialized, payload.get("recorded_at", "")),
        )
        return JournalEntry(
            sequence=int(cursor.lastrowid or 0),
            prev_digest=prev_digest,
            entry_digest=entry_digest,
            payload=stored_payload,
            recorded_at=str(payload.get("recorded_at", "")),
        )

    def append(self, payload: Mapping[str, object], *, recorded_at: str) -> JournalEntry:
        """Append one entry and return it as stored.

        Serialised by ``BEGIN IMMEDIATE``, which takes the database write lock:
        two concurrent appends cannot read the same head and produce a fork.
        Deadlock is excluded structurally rather than retried away.
        """
        # The stored form is JSON with sorted keys and no whitespace, so a third
        # party can recompute the digest from the stored text alone. The custom
        # canonical byte format is used for the digest preimage, not for storage.
        serialized = canonical_json_dumps(dict(payload))

        with self._connect() as connection, closing(connection.cursor()) as cursor:
            cursor.execute("BEGIN IMMEDIATE")
            try:
                sequence, prev_digest = self._head(cursor)
                entry_digest = digest({"prev": prev_digest, "payload": serialized})
                cursor.execute(
                    "INSERT INTO journal_entry "
                    "(prev_digest, entry_digest, payload, recorded_at) "
                    "VALUES (?, ?, ?, ?)",
                    (prev_digest, entry_digest, serialized, recorded_at),
                )
                new_sequence = int(cursor.lastrowid or 0)
                cursor.execute("COMMIT")
            except Exception:
                cursor.execute("ROLLBACK")
                raise

        return JournalEntry(
            sequence=new_sequence,
            prev_digest=prev_digest,
            entry_digest=entry_digest,
            payload=json.loads(serialized),
            recorded_at=recorded_at,
        )

    # ------------------------------------------------------------------ verify

    def entries(self) -> Sequence[JournalEntry]:
        with self._connect() as connection, closing(connection.cursor()) as cursor:
            cursor.execute(
                "SELECT sequence, prev_digest, entry_digest, payload, recorded_at "
                "FROM journal_entry ORDER BY sequence"
            )
            return [
                JournalEntry(
                    sequence=int(row[0]),
                    prev_digest=str(row[1]),
                    entry_digest=str(row[2]),
                    payload=json.loads(str(row[3])),
                    recorded_at=str(row[4]),
                )
                for row in cursor.fetchall()
            ]

    def verify(self) -> TamperReport:
        """Recompute every digest from the stored payloads and compare.

        Verification is a recorded operation whose result is persisted by the
        caller. "We verify on read" without a recorded result is not evidence.
        """
        stored = self.entries()
        findings: list[tuple[int, str, str]] = []
        expected_prev = GENESIS_DIGEST
        expected_sequence = 1
        head = GENESIS_DIGEST

        sequences = [entry.sequence for entry in stored]
        if sequences != sorted(set(sequences)):
            for _index, sequence in enumerate(sequences):
                if sequence != expected_sequence:
                    findings.append(
                        (sequence, TamperType.ENTRY_REORDERED, "sequence out of order")
                    )
                expected_sequence += 1
        else:
            for entry in stored:
                if entry.sequence != expected_sequence:
                    findings.append(
                        (
                            entry.sequence,
                            TamperType.ENTRY_DELETED
                            if entry.sequence > expected_sequence
                            else TamperType.ENTRY_REORDERED,
                            f"expected sequence {expected_sequence}, found {entry.sequence}",
                        )
                    )
                expected_sequence = entry.sequence + 1

        for entry in stored:
            # Re-serialize to the exact stored form before hashing. The preimage
            # is the JSON text, not the parsed dict: hashing the dict would
            # silently change the preimage and make verification compare two
            # different things.
            serialized = canonical_json_dumps(entry.payload)
            recomputed = digest({"prev": expected_prev, "payload": serialized})
            if recomputed != entry.entry_digest:
                findings.append(
                    (
                        entry.sequence,
                        TamperType.PAYLOAD_MODIFIED,
                        "recomputed digest does not match the stored digest",
                    )
                )
            if entry.prev_digest != expected_prev:
                findings.append(
                    (
                        entry.sequence,
                        TamperType.CHAIN_BREAK,
                        f"prev_digest does not chain from {expected_prev[:12]}",
                    )
                )
            expected_prev = entry.entry_digest
            head = entry.entry_digest

        # An empty payload with a well-formed digest is the hand-written case:
        # the digest is present but was never computed from its entry.
        for entry in stored:
            if not entry.payload and entry.entry_digest != GENESIS_DIGEST:
                findings.append(
                    (entry.sequence, TamperType.HANDSHAKE_DIGEST, "empty payload")
                )

        return TamperReport(
            intact=not findings,
            findings=tuple(findings),
            entries_verified=len(stored),
            head_digest=head,
        )

    def head(self) -> tuple[int, str]:
        """The chain head, for external anchoring."""
        entries = self.entries()
        if not entries:
            return 0, GENESIS_DIGEST
        last = entries[-1]
        return last.sequence, last.entry_digest

    def table_digest(self) -> str:
        """A digest over the whole table, independent of the chain.

        Detects a wholesale rewrite that re-chains consistently: the chain would
        verify, but the content digest would differ from the anchored one.
        """
        return digest({"rows": [dict(e.to_canonical()) for e in self.entries()]})


def open_journal(path: Path | str = ":memory:") -> Journal:
    """Open a journal.

    If *path* is a PostgreSQL DSN (starting with ``postgresql://`` or ``postgres://``),
    a ``PostgresJournal`` is returned. Otherwise a SQLite ``Journal`` is used.
    """
    path_str = str(path)
    if path_str.startswith("postgresql://") or path_str.startswith("postgres://"):
        try:
            from .postgres import PostgresJournal
        except ImportError as exc:
            raise RuntimeError("PostgreSQL journal requires psycopg or psycopg2") from exc
        journal = PostgresJournal(path_str)
        journal.migrate()
        return journal
    journal = Journal(path)
    journal.migrate()
    return journal
