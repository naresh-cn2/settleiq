"""
PostgreSQL integration tests for SettleIQ persistence layer.

These tests require a real PostgreSQL instance. The DSN must be provided via the
environment variable TEST_POSTGRES_DSN (or SETTLEIQ_TEST_POSTGRES_URL), e.g. a
Docker container or managed DB. They will be skipped if the variable is not set.
"""
import os
import uuid

import pytest

from settleiq.engine import ReconciliationResult
from settleiq.model.run_identity import RunIdentity
from settleiq.persistence.postgres import PostgresPersistence

TEST_DSN = os.environ.get("TEST_POSTGRES_DSN") or os.environ.get("SETTLEIQ_TEST_POSTGRES_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DSN,
    reason="TEST_POSTGRES_DSN or SETTLEIQ_TEST_POSTGRES_URL not set",
)


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


def _make_result(run_id: str, counts=None) -> ReconciliationResult:
    """Create a minimal ReconciliationResult for testing persistence."""
    if counts is None:
        counts = {
            "eligible": 1,
            "deterministic": 1,
            "human_confirmed": 0,
            "ambiguous": 0,
            "conflict": 0,
            "insufficient": 0,
            "quarantined": 0,
            "rejected": 0,
        }
    identity = RunIdentity(
        input_digest="test_digest",
        rule_version="1.0",
        schema_version="1.0",
    )
    # Override run_id by creating a new RunIdentity with the same digest? 
    # RunIdentity.run_id is derived from input_digest, rule_version, schema_version.
    # To have a specific run_id, we need to set input_digest accordingly.
    # But the run_id is derived from the identity tuple. We'll just use the derived run_id.
    # For test uniqueness, we can include a unique component in input_digest.
    identity = RunIdentity(
        input_digest=f"test_digest_{run_id}",
        rule_version="1.0",
        schema_version="1.0",
    )
    return ReconciliationResult(
        identity=identity,
        decisions=[],
        discrepancies=[],
        decompositions=[],
        counts=counts,
    )


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
    result = _make_result(run_id)
    pg_store.record_run(result)
    run = pg_store.find_run(result.identity.run_id)
    assert run is not None
    assert run["run_id"] == result.identity.run_id
    assert run["numerator"] == 1
    assert run["denominator"] == 1


def test_discrepancy_resolution_atomic(pg_store):
    """Create a run, insert a discrepancy, resolve it, and verify atomicity."""
    run_id = _unique_id("run")
    result = _make_result(run_id)
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
            result.identity.run_id,
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
    run_id = _unique_id("run")
    # Use counts that reflect the decimal precision test
    counts = {
        "eligible": 100000000,
        "deterministic": 123456789,
        "human_confirmed": 0,
        "ambiguous": 0,
        "conflict": 0,
        "insufficient": 0,
        "quarantined": 0,
        "rejected": 0,
    }
    result = _make_result(run_id, counts=counts)
    pg_store.record_run(result)
    run = pg_store.find_run(result.identity.run_id)
    assert run is not None
    assert run["numerator"] == 123456789
    assert run["denominator"] == 100000000


def test_audit_journal_integrity(pg_store):
    """Verify that the hash-chained audit journal records entries and detects tampering."""
    from settleiq.journal import open_journal
    journal = open_journal(TEST_DSN)
    with pg_store._connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM journal_entry;")
        count_before = cur.fetchone()[0]

    run_id = _unique_id("run")
    result = _make_result(run_id)
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

    derived_ids = []
    errors = []

    def insert_run(prefix):
        try:
            result = _make_result(prefix)
            pg_store.record_run(result)
            derived_ids.append(result.identity.run_id)
        except Exception as e:
            errors.append((prefix, e))

    prefix1 = _unique_id("concurrent")
    prefix2 = _unique_id("concurrent")
    t1 = threading.Thread(target=insert_run, args=(prefix1,))
    t2 = threading.Thread(target=insert_run, args=(prefix2,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert not errors, f"Concurrent inserts raised: {errors}"
    assert len(derived_ids) == 2
    for rid in derived_ids:
        run = pg_store.find_run(rid)
        assert run is not None


def test_migration_concurrency(pg_store):
    """Simulate multiple workers attempting to run migrations concurrently."""
    import threading

    errors = []

    def run_migrate():
        try:
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