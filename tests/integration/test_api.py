"""Integration tests for the SettleIQ REST API and dashboard delivery.

Tests all endpoints, idempotency, genuine discrepancy resolution, journal
integrity atomicity, static dashboard delivery, security limits, and error
handling against isolated temporary databases.
"""

from __future__ import annotations

from collections.abc import Mapping

import pytest
from fastapi.testclient import TestClient

from settleiq.api.app import app
from settleiq.fixtures.generator import generate


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    db_file = tmp_path / "test_api.sqlite3"
    monkeypatch.setenv("SETTLEIQ_DB_PATH", str(db_file))
    return TestClient(app)


@pytest.fixture
def run_payload() -> dict[str, object]:
    dataset = generate()
    groups: dict[str, list[Mapping[str, object]]] = {}
    for kind, record in dataset.records:
        groups.setdefault(kind, []).append(record)

    return {
        "window_start": "2026-10-01",
        "window_end": "2026-10-31",
        "settlement_window_days": 3,
        "records": [{"kind": k, "records": recs} for k, recs in groups.items()],
    }


def test_health_endpoint(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["api_version"] == "1"


def test_create_run_and_idempotency_replay(
    client: TestClient, run_payload: dict[str, object]
) -> None:
    # 1. First run creation
    res = client.post("/v1/runs", json=run_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["replayed"] is False
    assert "run_id" in data
    assert data["numerator"] == 19
    assert data["denominator"] == 25
    assert data["rate"] == 0.76
    assert data["discrepancy_count"] == 7
    run_id = data["run_id"]

    # 2. Idempotent replay with same inputs
    replay_res = client.post("/v1/runs", json=run_payload)
    assert replay_res.status_code == 201
    assert replay_res.headers.get("Idempotency-Replayed") == "true"
    replay_data = replay_res.json()
    assert replay_data["replayed"] is True
    assert replay_data["run_id"] == run_id
    assert replay_data["numerator"] == 19
    assert replay_data["denominator"] == 25
    assert replay_data["rate"] == 0.76


def test_create_run_rejects_completely_invalid_records(client: TestClient) -> None:
    bad_payload = {
        "window_start": "2026-10-01",
        "window_end": "2026-10-31",
        "settlement_window_days": 3,
        "records": [
            {
                "kind": "charge",
                "records": [{"id": "bad_1", "amount": "invalid-amount", "currency": "USD"}],
            }
        ],
    }
    res = client.post("/v1/runs", json=bad_payload)
    assert res.status_code == 400
    assert "quarantined" in str(res.json())


def test_list_runs_includes_computed_rate(
    client: TestClient, run_payload: dict[str, object]
) -> None:
    client.post("/v1/runs", json=run_payload)

    res = client.get("/v1/runs")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 1
    run = data["runs"][0]
    assert run["numerator"] == 19
    assert run["denominator"] == 25
    assert run["rate"] == 0.76  # Guarantees UI does not show NaN%


def test_get_run_detail_and_not_found(client: TestClient, run_payload: dict[str, object]) -> None:
    created = client.post("/v1/runs", json=run_payload).json()
    run_id = created["run_id"]

    res = client.get(f"/v1/runs/{run_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["run"]["run_id"] == run_id
    assert data["discrepancy_count"] == 7

    missing = client.get("/v1/runs/nonexistent-run-id")
    assert missing.status_code == 404
    assert missing.json()["detail"]["error"] == "run_not_found"


def test_list_discrepancies_top_level_and_run_scoped(
    client: TestClient, run_payload: dict[str, object]
) -> None:
    created = client.post("/v1/runs", json=run_payload).json()
    run_id = created["run_id"]

    # 1. Top-level query (what the frontend DiscrepanciesPage calls)
    top_res = client.get("/v1/discrepancies")
    assert top_res.status_code == 200
    assert top_res.json()["count"] == 7

    # Filtered by type
    filtered_type = client.get("/v1/discrepancies?type=AMOUNT_BREAK")
    assert filtered_type.status_code == 200
    assert filtered_type.json()["count"] == 1
    assert filtered_type.json()["discrepancies"][0]["type"] == "AMOUNT_BREAK"

    # Filtered by severity
    filtered_sev = client.get("/v1/discrepancies?severity=HIGH")
    assert filtered_sev.status_code == 200
    assert all(d["severity"] == "HIGH" for d in filtered_sev.json()["discrepancies"])

    # 2. Run-scoped query
    run_res = client.get(f"/v1/runs/{run_id}/discrepancies")
    assert run_res.status_code == 200
    assert run_res.json()["count"] == 7


def test_discrepancy_detail_and_investigation(
    client: TestClient, run_payload: dict[str, object]
) -> None:
    created = client.post("/v1/runs", json=run_payload).json()
    run_id = created["run_id"]

    discs = client.get(f"/v1/runs/{run_id}/discrepancies").json()["discrepancies"]
    first = discs[0]
    disc_id = first["discrepancy_id"]

    # Top-level endpoint called by InvestigationPage
    res = client.get(f"/v1/discrepancies/{disc_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["discrepancy_id"] == disc_id
    assert data["status"] == "OPEN"
    assert "resolution_history" in data
    assert len(data["resolution_history"]) == 0

    # Nonexistent
    missing = client.get("/v1/discrepancies/nonexistent_disc_id")
    assert missing.status_code == 404


def test_discrepancy_resolution_persists_and_journals(
    client: TestClient, run_payload: dict[str, object]
) -> None:
    created = client.post("/v1/runs", json=run_payload).json()
    run_id = created["run_id"]

    discs = client.get(f"/v1/runs/{run_id}/discrepancies").json()["discrepancies"]
    disc_id = discs[0]["discrepancy_id"]

    # 1. Resolve discrepancy
    resolve_body = {
        "reason": "Matched to bank statement line item ref #982",
        "resolution": "resolved",
        "selected_candidate": "cand_target",
        "resolved_by": "analyst_bob",
    }
    res = client.post(f"/v1/discrepancies/{disc_id}/resolve", json=resolve_body)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "RESOLVED"
    assert data["appended"] is True
    assert data["reason"] == resolve_body["reason"]

    # 2. Verify subsequent retrieval reflects RESOLVED status and records history
    detail = client.get(f"/v1/discrepancies/{disc_id}").json()
    assert detail["status"] == "RESOLVED"
    assert len(detail["resolution_history"]) == 1
    history = detail["resolution_history"][0]
    assert history["reason"] == resolve_body["reason"]
    assert history["selected_candidate"] == "cand_target"
    assert history["resolved_by"] == "analyst_bob"
    assert "resolved_at" in history

    # 3. Verify audit journal has recorded the resolution event
    verify_res = client.post("/v1/journal/verify")
    assert verify_res.status_code == 200
    journal_report = verify_res.json()
    assert journal_report["intact"] is True
    # 1 entry for the run, 1 entry for the resolution
    assert journal_report["entries_verified"] == 2


def test_discrepancy_resolution_validations(
    client: TestClient, run_payload: dict[str, object]
) -> None:
    client.post("/v1/runs", json=run_payload)
    discs = client.get("/v1/discrepancies").json()["discrepancies"]

    ambiguous = next(d for d in discs if d["type"] == "AMBIGUOUS_MATCH")
    amb_id = ambiguous["discrepancy_id"]

    # Missing reason
    res_empty = client.post(f"/v1/discrepancies/{amb_id}/resolve", json={"reason": ""})
    assert res_empty.status_code in (400, 422)

    # Ambiguous match missing candidate selection
    res_no_cand = client.post(
        f"/v1/discrepancies/{amb_id}/resolve",
        json={"reason": "Human approval without choosing candidate"},
    )
    assert res_no_cand.status_code == 400
    assert "selected candidate" in res_no_cand.json()["detail"]["detail"]

    # Nonexistent discrepancy
    res_missing = client.post(
        "/v1/discrepancies/nonexistent_id/resolve",
        json={"reason": "Does not exist"},
    )
    assert res_missing.status_code == 404


def test_metrics_endpoint_breakdown(client: TestClient, run_payload: dict[str, object]) -> None:
    created = client.post("/v1/runs", json=run_payload).json()
    run_id = created["run_id"]

    # Before resolution
    m1 = client.get(f"/v1/runs/{run_id}/metrics").json()
    assert m1["numerator"] == 19
    assert m1["denominator"] == 25
    assert m1["rate"] == 0.76
    assert m1["ambiguous"] == 1
    assert m1["human_confirmed"] == 0

    # Resolve one discrepancy
    discs = client.get(f"/v1/runs/{run_id}/discrepancies").json()["discrepancies"]
    client.post(
        f"/v1/discrepancies/{discs[0]['discrepancy_id']}/resolve",
        json={"reason": "Resolved by reviewer"},
    )

    # After resolution
    m2 = client.get(f"/v1/runs/{run_id}/metrics").json()
    assert m2["human_confirmed"] == 1


def test_export_run(client: TestClient, run_payload: dict[str, object]) -> None:
    created = client.post("/v1/runs", json=run_payload).json()
    run_id = created["run_id"]

    res = client.get(f"/v1/runs/{run_id}/export")
    assert res.status_code == 200
    data = res.json()
    assert data["format"] == "json"
    assert data["run"]["run_id"] == run_id
    assert len(data["discrepancies"]) == 7

    bad_format = client.get(f"/v1/runs/{run_id}/export?format=csv")
    assert bad_format.status_code == 400


def test_static_dashboard_delivery(client: TestClient) -> None:
    # Root serves index.html
    root = client.get("/")
    assert root.status_code == 200
    assert "<!doctype html>" in root.text.lower() or "<html" in root.text.lower()

    # SPA route direct navigation serves index.html
    spa_disc = client.get("/discrepancies")
    assert spa_disc.status_code == 200
    assert "<!doctype html>" in spa_disc.text.lower() or "<html" in spa_disc.text.lower()

    spa_investigation = client.get("/discrepancies/dsc:123")
    assert spa_investigation.status_code == 200

    # Missing API route does NOT return index.html
    api_missing = client.get("/v1/unknown-endpoint")
    assert api_missing.status_code == 404
    assert api_missing.headers.get("content-type", "").startswith("application/json")

    # Missing asset does NOT return index.html
    asset_missing = client.get("/assets/missing-file.js")
    assert asset_missing.status_code == 404


def test_security_headers_and_payload_limits(client: TestClient) -> None:
    res = client.get("/health")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("Content-Security-Policy") is not None

    # Payload larger than 10MB
    large_payload_headers = {"Content-Length": str(11 * 1024 * 1024)}
    too_large = client.post("/v1/runs", headers=large_payload_headers, json={"records": []})
    assert too_large.status_code == 413
    assert too_large.json()["error"] == "payload_too_large"


def test_api_key_boundary_enforcement(
    tmp_path, monkeypatch, run_payload: dict[str, object]
) -> None:
    db_file = tmp_path / "auth_test.sqlite3"
    monkeypatch.setenv("SETTLEIQ_DB_PATH", str(db_file))
    monkeypatch.setenv("SETTLEIQ_API_KEY", "prod-secret-999")
    auth_client = TestClient(app)

    # 1. Read-only endpoints do not require API key
    health = auth_client.get("/health")
    assert health.status_code == 200

    list_runs = auth_client.get("/v1/runs")
    assert list_runs.status_code == 200

    # 2. Mutating endpoint without key is rejected
    unauth = auth_client.post("/v1/runs", json=run_payload)
    assert unauth.status_code == 401
    assert unauth.json()["error"] == "unauthorized"

    # 3. Mutating endpoint with invalid key is rejected
    bad_key = auth_client.post(
        "/v1/runs", json=run_payload, headers={"X-API-Key": "wrong-key"}
    )
    assert bad_key.status_code == 401

    # 4. Mutating endpoint with correct key succeeds
    authed = auth_client.post(
        "/v1/runs", json=run_payload, headers={"X-API-Key": "prod-secret-999"}
    )
    assert authed.status_code == 201
