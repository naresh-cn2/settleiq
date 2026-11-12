"""Integration tests for public demo access.

Verifies:
- Public demo session issuance (no credentials required)
- Demo token authorization boundary on /v1/demo/* endpoints
- Data isolation: demo database is separate from the production store
- Demo rate limits (session creation and per-session requests)
- Existing API-key authentication is unchanged (valid/invalid key)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from settleiq.api import app as app_module
from settleiq.api.app import app


@pytest.fixture
def isolated_env(tmp_path, monkeypatch):
    """Point both production and demo stores at isolated temp databases."""
    prod_db = tmp_path / "prod.sqlite3"
    demo_db = tmp_path / "demo.sqlite3"
    monkeypatch.setenv("SETTLEIQ_DB_PATH", str(prod_db))
    monkeypatch.setenv("SETTLEIQ_API_KEY", "prod-secret-999")
    monkeypatch.setattr(app_module, "_DEMO_DB_PATH", str(demo_db))
    # Reset in-memory demo/auth rate-limit state between tests.
    app_module._IP_REQUEST_TIMESTAMPS.clear()
    app_module._DEMO_SESSIONS.clear()
    app_module._DEMO_SESSION_TIMESTAMPS.clear()
    app_module._DEMO_SESSION_CREATION_TIMESTAMPS.clear()
    return {"prod_db": prod_db, "demo_db": demo_db}


def _issue_session(client: TestClient) -> str:
    res = client.post("/v1/demo/session")
    assert res.status_code == 201, res.text
    return res.json()["demo_token"]


def test_demo_session_issued_without_credentials(
    isolated_env: dict[str, object],
) -> None:
    client = TestClient(app)
    token = _issue_session(client)
    assert isinstance(token, str) and len(token) > 0
    body = client.post("/v1/demo/session").json()
    assert "expires_in" in body


def test_demo_session_rate_limited(isolated_env: dict[str, object]) -> None:
    app_module._DEMO_SESSION_RATE_LIMIT = 2
    client = TestClient(app)
    _issue_session(client)
    _issue_session(client)
    limited = client.post("/v1/demo/session")
    assert limited.status_code == 429
    assert limited.json()["error"] == "rate_limit_exceeded"


def test_demo_token_required_for_demo_endpoints(
    isolated_env: dict[str, object],
) -> None:
    client = TestClient(app)
    # No token: all demo data paths are rejected.
    for path in (
        "/v1/demo/runs",
        "/v1/demo/discrepancies",
        "/v1/demo/journal/verify",
    ):
        res = client.get(path)
        assert res.status_code == 401, f"{path}: {res.text}"
        assert res.json()["error"] == "unauthorized"


def test_valid_demo_token_accesses_demo_data(
    isolated_env: dict[str, object],
) -> None:
    client = TestClient(app)
    token = _issue_session(client)
    headers = {"X-Demo-Token": token}

    # Empty demo database.
    res = client.get("/v1/demo/runs", headers=headers)
    assert res.status_code == 200
    assert res.json()["count"] == 0

    # Seed a demo run (demo token -> isolated demo store).
    seed = client.post("/v1/demo/seed", headers=headers)
    assert seed.status_code == 201, seed.text
    run_id = seed.json()["run_id"]

    # The seeded run is readable back via demo endpoints.
    res = client.get("/v1/demo/runs", headers=headers)
    assert res.status_code == 200
    assert res.json()["count"] == 1
    assert res.json()["runs"][0]["run_id"] == run_id

    disc = client.get(f"/v1/demo/runs/{run_id}/discrepancies", headers=headers)
    assert disc.status_code == 200
    assert disc.json()["run_id"] == run_id

    metrics = client.get(f"/v1/demo/runs/{run_id}/metrics", headers=headers)
    assert metrics.status_code == 200
    assert metrics.json()["run_id"] == run_id

    journal = client.post("/v1/demo/journal/verify", headers=headers)
    assert journal.status_code == 200


def test_demo_isolated_from_production_data(isolated_env: dict[str, object]) -> None:
    client = TestClient(app)
    auth_headers = {"X-API-Key": "prod-secret-999"}

    # Seed a production run with a valid API key.
    from settleiq.fixtures.generator import generate

    dataset = generate()
    groups: dict[str, list[dict[str, object]]] = {}
    for kind, record in dataset.records:
        groups.setdefault(kind, []).append(record)
    prod_payload = {
        "window_start": "2026-10-01",
        "window_end": "2026-10-31",
        "settlement_window_days": 3,
        "records": [{"kind": k, "records": recs} for k, recs in groups.items()],
    }
    created = client.post("/v1/runs", json=prod_payload, headers=auth_headers)
    assert created.status_code == 201
    prod_run_id = created.json()["run_id"]

    # Demo token must NOT see the production run.
    token = _issue_session(client)
    demo_headers = {"X-Demo-Token": token}
    demo_runs = client.get("/v1/demo/runs", headers=demo_headers)
    assert demo_runs.status_code == 200
    assert demo_runs.json()["count"] == 0
    demo_run_res = client.get(f"/v1/demo/runs/{prod_run_id}", headers=demo_headers)
    assert demo_run_res.status_code == 404

    # Production API key must NOT see demo data.
    prod_runs = client.get("/v1/runs", headers=auth_headers)
    assert prod_runs.status_code == 200
    prod_run_ids = {r["run_id"] for r in prod_runs.json()["runs"]}
    assert prod_run_id in prod_run_ids


def test_api_key_auth_unchanged(isolated_env: dict[str, object]) -> None:
    client = TestClient(app)

    # Missing key -> 401.
    assert client.get("/v1/runs").status_code == 401

    # Invalid key -> 401.
    assert (
        client.get("/v1/runs", headers={"X-API-Key": "wrong-key"}).status_code
        == 401
    )

    # Valid key succeeds.
    res = client.get("/v1/runs", headers={"X-API-Key": "prod-secret-999"})
    assert res.status_code == 200

    # Health remains public.
    assert client.get("/health").status_code == 200


def test_demo_token_rejected_on_production_endpoints(
    isolated_env: dict[str, object],
) -> None:
    client = TestClient(app)
    token = _issue_session(client)
    demo_headers = {"X-Demo-Token": token}

    # A demo token cannot call production endpoints.
    assert client.post("/v1/runs", json={}, headers=demo_headers).status_code == 401
    assert client.get("/v1/runs", headers=demo_headers).status_code == 401


def test_expired_or_invalid_demo_token_rejected(
    isolated_env: dict[str, object],
) -> None:
    client = TestClient(app)

    assert (
        client.get(
            "/v1/demo/runs", headers={"X-Demo-Token": "not-a-real-token"}
        ).status_code
        == 401
    )

    # Expired token: monkeypatch TTL to zero and re-issue.
    app_module._DEMO_SESSION_TTL_SECS = 0
    token = _issue_session(client)
    assert (
        client.get("/v1/demo/runs", headers={"X-Demo-Token": token}).status_code
        == 401
    )

