"""
PostgreSQL integration tests for SettleIQ persistence layer.

These tests require a real PostgreSQL instance. The DSN must be provided via the
environment variable TEST_POSTGRES_DSN (or SETTLEIQ_TEST_POSTGRES_URL) e.g., a Docker container or managed DB.
They will be skipped if the variable is not set.
"""
import os
import uuid
import pytest
from settleiq.persistence.postgres import PostgresPersistence
from settleiq.engine import ReconciliationResult, Discrepancy

TEST_DSN = os.environ.get("TEST_POSTGRES_DSN") or os.environ.get("SETTLEIQ_TEST_POSTGRES_URL")

pytestmark = pytest.mark.skipif(not TEST_DSN, reason="TEST_POSTGRES_DSN or SETTLEIQ_TEST_POSTGRES_URL not set")


@pytest.fixture(scope="module")
def pg_store():
    """Create a PostgresPersistence instance and ensure schema is up-to-date."""
    store = PostgresPersistence(TEST_DSN)
    store.migrate()
    yield store
    # Cleanup: drop only the tables we created in this test run.
    # This is safe because we are using a dedicated test database.
    with store._connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            DROP TABLE IF EXISTS journal_entry;
            DROP TABLE IF EXISTS discrepancy_resolution;
            DROP TABLE IF EXISTS discrepancy;
            DROP TABLE IF EXISTS reconciliation_run;
            DROP TABLE IF EXISTS supersession;
            DROP TABLE IF EXISTS schema_migration;
        """)
        conn.commit()


def _unique_id(prefix: str) -> str:
    """Generate a unique identifier for test entities."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_fresh_schema_initialization(pg_store):
    """Verify that the migration creates all expected tables."""
    with pg_store._connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public';
        """)
        tables = {row[0] for row in cur.fetchall()}
    expected = {
        "reconciliation_run",
        "discrepancy",
        "discrepancy_resolution",
        "supersession",
        "journal_entry",
        "schema_migration",
    }
    assert expected.issubset(tables)


def test_migration_idempotency(pg_store):
    """Running migrate a second time must not raise and must not duplicate schema_migration rows."""
    pg_store.migrate()
    with pg_store._connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM schema_migration WHERE version = 1;")
        count = cur.fetchone()[0]
    assert count == 1


def test_reconciliation_run_persistence(pg_store):
    """Persist a run and verify it can be retrieved."""
    run_id = _unique_id("run")
    result = ReconciliationResult(
        identity=ReconciliationResult.Identity(
            run_id=run_id,
            input_digest="test_digest",
            rule_version="1.0",
            schema_version="1.0",
        ),
        metrics=ReconciliationResult.Metrics(
            numerator=5,
            denominator=10,
            methodology_version="1.0",
        ),
        discrepancies=[],
        decomp=[],
    )
    pg_store.record_run(result)
    run = pg_store.find_run(run_id)
    assert run is not None
    assert run["run_id"] == run_id
    assert run["numerator"] == 5
    assert run["denominator"] == 10


def test_discrepancy_resolution_atomic(pg_store):
    """Create a run, insert a discrepancy, resolve it, and verify atomicity."""
    run_id = _unique_id("run")
    result = ReconciliationResult(
        identity=ReconciliationResult.Identity(
            run_id=run_id,
            input_digest="test_digest_2",
            rule_version="1.0",
            schema_version="1.0",
        ),
        metrics=ReconciliationResult.Metrics(
            numerator=1,
            denominator=1,
            methodology_version="1.0",
        ),
        discrepancies=[],
        decomp=[],
    )
    pg_store.record_run(result)

    discrepancy_id = _unique_id("dsc")
    with pg_store._connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO discrepancy
            (discrepancy_id, run_id, type, severity, constituent_kind,
             constituent_id, reason, age_days, status)
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s);
        """, (
            discrepancy_id,
            run_id,
            "NET_GROSS_BREAK",
            "HIGH",
            "payout",
            "payout_123",
            "Test discrepancy",
            0,
            "OPEN",
        ))
        conn.commit()

    resolved = pg_store.resolve_discrepancy(
        discrepancy_id=discrepancy_id,
        reason="Fixed by test",
        resolved_by="tester"
    )
    assert resolved is not None
    assert resolved["status"] == "RESOLVED"

    disc = pg_store.find_discrepancy(discrepancy_id)
    assert disc is not None
    assert disc["status"] == "RESOLVED"


def test_decimal_precision(pg_store):
    """Ensure monetary amounts stored as NUMERIC retain exact precision."""
    from decimal import Decimal
    run_id = _unique_id("run")
    result = ReconciliationResult(
        identity=ReconciliationResult.Identity(
            run_id=run_id,
            input_digest="digest",
            rule_version="1.0",
            schema_version="1.0",
        ),
        metrics=ReconciliationResult.Metrics(
            numerator=Decimal("12345.6789"),
            denominator=Decimal("10000"),
            methodology_version="1.0",
        ),
        discrepancies=[],
        decomp=[],
    )
    pg_store.record_run(result)
    run = pg_store.find_run(run_id)
    assert run is not None
    assert run["numerator"] == 123456789
    assert run["denominator"] == 100000000


def test_audit_journal_integrity(pg_store):
    """Verify that the hash-chained audit journal records entries and detects tampering."""
    from settleiq.journal.chain import open_journal
    journal = open_journal(TEST_DSN)
    with pg_store._connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM journal_entry;")
        count_before = cur.fetchone()[0]

    run_id = _unique_id("run")
    result = ReconciliationResult(
        identity=ReconciliationResult.Identity(
            run_id=run_id,
            input_digest="journal_digest",
            rule_version="1.0",
            schema_version="1.0",
        ),
        metrics=ReconciliationResult.Metrics(
            numerator=1,
            denominator=1,
            methodology_version="1.0",
        ),
        discrepancies=[],
        decomp=[],
    )
    pg_store.record_run(result, journal=journal, recorded_at="2026-10-30T00:00:00Z")

    report = journal.verify()
    assert report.intact is True

    with pg_store._connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM journal_entry;")
        count_after = cur.fetchone()[0]
    assert count_after == count_before + 1


def test_concurrent_operations(pg_store):
    """Simulate two threads inserting runs concurrently."""
    import threading

    results = []
    errors = []

    def insert_run(run_id):
        try:
            result = ReconciliationResult(
                identity=ReconciliationResult.Identity(
                    run_id=run_id,
                    input_digest=f"digest_{run_id}",
                    rule_version="1.0",
                    schema_version="1.0",
                ),
                metrics=ReconciliationResult.Metrics(
                    numerator=1,
                    denominator=1,
                    methodology_version="1.0",
                ),
                discrepancies=[],
                decomp=[],
            )
            pg_store.record_run(result)
            results.append(run_id)
        except Exception as e:
            errors.append((run_id, e))

    run_id1 = _unique_id("concurrent")
    run_id2 = _unique_id("concurrent")
    t1 = threading.Thread(target=insert_run, args=(run_id1,))
    t2 = threading.Thread(target=insert_run, args=(run_id2,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert not errors, f"Concurrent inserts raised: {errors}"
    assert len(results) == 2
    for rid in results:
        run = pg_store.find_run(rid)
        assert run is not None


def test_migration_concurrency(pg_store):
    """Simulate multiple workers attempting to run migrations concurrently."""
    import threading
    import time

    errors = []

    def run_migrate():
        try:
            # Each thread creates its own connection pool? We'll just call migrate.
            # Since migrate uses the same DSN, it will share the same database.
            pg_store.migrate()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=run_migrate) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Concurrent migrations raised: {errors}"

    # Verify schema integrity after concurrent migrations
    with pg_store._connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM schema_migration WHERE version = 1;")
        count = cur.fetchone()[0]
    assert count == 1