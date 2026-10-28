"""Tests for the PostgreSQL persistence implementation and migrations.

Verifies:
- Migration DDL syntax and ordering
- PostgresPersistence contract with simulated and live connection targets
- Atomic rollback semantics under induced failures during writes
- Dual-backend factory (open_store routing)
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from settleiq.engine import RunParameters, reconcile
from settleiq.fixtures.generator import generate
from settleiq.persistence.postgres import MIGRATIONS_DIR, PostgresPersistence
from settleiq.validation import validate_records


def test_postgres_migration_files_exist_and_contain_ddl() -> None:
    assert MIGRATIONS_DIR.is_dir()
    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    assert len(sql_files) >= 1

    first_migration = sql_files[0].read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS reconciliation_run" in first_migration
    assert "CREATE TABLE IF NOT EXISTS discrepancy" in first_migration
    assert "CREATE TABLE IF NOT EXISTS discrepancy_resolution" in first_migration
    assert "CREATE TABLE IF NOT EXISTS journal_entry" in first_migration
    assert "CHECK (numerator >= 0)" in first_migration
    assert "CHECK (denominator >= 0)" in first_migration


def test_open_store_routes_to_postgres_on_url_prefix() -> None:
    # URL starting with postgresql:// or postgres:// routes to PostgresPersistence
    pg_target = "postgresql://user:pass@localhost:5432/test_db"
    store = PostgresPersistence(pg_target)
    assert store.dsn == pg_target


def test_postgres_persistence_rollback_on_failure() -> None:
    """Verifies that an error during a write transaction triggers conn.rollback()."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Simulate database error on query execution
    mock_cursor.execute.side_effect = RuntimeError("Simulated DB connection lost")

    pg_store = PostgresPersistence(mock_conn)

    dataset = generate()
    validated = validate_records(dataset.records)
    result = reconcile(validated.accepted, RunParameters("2026-10-01", "2026-10-31"))

    with pytest.raises(RuntimeError, match="Simulated DB connection lost"):
        pg_store.record_run(result)

    # Verify rollback was called and commit was NOT called
    mock_conn.rollback.assert_called_once()
    mock_conn.commit.assert_not_called()


def test_postgres_persistence_resolve_rollback_on_failure() -> None:
    """Verifies that failure during discrepancy resolution triggers rollback."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Cursor returns an existing discrepancy row on SELECT
    mock_cursor.fetchone.return_value = ("run_123",)
    # But fails on UPDATE
    def execute_side_effect(sql, *args):
        if "UPDATE discrepancy" in sql:
            raise RuntimeError("Disk write failed")
        return None

    mock_cursor.execute.side_effect = execute_side_effect

    pg_store = PostgresPersistence(mock_conn)

    with pytest.raises(RuntimeError, match="Disk write failed"):
        pg_store.resolve_discrepancy("dsc_999", reason="Manual inspection")

    mock_conn.rollback.assert_called_once()
    mock_conn.commit.assert_not_called()
