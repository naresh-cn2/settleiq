"""Journal integrity tests — the tamper suite.

These are the tests that substantiate SettleIQ's integrity claim. A repository
that stores hashes but has not run this suite has not demonstrated integrity; it
has demonstrated that it can call a hash function, which is not a security
property (SETTLEIQ-08 §5.4, T-01…T-07).
"""

from __future__ import annotations

import json

import pytest

from settleiq.engine import RunParameters, reconcile
from settleiq.fixtures.generator import generate
from settleiq.journal import GENESIS_DIGEST, Journal, TamperType, open_journal
from settleiq.persistence.store import open_store
from settleiq.validation import validate_records

WINDOW = RunParameters("2026-10-01", "2026-10-31")

TAMPER = TamperType


def _result():
    dataset = generate()
    validated = validate_records(dataset.records)
    return reconcile(validated.accepted, WINDOW)


@pytest.fixture
def journal(tmp_path) -> Journal:
    j = open_journal(tmp_path / "journal.sqlite3")
    for index in range(5):
        j.append({"kind": "note", "index": index}, recorded_at="2026-10-28T00:00:00Z")
    return j


def test_append_returns_the_computed_digest(journal: Journal) -> None:
    entry = journal.append({"kind": "probe"}, recorded_at="2026-10-28T00:00:00Z")
    assert len(entry.entry_digest) == 64
    assert entry.prev_digest != GENESIS_DIGEST


def test_a_fresh_journal_verifies_intact(tmp_path) -> None:
    journal = open_journal(tmp_path / "fresh.sqlite3")
    report = journal.verify()
    assert report.intact
    assert report.entries_verified == 0
    assert report.head_digest == GENESIS_DIGEST


def test_an_unmodified_journal_verifies_intact(journal: Journal) -> None:
    assert journal.verify().intact


def test_digest_is_reproducible_from_payload(tmp_path) -> None:
    """A digest must be recomputable by a third party, not just by the writer."""
    journal = open_journal(tmp_path / "repro.sqlite3")
    entry = journal.append({"a": 1, "b": "x"}, recorded_at="2026-10-28T00:00:00Z")
    from settleiq.canonical.serialization import digest as d

    payload_str = json.dumps({"a": 1, "b": "x"}, sort_keys=True, separators=(",", ":"))
    expected = d({"prev": GENESIS_DIGEST, "payload": payload_str})
    assert entry.entry_digest == expected


# ---------------------------------------------------------------- T-01 modify payload
def test_modifying_a_payload_is_detected(journal: Journal, tmp_path) -> None:
    _mutate(journal, "UPDATE journal_entry SET payload = ? WHERE sequence = 2",
            (json.dumps({"kind": "tampered"}, sort_keys=True, separators=(",", ":")),))
    report = journal.verify()
    assert not report.intact
    assert any(kind == TAMPER.PAYLOAD_MODIFIED for _, kind, _ in report.findings)


# ---------------------------------------------------------------- T-02 modify digest
def test_modifying_a_digest_is_detected(journal: Journal) -> None:
    _mutate(journal, "UPDATE journal_entry SET entry_digest = ? WHERE sequence = 2",
            ("f" * 64,))
    assert not journal.verify().intact


# ---------------------------------------------------------------- T-03 delete an entry
def test_deleting_an_entry_is_detected(journal: Journal) -> None:
    _mutate(journal, "DELETE FROM journal_entry WHERE sequence = 3")
    report = journal.verify()
    assert not report.intact
    assert any(kind in (TAMPER.ENTRY_DELETED, TAMPER.CHAIN_BREAK) for _, kind, _ in report.findings)


# ---------------------------------------------------------------- T-04 hand-written digest
def test_a_hand_written_digest_is_detected(tmp_path) -> None:
    """The fabrication case: a digest present but never computed from its entry."""
    journal = open_journal(tmp_path / "fabricated.sqlite3")
    _mutate(
        journal,
        "INSERT INTO journal_entry (sequence, prev_digest, entry_digest, payload, recorded_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (1, GENESIS_DIGEST, "deadbeef" * 8, json.dumps({}), "2026-10-28T00:00:00Z"),
    )
    report = journal.verify()
    assert not report.intact
    assert any(
        kind in (TAMPER.HANDSHAKE_DIGEST, TAMPER.PAYLOAD_MODIFIED)
        for _, kind, _ in report.findings
    )


# ---------------------------------------------------------------- T-05 reorder
def test_reordering_entries_is_detected(journal: Journal) -> None:
    _mutate(journal, "UPDATE journal_entry SET sequence = 99 WHERE sequence = 2")
    report = journal.verify()
    assert not report.intact
    assert any(
        kind in (TAMPER.ENTRY_REORDERED, TAMPER.CHAIN_BREAK)
        for _, kind, _ in report.findings
    )


# ---------------------------------------------------------------- T-06 duplicate
def test_duplicating_an_entry_is_detected(journal: Journal) -> None:
    _mutate(
        journal,
        "INSERT INTO journal_entry (sequence, prev_digest, entry_digest, payload, recorded_at) "
        "SELECT sequence + 10, prev_digest, entry_digest, payload, recorded_at "
        "FROM journal_entry WHERE sequence = 2",
    )
    assert not journal.verify().intact


# ---------------------------------------------------------------- T-07 truncate
def test_truncating_the_tail_is_NOT_detected_by_the_chain_alone(journal: Journal) -> None:
    """A real limitation, asserted rather than glossed over (T-07).

    Deleting the tail of a chain leaves every remaining link internally
    consistent, so the chain verifies. This is the well-known boundary of a
    self-contained hash chain: it detects modification, deletion from the
    middle, reordering, and duplication, but **not** tail truncation.

    The standard remedy is to anchor the head digest externally, on a schedule,
    and compare on verification. That is deliberately not implemented here, and
    this test documents the gap rather than asserting a guarantee the code does
    not provide.

    A deployment that needs truncation resistance must anchor `journal.head()`
    out-of-band. Until it does, the correct claim is: *modification of recorded
    entries is detectable; truncation is not.*
    """
    _mutate(journal, "DELETE FROM journal_entry WHERE sequence > 2")

    report = journal.verify()
    assert report.intact, "the truncated chain is internally consistent"
    assert report.entries_verified == 2

    # What DOES catch it: an independently anchored expectation of the head.
    anchored_before = journal.head()
    assert anchored_before[0] == 2
    _mutate(journal, "DELETE FROM journal_entry WHERE sequence > 1")
    anchored_after = journal.head()
    assert anchored_after[0] == 1
    assert anchored_before != anchored_after, (
        "an externally anchored head detects truncation even though the chain "
        "does not"
    )
    _mutate(journal, "DELETE FROM journal_entry WHERE sequence > 4")


def test_a_detached_middle_deletion_IS_detected(journal: Journal) -> None:
    """The complement: deleting from the middle breaks the link, and is caught."""
    _mutate(journal, "DELETE FROM journal_entry WHERE sequence = 3")
    assert not journal.verify().intact


def test_an_intact_journal_verifies_after_many_appends(tmp_path) -> None:
    journal = open_journal(tmp_path / "many.sqlite3")
    for index in range(50):
        journal.append({"index": index}, recorded_at="2026-10-28T00:00:00Z")
    report = journal.verify()
    assert report.intact
    assert report.entries_verified == 50


def test_a_wholesale_rewrite_is_invisible_to_the_chain_but_visible_to_the_digest(
    tmp_path,
) -> None:
    """The limitation, demonstrated rather than asserted.

    Rebuilding the whole chain from genesis makes `verify()` pass, because every
    link is internally consistent. What it cannot forge is agreement with a
    previously anchored table digest. This test exists to show the boundary of
    the guarantee, not to claim it is stronger than it is.
    """
    original = open_journal(tmp_path / "a.sqlite3")
    for index in range(3):
        original.append({"index": index}, recorded_at="2026-10-28T00:00:00Z")
    anchored = original.table_digest()

    forged = open_journal(tmp_path / "b.sqlite3")
    for index in range(3):
        forged.append({"index": index + 100}, recorded_at="2026-10-28T00:00:00Z")

    assert forged.verify().intact
    assert forged.table_digest() != anchored


def test_the_journal_and_the_run_commit_atomically(tmp_path) -> None:
    """A journal entry must never exist for a run that was not persisted."""
    store = open_store(tmp_path / "atomic.sqlite3")
    journal = open_journal(tmp_path / "atomic.sqlite3")
    result = _result()
    run_id = store.record_run(result, journal=journal, recorded_at="2026-10-28T00:00:00Z")

    stored = store.find_run(run_id)
    assert stored is not None
    report = journal.verify()
    assert report.intact
    assert report.entries_verified == 1

    entries = journal.entries()
    assert entries[0].payload["run_id"] == run_id
    assert entries[0].payload["denominator"] == result.metrics.denominator


def test_an_identical_run_is_journalled_once(tmp_path) -> None:
    store = open_store(tmp_path / "once.sqlite3")
    journal = open_journal(tmp_path / "once.sqlite3")
    result = _result()
    store.record_run(result, journal=journal, recorded_at="2026-10-28T00:00:00Z")
    store.record_run(result, journal=journal, recorded_at="2026-10-28T00:00:00Z")
    assert journal.verify().entries_verified == 1


def test_recorded_at_is_excluded_from_the_preimage(tmp_path) -> None:
    """OQ-12, demonstrated rather than asserted.

    A captured-date value is stored as entry content but must never enter the
    digest preimage, or verification could not reproduce a digest and the chain
    would verify as broken immediately. This proves it both ways: the stored
    digest matches a preimage *without* the clock, and would not match one
    *with* it.
    """
    from settleiq.canonical.serialization import digest

    journal = open_journal(tmp_path / "clock.sqlite3")
    first = journal.append({"k": "v"}, recorded_at="2026-10-28T00:00:00Z")

    payload_kv = json.dumps({"k": "v"}, sort_keys=True, separators=(",", ":"))
    without_clock = digest({"prev": GENESIS_DIGEST, "payload": payload_kv})
    with_clock = digest(
        {
            "prev": GENESIS_DIGEST,
            "payload": json.dumps(
                {"k": "v", "recorded_at": "2026-10-28T00:00:00Z"},
                sort_keys=True,
                separators=(",", ":"),
            ),
        }
    )

    assert first.entry_digest == without_clock
    assert first.entry_digest != with_clock
    assert journal.verify().intact


def test_head_is_available_for_external_anchoring(journal: Journal) -> None:
    sequence, head = journal.head()
    assert sequence == 5
    assert len(head) == 64


def _mutate(journal: Journal, sql: str, params: tuple[object, ...] = ()) -> None:
    with journal._connect() as connection, closing(connection.cursor()) as cursor:
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute(sql, params)
        cursor.execute("COMMIT")


from contextlib import closing  # noqa: E402  (imported late to keep the fixture local)
