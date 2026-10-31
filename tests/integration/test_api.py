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
    monkeypatch.setenv("SETTLEIQ_API_KEY", "test-api-key-123")
    return TestClient(app, headers={"X-API-Key": "test-api-key-123"})


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
    assert data["count"] >= 1
    assert "rate" in data["runs"][0]
    assert isinstance(data["runs"][0]["rate"], float)


def test_get_run_detail_and_not_found(
    client: TestClient, run_payload: dict[str, object]
) -> None:
    created = client.post("/v1/runs", json=run_payload).json()
    run_id = created["run_id"]

    detail = client.get(f"/v1/runs/{run_id}")
    assert detail.status_code == 200
    assert detail.json()["run"]["run_id"] == run_id

    not_found = client.get("/v1/runs/nonexistent-id")
    assert not_found.status_code == 404
    assert not_found.json()["detail"]["error"] == "run_not_found"


def test_list_discrepancies_top_level_and_run_scoped(
    client: TestClient, run_payload: dict[str, object]
) -> None:
    created = client.post("/v1/runs", json=run_payload).json()
    run_id = created["run_id"]

    all_discs = client.get("/v1/discrepancies").json()
    assert "count" in all_discs
    assert "discrepancies" in all_discs

    run_discs = client.get(f"/v1/runs/{run_id}/discrepancies").json()
    assert run_discs["run_id"] == run_id
    assert "count" in run_discs
    assert "discrepancies" in run_discs


def test_discrepancy_detail_and_investigation(
    client: TestClient, run_payload: dict[str, object]
) -> None:
    created = client.post("/v1/runs", json=run_payload).json()
    run_id = created["run_id"]

    discs = client.get(f"/v1/runs/{run_id}/discrepancies").json()["discrepancies"]
    assert len(discs) > 0
    first_disc = discs[0]
    disc_id = first_disc["discrepancy_id"]

    detail = client.get(f"/v1/discrepancies/{disc_id}")
    assert detail.status_code == 200
    assert detail.json()["discrepancy_id"] == disc_id

    investigation = client.get(f"/v1/discrepancies/{disc_id}/investigate")
    assert investigation.status_code == 200
    inv_data = investigation.json()
    assert inv_data["discrepancy_id"] == disc_id
    assert "hypotheses" in inv_data
    assert "trace" in inv_data
    assert "draft_resolution" in inv_data

    trace = client.get(f"/v1/runs/{run_id}/trace/{first_disc['constituent_id']}")
    assert trace.status_code == 200
    trace_data = trace.json()
    assert "nodes" in trace_data


def test_discrepancy_resolution_persists_and_journals(
    client: TestClient, run_payload: dict[str, object]
) -> None:
    created = client.post("/v1/runs", json=run_payload).json()
    run_id = created["run_id"]

    discs = client.get(f"/v1/runs/{run_id}/discrepancies").json()["discrepancies"]
    target_disc = next(d for d in discs if d["type"] == "NET_GROSS_BREAK")
    disc_id = target_disc["discrepancy_id"]

    # Resolve the discrepancy
    resolve_resp = client.post(
        f"/v1/discrepancies/{disc_id}/resolve",
        json={"reason": "Test resolution", "resolved_by": "tester"},
    )
    assert resolve_resp.status_code == 200
    resolved = resolve_resp.json()
    assert resolved["status"] == "RESOLVED"
    assert resolved["discrepancy_id"] == disc_id

    # Verify persistence
    check = client.get(f"/v1/discrepancies/{disc_id}")
    assert check.json()["status"] == "RESOLVED"

    # Verify journal integrity
    journal_res = client.post("/v1/journal/verify")
    assert journal_res.json()["intact"] is True


def test_discrepancy_resolution_validations(
    client: TestClient, run_payload: dict[str, object]
) -> None:
    client.post("/v1/runs", json=run_payload)

    discs = client.get("/v1/discrepancies").json()["discrepancies"]
    ambig = next(d for d in discs if d["type"] == "AMBIGUOUS_MATCH")
    disc_id = ambig["discrepancy_id"]

    # Missing reason
    bad = client.post(
        f"/v1/discrepancies/{disc_id}/resolve",
        json={"reason": "", "resolved_by": "tester"},
    )
    assert bad.status_code == 422
    # FastAPI validation error format
    assert any("string_too_short" in str(e) for e in bad.json()["detail"])

    # Missing candidate for ambiguous
    bad2 = client.post(
        f"/v1/discrepancies/{disc_id}/resolve",
        json={"reason": "Test", "resolved_by": "tester"},
    )
    assert bad2.status_code == 400
    assert "selection_required" in bad2.json()["detail"]["error"]

    # Valid resolution with candidate
    good = client.post(
        f"/v1/discrepancies/{disc_id}/resolve",
        json={
            "reason": "Selected correct match",
            "resolved_by": "tester",
            "selected_candidate": "cand_1",
        },
    )
    assert good.status_code == 200


def test_metrics_endpoint_breakdown(
    client: TestClient, run_payload: dict[str, object]
) -> None:
    created = client.post("/v1/runs", json=run_payload).json()
    run_id = created["run_id"]

    metrics = client.get(f"/v1/runs/{run_id}/metrics")
    assert metrics.status_code == 200
    data = metrics.json()
    assert data["run_id"] == run_id
    assert data["numerator"] == 19
    assert data["denominator"] == 25
    assert data["ambiguous"] >= 0
    assert data["methodology_version"]


def test_export_run(
    client: TestClient, run_payload: dict[str, object]
) -> None:
    created = client.post("/v1/runs", json=run_payload).json()
    run_id = created["run_id"]

    export = client.get(f"/v1/runs/{run_id}/export")
    assert export.status_code == 200
    data = export.json()
    assert data["format"] == "json"
    assert data["run"]["run_id"] == run_id
    assert "discrepancies" in data


def test_payload_too_large(client: TestClient) -> None:
    too_large = client.post(
        "/v1/runs",
        headers={"Content-Length": str(11 * 1024 * 1024)},
        json={"records": []},
    )
    assert too_large.status_code == 413
    assert too_large.json()["error"] == "payload_too_large"


def test_api_key_boundary_enforcement(
    tmp_path, monkeypatch, run_payload: dict[str, object]
) -> None:
    db_file = tmp_path / "auth_test.sqlite3"
    monkeypatch.setenv("SETTLEIQ_DB_PATH", str(db_file))
    monkeypatch.setenv("SETTLEIQ_API_KEY", "prod-secret-999")
    auth_client = TestClient(app)

    # 1. Health endpoint is public (no auth required)
    health = auth_client.get("/health")
    assert health.status_code == 200

    # 2. All /v1/* endpoints require authentication
    list_runs = auth_client.get("/v1/runs")
    assert list_runs.status_code == 401
    assert list_runs.json()["error"] == "unauthorized"

    # 2. Mutating endpoint without key is rejected
    unauth = auth_client.post("/v1/runs", json=run_payload)
    assert unauth.status_code == 401
    assert unauth.json()["error"] == "unauthorized"

    # 3. Mutating endpoint with invalid key is rejected
    bad_key = auth_client.post(
        "/v1/runs", json=run_payload, headers={"X-API-Key": "wrong-key"}
    )
    assert bad_key.status_code == 401
    assert bad_key.json()["error"] == "unauthorized"

    # 4. Mutating endpoint with correct key succeeds
    authed = auth_client.post(
        "/v1/runs", json=run_payload, headers={"X-API-Key": "prod-secret-999"}
    )
    assert authed.status_code == 201


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
    assert api_missing.json()["detail"]["error"] == "not_found"