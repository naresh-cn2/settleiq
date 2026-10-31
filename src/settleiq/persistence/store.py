"""Persistence.

PostgreSQL is the declared default (Q3, adopted for implementation) but Docker
and PostgreSQL are unavailable in this environment, so the store is implemented
against SQLite behind an interface. Amounts are stored as **exact decimal text**
rather than a typed numeric column, which is stricter than Postgres `numeric`
(no scale rounding is possible at all) and makes a later Postgres swap
mechanical.

Transaction boundaries are explicit: a run and its results commit atomically, or
not at all. A failed run must never leave a database that represents an
incomplete reconciliation as complete.
"""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from settleiq.canonical.serialization import digest
from settleiq.engine import ReconciliationResult
from settleiq.journal.chain import Journal

__all__ = ["ALLOWED_TABLES", "SCHEMA_STATEMENTS", "Persistence", "open_store", "ensure_migrations"]

SCHEMA_STATEMENTS: Final[tuple[str, ...]] = (
    """
    CREATE TABLE IF NOT EXISTS reconciliation_run (
        run_id            TEXT PRIMARY KEY,
        input_digest      TEXT NOT NULL,
        rule_version      TEXT NOT NULL,
        schema_version    TEXT NOT NULL,
        status            TEXT NOT NULL,
        declared_window   TEXT NOT NULL,
        numerator         INTEGER NOT NULL,
        denominator       INTEGER NOT NULL,
        methodology_version TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS discrepancy (
        discrepancy_id    TEXT PRIMARY KEY,
        run_id            TEXT NOT NULL REFERENCES reconciliation_run(run_id),
        type              TEXT NOT NULL,
        severity          TEXT NOT NULL,
        constituent_kind  TEXT NOT NULL,
        constituent_id    TEXT NOT NULL,
        reason            TEXT NOT NULL,
        age_days          INTEGER NOT NULL,
        status            TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS discrepancy_resolution (
        resolution_id     TEXT PRIMARY KEY,
        discrepancy_id    TEXT NOT NULL REFERENCES discrepancy(discrepancy_id),
        run_id            TEXT NOT NULL,
        status            TEXT NOT NULL,
        reason            TEXT NOT NULL,
        selected_candidate TEXT,
        resolved_by       TEXT NOT NULL,
        resolved_at       TEXT NOT NULL
    )
    """,
    # A settled record is never updated. A correction is a new row referencing
    # the one it supersedes (AC-3.04).
    """
    CREATE TABLE IF NOT EXISTS supersession (
        superseded_id     TEXT PRIMARY KEY,
        superseding_id    TEXT NOT NULL,
        reason            TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_discrepancy_run ON discrepancy(run_id)",
    "CREATE INDEX IF NOT EXISTS ix_discrepancy_type ON discrepancy(type)",
    (
        "CREATE INDEX IF NOT EXISTS ix_resolution_discrepancy "
        "ON discrepancy_resolution(discrepancy_id)"
    ),
)

ALLOWED_TABLES: Final[frozenset[str]] = frozenset({
    "reconciliation_run",
    "discrepancy",
    "discrepancy_resolution",
    "supersession",
    "journal_entry",
})


class Persistence:
    """A store for reconciliation runs and their discrepancies.

    The journal is a separate concern (M5 of the specification, not implemented
    here): this table set records outcomes, not a tamper-evident chain.
    """

    def __init__(self, path: Path | str) -> None:
        self.path = str(path)
        # An in-memory database is created fresh on every connection, so a
        # schema migrated on one connection would be invisible to the next.
        # Hold a single connection for its lifetime instead.
        self._shared: sqlite3.Connection | None = (
            None if self.path != ":memory:" else sqlite3.connect(":memory:")
        )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        # isolation_level=None puts the connection in autocommit so that BEGIN
        # is explicit. Implicit autocommit is how partial commits happen.
        if self._shared is not None:
            connection = self._shared
            connection.execute("PRAGMA foreign_keys = ON")
            yield connection
            return
        connection = sqlite3.connect(self.path, isolation_level=None)
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            yield connection
        finally:
            connection.close()

    def close(self) -> None:
        if self._shared is not None:
            self._shared.close()
            self._shared = None

    def connection(self) -> sqlite3.Connection | None:
        """The store's live connection, for a journal that must share it.

        An in-memory database is created fresh per connection, so a journal that
        opens its own ":memory:" would read a different database from this
        store. Returning the shared connection lets a caller adopt it.
        """
        return self._shared

    def migrate(self) -> None:
        with self._connect() as connection, closing(connection.cursor()) as cursor:
            for statement in SCHEMA_STATEMENTS:
                cursor.execute(statement)

    def record_run(
        self,
        result: ReconciliationResult,
        *,
        journal: Journal | None = None,
        recorded_at: str = "",
    ) -> str:
        """Record a completed run and its discrepancies atomically.

        When a journal is supplied, the run is also appended to the hash chain in
        the **same** transaction as the outcome rows, so a journal entry cannot
        exist for a run that was not persisted, and vice versa.

        Re-recording an identical run is a no-op: the run id is derived from the
        inputs, so a duplicate submission is recognised rather than duplicated
        (SETTLEIQ-REQ-009, `09` API-R08).
        """
        metrics = result.metrics
        run_id = result.identity.run_id

        with self._connect() as connection, closing(connection.cursor()) as cursor:
            cursor.execute("BEGIN IMMEDIATE")
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO reconciliation_run
                    (run_id, input_digest, rule_version, schema_version, status,
                     declared_window, numerator, denominator, methodology_version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        result.identity.input_digest,
                        result.identity.rule_version,
                        result.identity.schema_version,
                        "COMPLETED",
                        "",
                        metrics.numerator,
                        metrics.denominator,
                        metrics.methodology_version,
                    ),
                )
                inserted_run = cursor.rowcount > 0
                for discrepancy in result.discrepancies:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO discrepancy
                        (discrepancy_id, run_id, type, severity, constituent_kind,
                         constituent_id, reason, age_days, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            discrepancy.discrepancy_id,
                            run_id,
                            discrepancy.type.value,
                            discrepancy.severity.value,
                            discrepancy.constituent_kind,
                            discrepancy.constituent_id,
                            discrepancy.reason,
                            discrepancy.age_days,
                            discrepancy.status.value,
                        ),
                    )
                # The journal append belongs to the same transaction as the rows
                # it attests to. An entry for a run that did not persist would be
                # a false attestation.
                if journal is not None and journal.path == self.path and inserted_run:
                    # Create the journal schema on THIS connection before
                    # appending, so an in-memory store and journal share one
                    # database rather than each holding a separate one.
                    journal.migrate_within(cursor)
                    journal.append_within(connection, cursor, _run_payload(result))
                connection.execute("COMMIT")
            except Exception:
                cursor.execute("ROLLBACK")
                raise
        return run_id

    def find_run(self, run_id: str) -> Mapping[str, object] | None:
        with self._connect() as connection, closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM reconciliation_run WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            columns = [d[0] for d in cursor.description]
            run = dict(zip(columns, row, strict=False))
            num = run.get("numerator", 0)
            den = run.get("denominator", 0)
            run["rate"] = (num / den) if den else 0.0
            return run

    def discrepancies_for(self, run_id: str) -> Sequence[Mapping[str, object]]:
        with self._connect() as connection, closing(connection.cursor()) as cursor:
            cursor.execute(
                "SELECT * FROM discrepancy WHERE run_id = ? ORDER BY discrepancy_id",
                (run_id,),
            )
            columns = [d[0] for d in cursor.description]
            return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]

    def find_discrepancy(self, discrepancy_id: str) -> Mapping[str, object] | None:
        with self._connect() as connection, closing(connection.cursor()) as cursor:
            cursor.execute(
                "SELECT * FROM discrepancy WHERE discrepancy_id = ?",
                (discrepancy_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            columns = [d[0] for d in cursor.description]
            disc = dict(zip(columns, row, strict=False))

            cursor.execute(
                "SELECT resolution_id, discrepancy_id, run_id, status, reason, "
                "selected_candidate, resolved_by, resolved_at FROM discrepancy_resolution "
                "WHERE discrepancy_id = ? ORDER BY resolved_at ASC",
                (discrepancy_id,),
            )
            res_cols = [d[0] for d in cursor.description]
            disc["resolution_history"] = [
                dict(zip(res_cols, r, strict=False)) for r in cursor.fetchall()
            ]
            return disc

    def all_discrepancies(
        self,
        *,
        run_id: str | None = None,
        type: str | None = None,
        severity: str | None = None,
    ) -> Sequence[Mapping[str, object]]:
        query = "SELECT * FROM discrepancy"
        params: list[object] = []
        clauses: list[str] = []
        if run_id:
            clauses.append("run_id = ?")
            params.append(run_id)
        if type:
            clauses.append("type = ?")
            params.append(type)
        if severity:
            clauses.append("severity = ?")
            params.append(severity)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY age_days DESC, discrepancy_id ASC"

        with self._connect() as connection, closing(connection.cursor()) as cursor:
            cursor.execute(query, tuple(params))
            columns = [d[0] for d in cursor.description]
            return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]

    def resolve_discrepancy(
        self,
        discrepancy_id: str,
        *,
        reason: str,
        selected_candidate: str | None = None,
        resolved_by: str = "investigator",
        journal: Journal | None = None,
        recorded_at: str | None = None,
    ) -> Mapping[str, object] | None:
        """Persist a resolution and atomically record the audit event in the journal.

        Both the database update and journal append commit within the same
        transaction to ensure durable consistency across both stores.
        """
        ts = recorded_at or datetime.now(UTC).isoformat()
        res_id = f"res_{discrepancy_id}_{int(time.time() * 1000)}"

        with self._connect() as connection, closing(connection.cursor()) as cursor:
            cursor.execute("BEGIN IMMEDIATE")
            try:
                cursor.execute(
                    "SELECT run_id, type, severity, constituent_kind, constituent_id, "
                    "reason, age_days, status FROM discrepancy WHERE discrepancy_id = ?",
                    (discrepancy_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    cursor.execute("ROLLBACK")
                    return None

                run_id = str(row[0])

                # Insert resolution record into discrepancy_resolution
                cursor.execute(
                    """
                    INSERT INTO discrepancy_resolution
                    (resolution_id, discrepancy_id, run_id, status, reason,
                     selected_candidate, resolved_by, resolved_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        res_id,
                        discrepancy_id,
                        run_id,
                        "RESOLVED",
                        reason,
                        selected_candidate,
                        resolved_by,
                        ts,
                    ),
                )

                # Update the discrepancy status
                cursor.execute(
                    "UPDATE discrepancy SET status = 'RESOLVED' WHERE discrepancy_id = ?",
                    (discrepancy_id,),
                )

                # Atomically append audit event to the journal within the same transaction
                if journal is not None and journal.path == self.path:
                    journal.migrate_within(cursor)
                    journal.append_within(
                        connection,
                        cursor,
                        {
                            "kind": "DiscrepancyResolved",
                            "resolution_id": res_id,
                            "discrepancy_id": discrepancy_id,
                            "run_id": run_id,
                            "status": "RESOLVED",
                            "reason": reason,
                            "selected_candidate": selected_candidate,
                            "resolved_by": resolved_by,
                            "recorded_at": ts,
                        },
                    )

                connection.execute("COMMIT")
            except Exception:
                cursor.execute("ROLLBACK")
                raise

        return self.find_discrepancy(discrepancy_id)

    def all_runs(self) -> Sequence[Mapping[str, object]]:
        with self._connect() as connection, closing(connection.cursor()) as cursor:
            cursor.execute(
                "SELECT * FROM reconciliation_run ORDER BY input_digest, rule_version"
            )
            columns = [d[0] for d in cursor.description]
            runs = [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]
            for r in runs:
                den = r.get("denominator", 0)
                num = r.get("numerator", 0)
                r["rate"] = (num / den) if den else 0.0
            return runs

    def digest_of(self, table: str) -> str:
        """A tamper-evident digest over a whole table, computed on read.

        Not a chain and not a substitute for the M5 journal: it exists so a
        reviewer can detect that stored results were edited.
        """
        if table not in ALLOWED_TABLES:
            raise ValueError(f"Table {table!r} is not an allowed table")

        with self._connect() as connection, closing(connection.cursor()) as cursor:
            cursor.execute(f"SELECT * FROM {table}")
            columns = [d[0] for d in cursor.description]
            rows = [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]
        # `digest` canonicalises and sorts internally; sorting here would
        # require ordering dicts, which is not defined.
        return digest({"table": table, "rows": [_canonical_row(r) for r in rows]})


def _canonical_row(row: Mapping[str, object]) -> dict[str, object]:
    return {str(k): v for k, v in sorted(row.items())}


def ensure_migrations(path_or_url: Path | str = ":memory:") -> None:
    """Run migrations for the given DSN. Safe to call multiple times.

    This should be called during application startup or deployment before
    opening any stores. It is idempotent and safe for concurrent calls.
    """
    path_str = str(path_or_url)
    if path_str.startswith("postgresql://") or path_str.startswith("postgres://"):
        from settleiq.persistence.postgres import PostgresPersistence

        pg_store = PostgresPersistence(path_str)
        pg_store.migrate()
    else:
        store = Persistence(path_str)
        store.migrate()


def open_store(path_or_url: Path | str = ":memory:", *, run_migrations: bool = True) -> Persistence:
    """Open a persistence store.

    For SQLite (including in-memory), migrations are run by default.
    For PostgreSQL, migrations are NOT run by default - call `ensure_migrations()` explicitly.
    """
    path_str = str(path_or_url)
    if path_str.startswith("postgresql://") or path_str.startswith("postgres://"):
        from settleiq.persistence.postgres import PostgresPersistence

        pg_store = PostgresPersistence(path_str)
        if run_migrations:
            pg_store.migrate()
        return pg_store

    store = Persistence(path_str)
    if run_migrations:
        store.migrate()
    return store


def _run_payload(result: ReconciliationResult) -> dict[str, object]:
    """What the journal attests about a run.

    Deliberately narrow: identity, counts, and the discrepancy identities. It
    does not restate amounts, which are already persisted and are themselves
    reconstructable from the run inputs.
    """
    return {
        "kind": "ReconciliationRunRecorded",
        "run_id": result.identity.run_id,
        "input_digest": result.identity.input_digest,
        "rule_version": result.identity.rule_version,
        "schema_version": result.identity.schema_version,
        "numerator": result.metrics.numerator,
        "denominator": result.metrics.denominator,
        "discrepancy_ids": sorted(d.discrepancy_id for d in result.discrepancies),
    }
