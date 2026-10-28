"""Persistence tests (Gate 3 of the specification)."""

from __future__ import annotations

import pytest

from settleiq.engine import RunParameters, reconcile
from settleiq.fixtures.generator import generate
from settleiq.persistence.store import SCHEMA_STATEMENTS, Persistence, open_store
from settleiq.validation import validate_records

WINDOW = RunParameters("2026-10-01", "2026-10-31")


def _run():
    dataset = generate()
    validated = validate_records(dataset.records)
    return reconcile(validated.accepted, WINDOW)


def test_migration_is_idempotent(tmp_path) -> None:
    store = Persistence(tmp_path / "db.sqlite3")
    store.migrate()
    store.migrate()
    assert store.find_run("anything") is None


def test_run_and_discrepancies_persist(tmp_path) -> None:
    store = open_store(tmp_path / "db.sqlite3")
    result = _run()
    run_id = store.record_run(result)

    stored = store.find_run(run_id)
    assert stored is not None
    assert stored["run_id"] == run_id
    assert stored["numerator"] == result.metrics.numerator
    assert stored["denominator"] == result.metrics.denominator

    rows = store.discrepancies_for(run_id)
    assert len(rows) == len(result.discrepancies)


def test_results_survive_a_new_connection(tmp_path) -> None:
    path = tmp_path / "db.sqlite3"
    store = open_store(path)
    result = _run()
    run_id = store.record_run(result)
    store.close()

    reopened = open_store(path)
    assert reopened.find_run(run_id) is not None
    assert len(reopened.discrepancies_for(run_id)) == len(result.discrepancies)


def test_re_recording_an_identical_run_does_not_duplicate(tmp_path) -> None:
    store = open_store(tmp_path / "db.sqlite3")
    result = _run()
    store.record_run(result)
    store.record_run(result)
    assert len(store.all_runs()) == 1


def test_in_memory_store_keeps_its_schema() -> None:
    store = open_store(":memory:")
    result = _run()
    store.record_run(result)
    assert store.find_run(result.identity.run_id) is not None


def test_table_digest_detects_an_edited_stored_result(tmp_path) -> None:
    store = open_store(tmp_path / "db.sqlite3")
    result = _run()
    store.record_run(result)
    before = store.digest_of("discrepancy")

    with store._connect() as connection, pytest.MonkeyPatch.context():
        connection.execute("UPDATE discrepancy SET reason = 'edited'")
    after = store.digest_of("discrepancy")
    assert before != after


def test_schema_is_forward_only() -> None:
    joined = "\n".join(SCHEMA_STATEMENTS)
    for forbidden in ("DROP TABLE", "DROP COLUMN", "TRUNCATE"):
        assert forbidden not in joined.upper()


def test_a_distinct_rule_version_is_a_distinct_run(tmp_path) -> None:
    from settleiq.engine.rules import RuleRegistry
    from settleiq.fixtures.generator import generate as gen
    from settleiq.validation import validate_records as validate

    store = open_store(tmp_path / "db.sqlite3")
    dataset = gen()
    validated = validate(dataset.records)

    first = reconcile(validated.accepted, RunParameters("2026-10-01", "2026-10-31"))
    second = reconcile(
        validated.accepted,
        RunParameters(
            "2026-10-01",
            "2026-10-31",
            registry=RuleRegistry(version="1.0.1", rules=()),
        ),
    )
    store.record_run(first)
    store.record_run(second)
    assert len(store.all_runs()) == 2
