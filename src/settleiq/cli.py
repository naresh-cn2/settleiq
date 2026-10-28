"""The single-command reproduction entry point.

`python -m settleiq.cli run` provisions a store and journal, loads the
demonstration dataset, runs the engine, prints the discrepancies, the metrics
with their methodology, and the journal's state including its honest limitations,
then exits non-zero if anything asserted fails.

This is the demonstration contract (SETTLEIQ-MASTER-SPEC-001 section 4). A third
party with a clean clone runs it and sees the same output.
"""

from __future__ import annotations

import argparse
import json
import sys

from settleiq.engine import RunParameters, reconcile
from settleiq.engine.metrics import compute
from settleiq.fixtures.generator import generate
from settleiq.journal import open_journal
from settleiq.persistence.store import open_store
from settleiq.validation import validate_records

__all__ = ["build_parser", "main", "run_demonstration"]

WINDOW_START = "2026-10-01"
WINDOW_END = "2026-10-31"
RECORDED_AT = "2026-10-28T00:00:00Z"


def run_demonstration(*, database: str = ":memory:") -> dict[str, object]:
    """Load, validate, reconcile, persist, journal, and report — end to end."""
    dataset = generate()
    validated = validate_records(dataset.records)
    if validated.quarantined_count:
        raise AssertionError(
            f"demonstration dataset failed validation: {validated.quarantined}"
        )

    result = reconcile(validated.accepted, RunParameters(WINDOW_START, WINDOW_END))

    store = open_store(database)
    journal = open_journal(database)
    # An in-memory database is created fresh per connection. Without this, the
    # journal and the store would each hold a separate ":memory:" and the
    # journal would report a chain that lives somewhere else.
    shared = store.connection()
    if shared is not None:
        journal.adopt(shared)
    run_id = store.record_run(result, journal=journal, recorded_at=RECORDED_AT)

    metrics = compute(result.counts)
    expected = {d.expected_discrepancy for d in dataset.defects}
    produced = {d.type.value for d in result.discrepancies}

    report: dict[str, object] = {
        "run_id": run_id,
        "input_digest": result.identity.input_digest,
        "rule_version": result.identity.rule_version,
        "schema_version": result.identity.schema_version,
        "dataset_digest": dataset.input_digest,
        "generator_version": dataset.manifest["generator_version"],
        "provenance": dataset.manifest["provenance"],
        "metrics": metrics.to_canonical(),
        "discrepancies": [d.to_canonical() for d in result.discrepancies],
        "decompositions": [d.to_canonical() for d in result.decompositions],
        "injected_defects": [
            {
                "defect_id": d.defect_id,
                "expected": d.expected_discrepancy,
                "produced": d.expected_discrepancy in produced,
            }
            for d in dataset.defects
        ],
        "journal": _journal_section(journal),
    }
    unmet = sorted(expected - produced)
    report["all_injected_defects_reproduced"] = not unmet
    report["unreproduced"] = unmet
    return report


def _journal_section(journal) -> dict[str, object]:
    """Report the journal's state, including what it cannot prove."""
    report = journal.verify()
    sequence, head = journal.head()
    return {
        "intact": report.intact,
        "entries": report.entries_verified,
        "head_sequence": sequence,
        "head_digest": head,
        "findings": [list(f) for f in report.findings],
        "detects": [
            "payload modification",
            "digest modification",
            "deletion from the middle",
            "reordering",
            "duplication",
        ],
        "does_not_detect": [
            "tail truncation without an externally anchored head",
            "a wholesale rewrite from genesis",
        ],
    }


def _print_report(report: dict[str, object], stream) -> None:
    metrics = report["metrics"]
    assert isinstance(metrics, dict)
    write = stream.write

    write("SETTLEIQ - reconciliation demonstration\n")
    write("=" * 60 + "\n")
    write(f"run id            : {report['run_id'][:32]}...\n")
    write(f"input digest      : {report['input_digest']}\n")
    write(f"rule version      : {report['rule_version']}\n")
    write(f"provenance        : {report['provenance']}\n\n")

    write("METRICS (computed, with the methodology that produced them)\n")
    write("-" * 60 + "\n")
    write(f"  numerator       : {metrics['numerator']}\n")
    write(f"  denominator     : {metrics['denominator']}\n")
    write(f"  auto-match rate : {report['rate_text']}\n")
    write(f"  ambiguous       : {metrics['ambiguous']}\n")
    write(f"  rule conflicts  : {metrics['conflict']}\n")
    write(f"  insufficient    : {metrics['insufficient']}\n")
    write(f"  methodology     : v{metrics['methodology_version']}\n")
    write(f"  denominator def : {metrics['denominator_definition']}\n\n")

    write("DISCREPANCIES\n")
    write("-" * 60 + "\n")
    discrepancies = report["discrepancies"]
    assert isinstance(discrepancies, list)
    for item in discrepancies:
        assert isinstance(item, dict)
        flag = "unresolved" if item["status"] == "OPEN" else item["status"]
        write(
            f"  [{item['severity']:<6}] {item['type']:<18} "
            f"{item['constituent_kind']}:{item['constituent_id']} ({flag})\n"
        )
        write(f"           {item['reason']}\n")

    write("\nINJECTED DEFECTS - each expected before the run\n")
    write("-" * 60 + "\n")
    defects = report["injected_defects"]
    assert isinstance(defects, list)
    for defect in defects:
        assert isinstance(defect, dict)
        outcome = "reproduced" if defect["produced"] else "NOT REPRODUCED"
        write(f"  {defect['defect_id']}: {defect['expected']:<20} {outcome}\n")

    journal = report.get("journal")
    if isinstance(journal, dict):
        write("\nAUDIT JOURNAL (what it proves, and what it does not)\n")
        write("-" * 60 + "\n")
        write(f"  chain intact    : {journal['intact']}\n")
        write(f"  entries         : {journal['entries']}\n")
        write(f"  head digest     : {str(journal['head_digest'])[:32]}...\n")
        write(f"  detects         : {', '.join(journal['detects'])}\n")
        write(f"  does NOT detect : {', '.join(journal['does_not_detect'])}\n")

    write("\n")
    if report["all_injected_defects_reproduced"]:
        write("RESULT: every injected defect classified as recorded.\n")
    else:
        write(f"RESULT: FAILED - unreproduced: {report['unreproduced']}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="settleiq",
        description="Payment settlement reconciliation and discrepancy investigation",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run the reconciliation demonstration")
    run.add_argument("--json", action="store_true", help="emit the report as JSON")
    run.add_argument(
        "--database",
        default=":memory:",
        help="SQLite path for persisted runs and the journal (default: in-memory)",
    )

    sub.add_parser("gate", help="run the money-safety static gate")

    verify = sub.add_parser("verify", help="load a persisted store and verify its journal")
    verify.add_argument(
        "--database",
        default="settleiq.sqlite3",
        help="SQLite path holding the runs and the journal",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "gate":
        from settleiq.gates.float_gate import main as gate_main

        return gate_main()

    if args.command == "verify":
        store = open_store(args.database)
        journal = open_journal(args.database)
        report = journal.verify()
        print(json.dumps(report.to_canonical(), indent=2))
        if not report.intact:
            print("journal verification FAILED")
            return 1
        head_prefix = journal.head()[1][:24]
        print(f"journal verified: {report.entries_verified} entries, head {head_prefix}...")
        _ = store
        return 0

    report = run_demonstration(database=args.database)

    metrics = report["metrics"]
    assert isinstance(metrics, dict)
    numerator = metrics["numerator"]
    denominator = metrics["denominator"]
    rate = metrics["rate"]
    assert isinstance(rate, (int, float))
    report["rate_text"] = f"{numerator}/{denominator} = {rate:.4f}"

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        _print_report(report, sys.stdout)

    return 0 if report["all_injected_defects_reproduced"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
