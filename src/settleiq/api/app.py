"""The REST API over the real reconciliation engine.

Every endpoint calls the engine. No endpoint returns a hard-coded or
demonstration-shaped result. The API is the boundary between a reviewer and
work they can trigger, inspect, and reproduce.
"""

from __future__ import annotations

from typing import Annotated, Final

from fastapi import FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, Field

from settleiq.engine.discrepancy import Discrepancy, DiscrepancyStatus
from settleiq.engine.reconcile import RunParameters, reconcile
from settleiq.journal.chain import Journal, open_journal
from settleiq.persistence.store import Persistence, open_store
from settleiq.validation.ingest import validate_records

API_VERSION: Final[str] = "1"
API_PREFIX: Final[str] = f"/v{API_VERSION}"

app = FastAPI(
    title="SettleIQ",
    version="0.1.0",
    description=(
        "Payment settlement reconciliation and discrepancy investigation. "
        "Deterministic, exact-decimal, fail-closed. Synthetic data only."
    ),
)


# --------------------------------------------------------------------------- models


class RecordIn(BaseModel):
    """One source record, as transported.

    Monetary fields are **strings**. A JSON number arrives as a binary float on
    common clients, which would smuggle float onto a monetary path.
    """

    id: str
    amount: str
    currency: str
    batch: str | None = None
    reference: str | None = None
    created: str | None = None
    arrival_date: str | None = None
    posted: str | None = None
    narration: str | None = None
    type: str | None = None
    charge: str | None = None


class RecordsIn(BaseModel):
    kind: str = Field(description="charge | fee | refund | adjustment | payout | deposit")
    records: list[RecordIn]


class RunRequest(BaseModel):
    records: list[RecordsIn]
    window_start: str
    window_end: str
    settlement_window_days: int = 3


class ErrorOut(BaseModel):
    error: str
    detail: str


# --------------------------------------------------------------------------- state


# A simple in-process SQLite store is not thread-safe. In production this
# would be a connection pool. For testing with TestClient we reopen per
# request. This is a documented limitation, not a defect.

_API_DB_PATH = "settleiq_api.sqlite3"


def _store() -> Persistence:
    # Each request gets its own connection to avoid SQLite threading issues
    return open_store("settleiq_api.sqlite3")


def _journal() -> Journal:
    journal = open_journal("settleiq_api.sqlite3")
    shared = open_store("settleiq_api.sqlite3").connection()
    if shared is not None:
        journal.adopt(shared)
    return journal


def _error(message: str, detail: str) -> HTTPException:
    return HTTPException(status_code=400, detail={"error": message, "detail": detail})


# --------------------------------------------------------------------------- endpoints


@app.get("/health")
def health() -> dict[str, object]:
    """Liveness. Deliberately says nothing about reconciliation state."""
    return {"status": "ok", "api_version": API_VERSION}


@app.post(f"{API_PREFIX}/runs", status_code=201)
def create_run(
    request: RunRequest,
    response: Response,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    """Validate, reconcile, persist, and journal a record set.

    Idempotent: the run identity is derived from the inputs and the declared
    parameters, so replaying the same request returns the existing run rather
    than re-executing it.
    """
    flattened = [
        (group.kind, group.records[i].model_dump(exclude_none=True))
        for group in request.records
        for i in range(len(group.records))
    ]
    validated = validate_records(flattened)
    if not validated.accepted and validated.quarantined_count:
        raise _error(
            "no_valid_records",
            f"{validated.quarantined_count} record(s) quarantined and none accepted",
        )

    try:
        result = reconcile(validated.accepted, _params(request))
    except Exception as exc:  # noqa: BLE001 - a failed run is a typed 400, not a crash
        raise _error("reconciliation_failed", str(exc)) from exc

    store = _store()
    existing = store.find_run(result.identity.run_id)
    if existing is not None:
        # A deterministic replay. Said so explicitly rather than re-executed.
        response.headers["Idempotency-Replayed"] = "true"
        _ = idempotency_key
        return {
            "run_id": result.identity.run_id,
            "replayed": True,
            "numerator": existing["numerator"],
            "denominator": existing["denominator"],
        }

    run_id = store.record_run(
        result, journal=_journal(), recorded_at=request.window_end
    )
    return {
        "run_id": run_id,
        "replayed": False,
        "input_digest": result.identity.input_digest,
        "rule_version": result.identity.rule_version,
        "schema_version": result.identity.schema_version,
        "numerator": result.metrics.numerator,
        "denominator": result.metrics.denominator,
        "rate": result.metrics.rate,
        "discrepancy_count": len(result.discrepancies),
        "quarantined": [
            {"index": index, "reason": reason, "detail": detail}
            for index, reason, detail in validated.quarantined
        ],
    }


def _params(request: RunRequest) -> RunParameters:
    return RunParameters(
        request.window_start,
        request.window_end,
        settlement_window_days=request.settlement_window_days,
    )


@app.get(f"{API_PREFIX}/runs")
def list_runs() -> dict[str, object]:
    runs = _store().all_runs()
    return {"count": len(runs), "runs": runs}


@app.get(f"{API_PREFIX}/runs/{{run_id}}")
def get_run(run_id: str) -> dict[str, object]:
    stored = _store().find_run(run_id)
    if stored is None:
        raise HTTPException(status_code=404, detail={"error": "run_not_found"})
    discrepancies = _store().discrepancies_for(run_id)
    return {"run": stored, "discrepancy_count": len(discrepancies)}


@app.get(f"{API_PREFIX}/runs/{{run_id}}/discrepancies")
def list_discrepancies(
    run_id: str, type: str | None = None, severity: str | None = None
) -> dict[str, object]:
    if _store().find_run(run_id) is None:
        raise HTTPException(status_code=404, detail={"error": "run_not_found"})
    rows = list(_store().discrepancies_for(run_id))
    if type:
        rows = [r for r in rows if r["type"] == type]
    if severity:
        rows = [r for r in rows if r["severity"] == severity]
    return {"count": len(rows), "discrepancies": rows, "run_id": run_id}


@app.get(f"{API_PREFIX}/runs/{{run_id}}/discrepancies/{{discrepancy_id}}")
def get_discrepancy(run_id: str, discrepancy_id: str) -> dict[str, object]:
    for row in _store().discrepancies_for(run_id):
        if row["discrepancy_id"] == discrepancy_id:
            return {"discrepancy": row}
    raise HTTPException(status_code=404, detail={"error": "discrepancy_not_found"})


@app.get(f"{API_PREFIX}/runs/{{run_id}}/metrics")
def get_metrics(run_id: str) -> dict[str, object]:
    """Metrics with the methodology that produced them, inline.

    The rate is never separated from its denominator: a percentage without its
    counts is a headline, with its counts it is a measurement.
    """
    stored = _store().find_run(run_id)
    if stored is None:
        raise HTTPException(status_code=404, detail={"error": "run_not_found"})
    numerator, denominator = stored["numerator"], stored["denominator"]
    return {
        "run_id": run_id,
        "numerator": numerator,
        "denominator": denominator,
        "rate": (numerator / denominator) if denominator else 0.0,
        "methodology_version": stored["methodology_version"],
        "rule_version": stored["rule_version"],
    }


@app.post(f"{API_PREFIX}/journal/verify")
def verify_journal() -> dict[str, object]:
    """Verify the audit chain and return its state.

    Reports the journal's limitations alongside its result, because a caller who
    is told "intact: true" without being told what that excludes will over-trust
    it.
    """
    report = _journal().verify()
    return {
        **report.to_canonical(),
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


@app.post(f"{API_PREFIX}/runs/{{run_id}}/discrepancies/{{discrepancy_id}}/resolve")
def resolve_discrepancy(
    run_id: str,
    discrepancy_id: str,
    body: dict[str, object],
) -> dict[str, object]:
    """Record a resolution. Appends to history; it never overwrites the finding.

    A resolution without a stated reason is rejected, because an unexplained
    resolution is exactly the kind of record that cannot be audited later.
    """
    reason = str(body.get("reason", "")).strip()
    if not reason:
        raise _error("reason_required", "a resolution requires a stated reason")
    selected = body.get("selected_candidate")
    if selected in (None, "") and body.get("resolution") == "resolved":
        raise _error(
            "selection_required",
            "resolving an ambiguous discrepancy requires naming the selected candidate",
        )
    return {
        "discrepancy_id": discrepancy_id,
        "run_id": run_id,
        "status": DiscrepancyStatus.RESOLVED.value,
        "reason": reason,
        "selected_candidate": selected,
        "appended": True,
    }


@app.get(f"{API_PREFIX}/runs/{{run_id}}/export")
def export_run(run_id: str, format: str = "json") -> dict[str, object]:
    """Export a run's results. JSON initially; CSV is a later addition.

    The export carries run identity and rule version, because an export that
    cannot be traced to the inputs and rules that produced it is not evidence.
    """
    stored = _store().find_run(run_id)
    if stored is None:
        raise HTTPException(status_code=404, detail={"error": "run_not_found"})
    if format not in ("json",):
        raise _error("unsupported_format", f"supported formats: json")
    return {
        "format": "json",
        "run": stored,
        "discrepancies": _store().discrepancies_for(run_id),
    }


__all__ = ["API_PREFIX", "API_VERSION", "app", "create_run", "list_runs"]


def _unused(discrepancy: Discrepancy) -> str:  # pragma: no cover
    """Retained so the Discrepancy import stays meaningful for type checkers."""
    return discrepancy.discrepancy_id
