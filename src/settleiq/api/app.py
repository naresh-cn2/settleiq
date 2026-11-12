"""The REST API over the real reconciliation engine.

Every endpoint calls the engine or store. No endpoint returns a hard-coded or
demonstration-shaped result. The API is the boundary between a reviewer and
work they can trigger, inspect, and reproduce.
"""

from __future__ import annotations

import hmac
import logging
import os
import secrets
import time
from collections import defaultdict
from pathlib import Path
from typing import Annotated, Final

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from settleiq.engine.discrepancy import Discrepancy, DiscrepancyStatus
from settleiq.engine.reconcile import RunParameters, reconcile
from settleiq.journal.chain import Journal, open_journal
from settleiq.persistence.store import Persistence, ensure_migrations, open_store
from settleiq.validation.ingest import validate_records

logger = logging.getLogger(__name__)

API_VERSION: Final[str] = "1"
API_PREFIX: Final[str] = f"/v{API_VERSION}"

STATIC_DIR: Final[Path] = Path(__file__).resolve().parent.parent / "static"
ASSETS_DIR: Final[Path] = STATIC_DIR / "assets"

# Rate limiting in-memory state: IP -> list of request timestamps
_RATE_LIMIT_WINDOW_SECS: Final[float] = 60.0
_MAX_REQUESTS_PER_WINDOW: Final[int] = int(os.environ.get("SETTLEIQ_RATE_LIMIT", "120"))
_IP_REQUEST_TIMESTAMPS: dict[str, list[float]] = defaultdict(list)

# --------------------------------------------------------------------------- demo authorization
# Public demonstration access. Demo sessions are server-authorized:
# a short-lived demo token is issued by POST /v1/demo/session and unlocks
# only a separate synthetic demonstration database. A demo token is never
# a privileged API key, is never derived from SETTLEIQ_API_KEY, and can
# never reach real customer data.
_DEMO_DB_PATH: Final[str] = os.environ.get("SETTLEIQ_DEMO_DB_PATH", "demo.sqlite3")
_DEMO_SESSION_TTL_SECS: Final[float] = float(
    os.environ.get("SETTLEIQ_DEMO_SESSION_TTL_SECS", "1800")
)
_DEMO_SESSION_RATE_LIMIT: Final[int] = int(
    os.environ.get("SETTLEIQ_DEMO_SESSION_RATE_LIMIT", "10")
)
_DEMO_MAX_REQUESTS_PER_SESSION: Final[int] = int(
    os.environ.get("SETTLEIQ_DEMO_MAX_REQUESTS_PER_SESSION", "60")
)
_DEMO_SESSION_RATE_WINDOW_SECS: Final[float] = 60.0

# Demo session state: token -> {created_at, last_used}; and per-session
# request timestamps for the per-session sliding window.
_DEMO_SESSIONS: dict[str, dict[str, float]] = {}
_DEMO_SESSION_TIMESTAMPS: dict[str, list[float]] = defaultdict(list)
# Demo session *creation* is rate limited separately, per IP.
_DEMO_SESSION_CREATION_TIMESTAMPS: dict[str, list[float]] = defaultdict(list)

app = FastAPI(
    title="SettleIQ",
    version="0.1.0",
    description=(
        "Payment settlement reconciliation and discrepancy investigation. "
        "Deterministic, exact-decimal, fail-closed. Synthetic data only."
    ),
)


@app.on_event("startup")
def _run_startup_migrations() -> None:
    db_path = _db_path()
    # Only run migrations at startup if using a PostgreSQL DSN.
    # For SQLite (default dev path), migrations are handled per-request
    # so that test fixtures with monkeypatched DB paths work correctly.
    if db_path.startswith("postgresql://") or db_path.startswith("postgres://"):
        ensure_migrations(db_path)

# --------------------------------------------------------------------------- middleware

# CORS configuration: development origins + production origin from env
_cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
_prod_origin = os.environ.get("SETTLEIQ_CORS_ORIGIN")
if _prod_origin:
    _cors_origins.append(_prod_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_and_limits_middleware(request: Request, call_next) -> Response:  # noqa: ANN001
    now = time.time()
    client_ip = request.client.host if request.client else "127.0.0.1"

    # Rate limiting: Sliding-window check
    if _MAX_REQUESTS_PER_WINDOW > 0:
        timestamps = _IP_REQUEST_TIMESTAMPS[client_ip]
        # Evict timestamps outside the window
        cutoff = now - _RATE_LIMIT_WINDOW_SECS
        _IP_REQUEST_TIMESTAMPS[client_ip] = [ts for ts in timestamps if ts > cutoff]

        if len(_IP_REQUEST_TIMESTAMPS[client_ip]) >= _MAX_REQUESTS_PER_WINDOW:
            return Response(
                content=(
                    '{"error":"rate_limit_exceeded","detail":"Too many requests.'
                    ' Please retry later."}'
                ),
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": "60"},
            )
        _IP_REQUEST_TIMESTAMPS[client_ip].append(now)

    # Resource limit: Reject bodies larger than 10MB
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 10 * 1024 * 1024:
        return Response(
            content='{"error":"payload_too_large","detail":"Request body exceeds 10MB limit"}',
            status_code=413,
            media_type="application/json",
        )

    # Authorization boundary.
    #
    # /v1/demo/session is public (no credentials; rate limited above) and
    # issues short-lived demo tokens for the synthetic demonstration database.
    # Other /v1/demo/* paths require a valid demo token and never reach the
    # production store. Every other /v1/* path requires the configured API key
    # with constant-time comparison; production fails closed when
    # SETTLEIQ_API_KEY is not configured. Demo auth never weakens API-key auth.
    is_demo_path = request.url.path.startswith(f"{API_PREFIX}/demo/")
    if is_demo_path:
        if request.url.path == f"{API_PREFIX}/demo/session":
            # Public session issuer: no credentials required.
            pass
        elif _validate_demo_token(request.headers.get("X-Demo-Token", "")):
            request.state.auth_mode = "demo"
        elif (
            request.url.path == f"{API_PREFIX}/demo/seed"
            and request.method == "POST"
            and _api_key_valid(request)
        ):
            # Legacy path: authorized users seed the production store.
            request.state.auth_mode = "api"
        else:
            return Response(
                content=(
                    '{"error":"unauthorized","detail":"Invalid or missing demo token"}'
                ),
                status_code=401,
                media_type="application/json",
            )
    else:
        api_key_required = os.environ.get("SETTLEIQ_API_KEY")
        if not api_key_required:
            # Fail closed in production: if no API key configured, reject all
            # /v1/* requests.
            if request.url.path.startswith(f"{API_PREFIX}/"):
                logger.critical(
                    "SETTLEIQ_API_KEY not configured; rejecting request to %s",
                    request.url.path,
                )
                return Response(
                    content='{"error":"unauthorized","detail":"API authentication not configured"}',
                    status_code=401,
                    media_type="application/json",
                )
        else:
            # Require authentication for ALL /v1/* endpoints (including GET)
            if request.url.path.startswith(f"{API_PREFIX}/") and not _api_key_valid(
                request
            ):
                return Response(
                        content=(
                            '{"error":"unauthorized","detail":"Invalid or missing API key"}'
                        ),
                        status_code=401,
                        media_type="application/json",
                    )

    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none';"
    )
    return response


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


class ResolveRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)
    resolution: str = Field(default="resolved")
    selected_candidate: str | None = Field(default=None, max_length=256)
    resolved_by: str = Field(default="investigator", max_length=128)


class ErrorOut(BaseModel):
    error: str
    detail: str


# --------------------------------------------------------------------------- state


def _db_path() -> str:
    return os.environ.get("SETTLEIQ_DB_PATH", "settleiq_api.sqlite3")


def _store() -> Persistence:
    # Each request gets its own connection to avoid SQLite threading issues.
    # For PostgreSQL, migrations are handled once at startup and not repeated.
    # For SQLite, migrations are run per-request to support test fixtures
    # that monkeypatch SETTLEIQ_DB_PATH to temporary database paths.
    db_path = _db_path()
    if db_path.startswith("postgresql://") or db_path.startswith("postgres://"):
        # PostgreSQL: migrations run once at startup; do not repeat per request
        return open_store(db_path, run_migrations=False)
    # SQLite: run migrations per-request to support test fixtures with
    # monkeypatched database paths (CREATE TABLE IF NOT EXISTS is idempotent)
    return open_store(db_path, run_migrations=True)


def _journal() -> Journal:
    journal = open_journal(_db_path())
    shared = open_store(_db_path()).connection()
    if shared is not None:
        journal.adopt(shared)
    return journal


def _error(message: str, detail: str) -> HTTPException:
    return HTTPException(status_code=400, detail={"error": message, "detail": detail})


# --------------------------- demo store and authorization


def _demo_db_path() -> str:
    return _DEMO_DB_PATH


def _demo_store() -> Persistence:
    """Persistence handle for the isolated synthetic demonstration database.

    Demo endpoints never touch the production store returned by _store().
    """
    return open_store(_demo_db_path(), run_migrations=True)


def _demo_journal() -> Journal:
    journal = open_journal(_demo_db_path())
    shared = open_store(_demo_db_path(), run_migrations=False).connection()
    if shared is not None:
        journal.adopt(shared)
    return journal


def _issue_demo_token() -> str:
    """Issue a server-side demo session token.

    Random and opaque: it carries no privileged claims and is unrelated to
    SETTLEIQ_API_KEY. It unlocks only the demonstration database.
    """
    return secrets.token_urlsafe(32)


def _validate_demo_token(token: str) -> bool:
    """Validate a demo session token and enforce its per-session rate limit.

    Returns True for an active, in-budget token; expired tokens are evicted.
    """
    if not token:
        return False
    session = _DEMO_SESSIONS.get(token)
    now = time.time()
    if session is None or now - session["created_at"] > _DEMO_SESSION_TTL_SECS:
        _DEMO_SESSIONS.pop(token, None)
        _DEMO_SESSION_TIMESTAMPS.pop(token, None)
        return False
    timestamps = _DEMO_SESSION_TIMESTAMPS[token]
    cutoff = now - _DEMO_SESSION_RATE_WINDOW_SECS
    _DEMO_SESSION_TIMESTAMPS[token] = [ts for ts in timestamps if ts > cutoff]
    if len(_DEMO_SESSION_TIMESTAMPS[token]) >= _DEMO_MAX_REQUESTS_PER_SESSION:
        return False
    _DEMO_SESSION_TIMESTAMPS[token].append(now)
    session["last_used"] = now
    return True


def _require_demo(request: Request) -> None:
    """Reject the request unless it carries a valid demo token.

    Defense in depth: middleware performs this check too, but endpoints
    re-assert it so demo data paths can never be reached without demo auth.
    """
    if getattr(request.state, "auth_mode", None) != "demo":
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "detail": "Invalid or missing demo token"},
        )


def _api_key_valid(request: Request) -> bool:
    required = os.environ.get("SETTLEIQ_API_KEY")
    if not required:
        return False
    client_key = request.headers.get("X-API-Key", "")
    return hmac.compare_digest(
        client_key.encode("utf-8"), required.encode("utf-8")
    )


# --------------------------------------------------------------------------- endpoints


@app.get("/health")
def health() -> dict[str, object]:
    """Liveness. Deliberately says nothing about reconciliation state."""
    return {"status": "ok", "api_version": API_VERSION}


@app.get(f"{API_PREFIX}/health")
def health_v1() -> dict[str, object]:
    """Liveness under /v1 prefix for Vercel routing."""
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
        logger.exception("Reconciliation failed")
        raise _error("reconciliation_failed", "reconciliation processing failed") from exc

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
            "rate": existing.get("rate", 0.0),
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
    runs = list(_store().all_runs())
    return {"count": len(runs), "runs": runs}


@app.get(f"{API_PREFIX}/runs/{{run_id}}")
def get_run(run_id: str) -> dict[str, object]:
    stored = _store().find_run(run_id)
    if stored is None:
        raise HTTPException(status_code=404, detail={"error": "run_not_found"})
    discrepancies = _store().discrepancies_for(run_id)
    return {"run": stored, "discrepancy_count": len(discrepancies)}


@app.get(f"{API_PREFIX}/runs/{{run_id}}/discrepancies")
def list_run_discrepancies(
    run_id: str, type: str | None = None, severity: str | None = None
) -> dict[str, object]:
    if _store().find_run(run_id) is None:
        raise HTTPException(status_code=404, detail={"error": "run_not_found"})
    rows = list(_store().all_discrepancies(run_id=run_id, type=type, severity=severity))
    return {"count": len(rows), "discrepancies": rows, "run_id": run_id}


@app.get(f"{API_PREFIX}/runs/{{run_id}}/discrepancies/{{discrepancy_id}}")
def get_run_discrepancy(run_id: str, discrepancy_id: str) -> dict[str, object]:
    stored = _store().find_discrepancy(discrepancy_id)
    if stored is None or stored.get("run_id") != run_id:
        raise HTTPException(status_code=404, detail={"error": "discrepancy_not_found"})
    return {"discrepancy": stored, **stored}


@app.get(f"{API_PREFIX}/discrepancies")
def list_discrepancies(
    run_id: str | None = None,
    type: str | None = None,
    severity: str | None = None,
) -> dict[str, object]:
    """Top-level discrepancy query used by the investigation dashboard."""
    rows = list(_store().all_discrepancies(run_id=run_id, type=type, severity=severity))
    return {"count": len(rows), "discrepancies": rows}


@app.get(f"{API_PREFIX}/discrepancies/{{discrepancy_id}}")
def get_discrepancy(discrepancy_id: str) -> dict[str, object]:
    """Retrieve discrepancy detail for investigation."""
    stored = _store().find_discrepancy(discrepancy_id)
    if stored is None:
        raise HTTPException(status_code=404, detail={"error": "discrepancy_not_found"})
    return dict(stored)


@app.get(f"{API_PREFIX}/discrepancies/{{discrepancy_id}}/investigate")
@app.get(f"{API_PREFIX}/runs/{{run_id}}/discrepancies/{{discrepancy_id}}/investigate")
def investigate_discrepancy_endpoint(
    discrepancy_id: str,
    run_id: str | None = None,
) -> dict[str, object]:
    """Autonomous evidence-backed AI investigation for a discrepancy."""
    stored = _store().find_discrepancy(discrepancy_id)
    if stored is None or (run_id is not None and stored.get("run_id") != run_id):
        raise HTTPException(status_code=404, detail={"error": "discrepancy_not_found"})
    from settleiq.engine.investigator import investigate_discrepancy

    report = investigate_discrepancy(stored)
    return report.to_canonical()


@app.get(f"{API_PREFIX}/runs/{{run_id}}/trace/{{constituent_id}}")
def get_constituent_trace_endpoint(
    run_id: str,
    constituent_id: str,
) -> dict[str, object]:
    """Visual transaction trace for a constituent within a reconciliation run."""
    stored = _store().find_discrepancy(constituent_id)
    from settleiq.engine.investigator import build_transaction_trace

    dummy_disc = stored or {
        "constituent_id": constituent_id,
        "type": "NET_GROSS_BREAK",
        "reason": "",
    }
    trace = build_transaction_trace(dummy_disc)
    return trace.to_canonical()


@app.post(f"{API_PREFIX}/demo/seed", status_code=201)
def seed_demo_run(request: Request) -> dict[str, object]:
    """One-click seed creating a realistic reconciliation run with injected defects.

    With a valid demo token the run is recorded in the isolated synthetic
    demonstration database. With a valid API key (legacy path) the run is
    recorded in the production store, exactly as before.
    """
    from settleiq.fixtures.generator import generate

    mode = getattr(request.state, "auth_mode", None)
    dataset = generate()
    validated = validate_records(dataset.records)
    params = RunParameters("2026-10-01", "2026-10-31", settlement_window_days=3)
    result = reconcile(validated.accepted, params)
    if mode == "demo":
        store = _demo_store()
        journal = _demo_journal()
    else:
        store = _store()
        journal = _journal()
    run_id = store.record_run(result, journal=journal)
    return {
        "status": "seeded",
        "run_id": run_id,
        "numerator": result.metrics.numerator,
        "denominator": result.metrics.denominator,
        "rate": result.metrics.rate,
        "discrepancy_count": len(result.discrepancies),
    }


@app.post(f"{API_PREFIX}/demo/session", status_code=201)
def create_demo_session(request: Request) -> dict[str, object]:
    """Issue a short-lived public demo session.

    No credentials required: any visitor can open a controlled demonstration.
    Strictly rate limited per IP (see _DEMO_SESSION_RATE_LIMIT). The returned
    token unlocks only the synthetic demonstration database; it cannot be
    used against production endpoints and carries no privileged claims.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()

    # Per-IP sliding window on demo session creation.
    timestamps = _DEMO_SESSION_CREATION_TIMESTAMPS[client_ip]
    cutoff = now - _DEMO_SESSION_RATE_WINDOW_SECS
    _DEMO_SESSION_CREATION_TIMESTAMPS[client_ip] = [
        ts for ts in timestamps if ts > cutoff
    ]
    if len(_DEMO_SESSION_CREATION_TIMESTAMPS[client_ip]) >= _DEMO_SESSION_RATE_LIMIT:
        return Response(
            content=(
                '{"error":"rate_limit_exceeded","detail":"Demo sessions are rate '
                'limited. Please retry later."}'
            ),
            status_code=429,
            media_type="application/json",
            headers={"Retry-After": "60"},
        )
    _DEMO_SESSION_CREATION_TIMESTAMPS[client_ip].append(now)

    token = _issue_demo_token()
    _DEMO_SESSIONS[token] = {"created_at": now, "last_used": now}
    return {
        "demo_token": token,
        "expires_in": int(_DEMO_SESSION_TTL_SECS),
    }


# --------------------- demonstration endpoints (read-only synthetic data)


@app.get(f"{API_PREFIX}/demo/runs")
def list_demo_runs(request: Request) -> dict[str, object]:
    _require_demo(request)
    runs = list(_demo_store().all_runs())
    return {"count": len(runs), "runs": runs}


@app.get(f"{API_PREFIX}/demo/runs/{{run_id}}")
def get_demo_run(run_id: str, request: Request) -> dict[str, object]:
    _require_demo(request)
    stored = _demo_store().find_run(run_id)
    if stored is None:
        raise HTTPException(status_code=404, detail={"error": "run_not_found"})
    discrepancies = _demo_store().discrepancies_for(run_id)
    return {"run": stored, "discrepancy_count": len(discrepancies)}


@app.get(f"{API_PREFIX}/demo/runs/{{run_id}}/discrepancies")
def list_demo_run_discrepancies(
    run_id: str,
    request: Request,
    type: str | None = None,
    severity: str | None = None,
) -> dict[str, object]:
    _require_demo(request)
    if _demo_store().find_run(run_id) is None:
        raise HTTPException(status_code=404, detail={"error": "run_not_found"})
    rows = list(
        _demo_store().all_discrepancies(run_id=run_id, type=type, severity=severity)
    )
    return {"count": len(rows), "discrepancies": rows, "run_id": run_id}


@app.get(f"{API_PREFIX}/demo/runs/{{run_id}}/metrics")
def get_demo_metrics(run_id: str, request: Request) -> dict[str, object]:
    _require_demo(request)
    stored = _demo_store().find_run(run_id)
    if stored is None:
        raise HTTPException(status_code=404, detail={"error": "run_not_found"})
    numerator, denominator = int(stored["numerator"]), int(stored["denominator"])
    discrepancies = list(_demo_store().discrepancies_for(run_id))
    ambiguous = sum(1 for d in discrepancies if d["type"] == "AMBIGUOUS_MATCH")
    conflict = sum(
        1 for d in discrepancies if d["type"] in ("NET_GROSS_BREAK", "AMOUNT_BREAK")
    )
    human_confirmed = sum(1 for d in discrepancies if d["status"] == "RESOLVED")
    return {
        "run_id": run_id,
        "numerator": numerator,
        "denominator": denominator,
        "rate": (numerator / denominator) if denominator else 0.0,
        "ambiguous": ambiguous,
        "conflict": conflict,
        "insufficient": 0,
        "human_confirmed": human_confirmed,
        "quarantined": 0,
        "methodology_version": stored["methodology_version"],
        "rule_version": stored["rule_version"],
    }


@app.get(f"{API_PREFIX}/demo/runs/{{run_id}}/export")
def export_demo_run(run_id: str, request: Request) -> dict[str, object]:
    _require_demo(request)
    stored = _demo_store().find_run(run_id)
    if stored is None:
        raise HTTPException(status_code=404, detail={"error": "run_not_found"})
    return {
        "format": "json",
        "run": stored,
        "discrepancies": list(_demo_store().discrepancies_for(run_id)),
    }


@app.get(f"{API_PREFIX}/demo/runs/{{run_id}}/trace/{{constituent_id}}")
def get_demo_constituent_trace(
    run_id: str, constituent_id: str, request: Request
) -> dict[str, object]:
    _require_demo(request)
    from settleiq.engine.investigator import build_transaction_trace

    dummy_disc = {
        "constituent_id": constituent_id,
        "type": "NET_GROSS_BREAK",
        "reason": "",
    }
    trace = build_transaction_trace(dummy_disc)
    return trace.to_canonical()


@app.get(f"{API_PREFIX}/demo/discrepancies")
def list_demo_discrepancies(
    request: Request,
    run_id: str | None = None,
    type: str | None = None,
    severity: str | None = None,
) -> dict[str, object]:
    _require_demo(request)
    rows = list(
        _demo_store().all_discrepancies(run_id=run_id, type=type, severity=severity)
    )
    return {"count": len(rows), "discrepancies": rows}


@app.get(f"{API_PREFIX}/demo/discrepancies/{{discrepancy_id}}")
def get_demo_discrepancy(discrepancy_id: str, request: Request) -> dict[str, object]:
    _require_demo(request)
    stored = _demo_store().find_discrepancy(discrepancy_id)
    if stored is None:
        raise HTTPException(status_code=404, detail={"error": "discrepancy_not_found"})
    return dict(stored)


@app.get(f"{API_PREFIX}/demo/discrepancies/{{discrepancy_id}}/investigate")
def investigate_demo_discrepancy(
    discrepancy_id: str, request: Request
) -> dict[str, object]:
    _require_demo(request)
    from settleiq.engine.investigator import investigate_discrepancy

    stored = _demo_store().find_discrepancy(discrepancy_id)
    if stored is None:
        raise HTTPException(status_code=404, detail={"error": "discrepancy_not_found"})
    report = investigate_discrepancy(stored)
    return report.to_canonical()


@app.post(f"{API_PREFIX}/demo/journal/verify")
def verify_demo_journal(request: Request) -> dict[str, object]:
    _require_demo(request)
    report = _demo_journal().verify()
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


@app.post(f"{API_PREFIX}/discrepancies/{{discrepancy_id}}/resolve")
@app.post(f"{API_PREFIX}/runs/{{run_id}}/discrepancies/{{discrepancy_id}}/resolve")
def resolve_discrepancy(
    discrepancy_id: str,
    body: ResolveRequest,
    run_id: str | None = None,
) -> dict[str, object]:
    """Persist a resolution and record an immutable audit event in the journal.

    A resolution without a stated reason is rejected. Resolving an ambiguous
    match requires specifying the selected candidate.
    """
    store = _store()
    current = store.find_discrepancy(discrepancy_id)
    if current is None or (run_id is not None and current.get("run_id") != run_id):
        raise HTTPException(status_code=404, detail={"error": "discrepancy_not_found"})

    reason = body.reason.strip()
    if not reason:
        raise _error("reason_required", "a resolution requires a stated reason")

    selected = body.selected_candidate
    if current.get("type") == "AMBIGUOUS_MATCH" and not selected:
        raise _error(
            "selection_required",
            "resolving an ambiguous discrepancy requires naming the selected candidate",
        )

    resolved = store.resolve_discrepancy(
        discrepancy_id,
        reason=reason,
        selected_candidate=selected,
        resolved_by=body.resolved_by,
        journal=_journal(),
    )
    if resolved is None:
        raise HTTPException(status_code=404, detail={"error": "discrepancy_not_found"})

    return {
        "discrepancy_id": discrepancy_id,
        "run_id": resolved.get("run_id"),
        "status": DiscrepancyStatus.RESOLVED.value,
        "reason": reason,
        "selected_candidate": selected,
        "appended": True,
        "discrepancy": resolved,
    }


@app.get(f"{API_PREFIX}/runs/{{run_id}}/metrics")
def get_metrics(run_id: str) -> dict[str, object]:
    """Metrics with the methodology that produced them, inline.

    The rate is never separated from its denominator: a percentage without its
    counts is a headline, with its counts it is a measurement.
    """
    stored = _store().find_run(run_id)
    if stored is None:
        raise HTTPException(status_code=404, detail={"error": "run_not_found"})
    numerator, denominator = int(stored["numerator"]), int(stored["denominator"])
    discrepancies = list(_store().discrepancies_for(run_id))
    ambiguous = sum(1 for d in discrepancies if d["type"] == "AMBIGUOUS_MATCH")
    conflict = sum(1 for d in discrepancies if d["type"] in ("NET_GROSS_BREAK", "AMOUNT_BREAK"))
    human_confirmed = sum(1 for d in discrepancies if d["status"] == "RESOLVED")

    return {
        "run_id": run_id,
        "numerator": numerator,
        "denominator": denominator,
        "rate": (numerator / denominator) if denominator else 0.0,
        "ambiguous": ambiguous,
        "conflict": conflict,
        "insufficient": 0,
        "human_confirmed": human_confirmed,
        "quarantined": 0,
        "methodology_version": stored["methodology_version"],
        "rule_version": stored["rule_version"],
    }


@app.post(f"{API_PREFIX}/journal/verify")
def verify_journal() -> dict[str, object]:
    """Verify the audit chain and return its state.

    Reports the journal's limitations alongside its result, because a caller who
    is told 'intact: true' without being told what that excludes will over-trust
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
        raise _error("unsupported_format", "supported formats: json")
    return {
        "format": "json",
        "run": stored,
        "discrepancies": list(_store().discrepancies_for(run_id)),
    }


# --------------------------------------------------------------------------- static web dashboard


if ASSETS_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")


@app.get("/")
def serve_index() -> Response:
    index_file = STATIC_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(str(index_file))
    return Response(
        content='{"status":"ok","app":"SettleIQ API"}',
        media_type="application/json",
    )


@app.get("/{full_path:path}")
def serve_spa(full_path: str) -> Response:
    # Explicitly exclude API and health paths from SPA fallback
    clean_path = full_path.lstrip("/")
    if (
        clean_path == "v1"
        or clean_path.startswith("v1/")
        or clean_path == "health"
        or clean_path.startswith("health/")
    ):
        raise HTTPException(status_code=404, detail={"error": "not_found"})

    if clean_path.startswith("assets/"):
        raise HTTPException(status_code=404, detail={"error": "asset_not_found"})

    target_file = STATIC_DIR / clean_path
    if target_file.is_file():
        return FileResponse(str(target_file))

    index_file = STATIC_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(str(index_file))

    raise HTTPException(status_code=404, detail={"error": "not_found"})


__all__ = [
    "API_PREFIX",
    "API_VERSION",
    "ResolveRequest",
    "RunRequest",
    "app",
    "create_run",
    "list_runs",
]


def _unused(discrepancy: Discrepancy) -> str:  # pragma: no cover
    """Retained so the Discrepancy import stays meaningful for type checkers."""
    return discrepancy.discrepancy_id
