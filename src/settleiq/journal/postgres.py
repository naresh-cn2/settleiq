"""PostgreSQL implementation of the hash-chained audit journal.

Mirrors the SQLite Journal interface but uses a PostgreSQL connection.
"""
from __future__ import annotations

import json
from contextlib import closing, contextmanager

from settleiq.canonical.serialization import digest
from settleiq.journal.chain import JournalEntry, TamperReport, TamperType

try:
    import psycopg
    PSYCOPG_VERSION = 3
except ImportError:
    import psycopg2 as psycopg
    PSYCOPG_VERSION = 2


class PostgresJournal:
    """An append-only hash-chained journal backed by PostgreSQL."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    @contextmanager
    def _connect(self):
        conn = psycopg.connect(self.dsn) if PSYCOPG_VERSION == 3 else psycopg.connect(self.dsn)
        try:
            yield conn
        finally:
            conn.close()

    def migrate(self) -> None:
        """Create the journal_entry table if it doesn't exist."""
        with self._connect() as conn, closing(conn.cursor()) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS journal_entry (
                    sequence       BIGSERIAL PRIMARY KEY,
                    prev_digest    TEXT NOT NULL,
                    entry_digest   TEXT NOT NULL,
                    payload        JSONB NOT NULL,
                    recorded_at    TIMESTAMPTZ NOT NULL
                )
            """)
            conn.commit()

    def _head(self, cursor) -> tuple[int, str]:
        cursor.execute(
            "SELECT sequence, entry_digest FROM journal_entry "
            "ORDER BY sequence DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row is None:
            return 0, "0" * 64
        return int(row[0]), str(row[1])

    def entries(self) -> list:
        with self._connect() as conn, closing(conn.cursor()) as cur:
            cur.execute("""
                SELECT sequence, prev_digest, entry_digest, payload, recorded_at
                FROM journal_entry ORDER BY sequence
            """)
            rows = cur.fetchall()
        entries = []
        for row in rows:
            entries.append(
                JournalEntry(
                    sequence=int(row[0]),
                    prev_digest=str(row[1]),
                    entry_digest=str(row[2]),
                    payload=row[3] if isinstance(row[3], dict) else json.loads(str(row[3])),
                    recorded_at=str(row[4]),
                )
            )
        return entries

    def verify(self) -> TamperReport:
        """Recompute every digest from the stored payloads and compare."""
        stored = self.entries()
        findings = []
        expected_prev = "0" * 64
        expected_sequence = 1
        head = "0" * 64

        for entry in stored:
            if entry.sequence != expected_sequence:
                findings.append((
                    entry.sequence,
                    TamperType.CHAIN_BREAK,
                    f"expected sequence {expected_sequence}",
                ))
            # Recompute digest
            serialized = json.dumps(dict(entry.payload), sort_keys=True, separators=(",", ":"))
            computed = digest({"prev": entry.prev_digest, "payload": serialized})
            if entry.prev_digest != expected_prev:
                findings.append(
                    (entry.sequence, TamperType.DIGEST_MODIFIED, "prev_digest mismatch")
                )
            if entry.entry_digest != computed:
                findings.append(
                    (entry.sequence, TamperType.PAYLOAD_MODIFIED, "entry_digest mismatch")
                )
            expected_prev = entry.entry_digest
            expected_sequence += 1
            head = entry.entry_digest

        # Check for empty payload with non-genesis digest (handshake)
        for entry in stored:
            if not entry.payload and entry.entry_digest != ("0" * 64):
                findings.append(
                    (entry.sequence, TamperType.HANDSHAKE_DIGEST, "empty payload")
                )

        return TamperReport(
            intact=not findings,
            findings=tuple(findings),
            entries_verified=len(stored),
            head_digest=head,
        )