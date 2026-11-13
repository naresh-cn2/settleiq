"""Integration tests for public demo access (stateless architecture).

Verifies:
- Public demo session issuance (no credentials required, signed tokens)
- Demo token signature validation and expiration
- Demo token authorization boundary on /v1/demo/* endpoints
- Stable deterministic demo data across requests and instances
- Demo token rejection on production endpoints
- Existing API-key authentication is unchanged (valid/invalid key)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

import pytest
from fastapi.testclient import TestClient

from settleiq.api import app as app_module
from settleiq.api.app import app

DEMO_SECRET = "test-demo-secret-do-not-use-in-production"


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _issue_test_token(ttl_secs: float = 1800.0, iat_offset: float = 0.0) -> str:
    now = time.time() + iat_offset
    exp = now + ttl_secs
    nonce = "testnonce1234567890"
    payload = json.dumps(
        {"iat": now, "exp": exp, "nonce": nonce}, separators=(",", ":")
    )
    signature = hmac.new(
        DEMO_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).digest()
    return f"{_b64url_encode(payload.encode('utf-8'))}.{_b64url_encode(signature)}"


def _tampered_token() -> str:
    now = time.time()
    exp = now + 1800.0
    payload = json.dumps(
        {"iat": now, "exp": exp, "nonce": "bad"}, separators=(",", ":")
    )
    sig = b"\x00" * 32
    return (
        f"{_b64url_encode(payload.encode('utf-8'))}."
        f"{base64.urlsafe_b64encode(sig).rstrip(b'=').decode('ascii')}"
    )


@pytest.fixture
def demo_env(monkeypatch):
    monkeypatch.setenv("SETTLEIQ_DEMO_SECRET", DEMO_SECRET)
    monkeypatch.setenv("SETTLEIQ_DB_PATH", ":memory:")
    monkeypatch.setenv("SETTLEIQ_API_KEY", "prod-secret-999")
    app_module._IP_REQUEST_TIMESTAMPS.clear()
    app_module._DEMO_SESSION_CREATION_TIMESTAMPS.clear()
    app_module._DEMO_DATA = None
    yield


def _issue_session(client: TestClient) -> str:
    res = client.post("/v1/demo/session")
    assert res.status_code == 201, res.text
    return res.json()["demo_token"]


def test_demo_session_issued_without_credentials(demo_env: None) -> None:
    client = TestClient(app)
    token = _issue_session(client)
    assert isinstance(token, str) and len(token) > 0
    body = client.post("/v1/demo/session").json()
    assert "expires_in" in body
    assert body["expires_in"] > 0


def test_demo_session_rate_limited(demo_env: None) -> None:
    app_module._DEMO_SESSION_RATE_LIMIT = 2
    client = TestClient(app)
    _issue_session(client)
    _issue_session(client)
    limited = client.post("/v1/demo/session")
    assert limited.status_code == 429
    assert limited.json()["error"] == "rate_limit_exceeded"


def test_demo_session_fails_when_secret_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SETTLEIQ_DEMO_SECRET", raising=False)
    app_module._DEMO_SECRET = ""
    app_module._IP_REQUEST_TIMESTAMPS.clear()
    app_module._DEMO_SESSION_CREATION_TIMESTAMPS.clear()
    client = TestClient(app)
    res = client.post("/v1/demo/session")
    assert res.status_code == 503


def test_demo_token_required_for_demo_endpoints(demo_env: None) -> None:
    client = TestClient(app)
    for path in (
        "/v1/demo/runs",
        "/v1/demo/discrepancies",
        "/v1/demo/journal/verify",
    ):
        res = client.get(path)
        assert res.status_code == 401, f"{path}: {res.text}"
        assert res.json()["error"] == "unauthorized"


def test_valid_demo_token_accesses_demo_data(demo_env: None) -> None:
    client = TestClient(app)
    token = _issue_session(client)
    headers = {"X-Demo-Token": token}

    res = client.get("/v1/demo/runs", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["count"] == 1
    assert "run_id" in body["runs"][0]

    run_id = body["runs"][0]["run_id"]

    res = client.get(f"/v1/demo/runs/{run_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["run"]["run_id"] == run_id

    res = client.get(f"/v1/demo/runs/{run_id}/discrepancies", headers=headers)
    assert res.status_code == 200
    assert res.json()["run_id"] == run_id
    assert res.json()["count"] > 0

    res = client.get(f"/v1/demo/runs/{run_id}/metrics", headers=headers)
    assert res.status_code == 200
    assert res.json()["run_id"] == run_id
    assert res.json()["numerator"] > 0
    assert res.json()["denominator"] > 0

    res = client.get(f"/v1/demo/runs/{run_id}/export", headers=headers)
    assert res.status_code == 200
    assert res.json()["format"] == "json"

    discrepancies = client.get(
        f"/v1/demo/runs/{run_id}/discrepancies", headers=headers
    ).json()["discrepancies"]
    constituent_id = discrepancies[0]["constituent_id"]
    res = client.get(
        f"/v1/demo/runs/{run_id}/trace/{constituent_id}", headers=headers
    )
    assert res.status_code == 200
    assert len(res.json()["nodes"]) > 0

    res = client.get(f"/v1/demo/runs/{run_id}/history", headers=headers)
    assert res.status_code == 200
    assert res.json()["count"] >= 2
    assert res.json()["entries"][0]["event"] == "RUN_COMPLETED"

    res = client.post("/v1/demo/journal/verify", headers=headers)
    assert res.status_code == 200
    assert res.json()["intact"] is True


def test_invalid_demo_token_rejected(demo_env: None) -> None:
    client = TestClient(app)
    res = client.get(
        "/v1/demo/runs", headers={"X-Demo-Token": "not-a-real-token"}
    )
    assert res.status_code == 401
    res = client.get("/v1/demo/runs", headers={"X-Demo-Token": _tampered_token()})
    assert res.status_code == 401


def test_expired_demo_token_rejected(demo_env: None) -> None:
    client = TestClient(app)
    token = _issue_test_token(ttl_secs=-1.0)
    res = client.get("/v1/demo/runs", headers={"X-Demo-Token": token})
    assert res.status_code == 401


def test_demo_data_stable_across_requests(demo_env: None) -> None:
    client = TestClient(app)
    token = _issue_session(client)
    headers = {"X-Demo-Token": token}

    res1 = client.get("/v1/demo/runs", headers=headers)
    res2 = client.get("/v1/demo/runs", headers=headers)
    assert res1.json()["runs"][0]["run_id"] == res2.json()["runs"][0]["run_id"]
    assert res1.json() == res2.json()


def test_demo_discrepancies_list(demo_env: None) -> None:
    client = TestClient(app)
    token = _issue_session(client)
    headers = {"X-Demo-Token": token}

    res = client.get("/v1/demo/discrepancies", headers=headers)
    assert res.status_code == 200
    assert res.json()["count"] > 0

    res = client.get("/v1/demo/discrepancies?type=NET_GROSS_BREAK", headers=headers)
    assert res.status_code == 200
    for d in res.json()["discrepancies"]:
        assert d["type"] == "NET_GROSS_BREAK"


def test_demo_discrepancy_detail(demo_env: None) -> None:
    client = TestClient(app)
    token = _issue_session(client)
    headers = {"X-Demo-Token": token}

    res = client.get("/v1/demo/discrepancies", headers=headers)
    disc_id = res.json()["discrepancies"][0]["discrepancy_id"]

    res = client.get(f"/v1/demo/discrepancies/{disc_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["discrepancy_id"] == disc_id

    res = client.get(
        f"/v1/demo/discrepancies/{disc_id}/investigate", headers=headers
    )
    assert res.status_code == 200
    assert res.json()["discrepancy_id"] == disc_id
    assert "trace" in res.json()
    assert "hypotheses" in res.json()


def test_demo_isolated_from_production_data(demo_env: None) -> None:
    client = TestClient(app)
    token = _issue_session(client)
    demo_headers = {"X-Demo-Token": token}
    demo_runs = client.get("/v1/demo/runs", headers=demo_headers)
    assert demo_runs.status_code == 200
    assert demo_runs.json()["count"] == 1


def test_api_key_auth_unchanged(demo_env: None) -> None:
    client = TestClient(app)

    assert client.get("/v1/runs").status_code == 401

    assert (
        client.get("/v1/runs", headers={"X-API-Key": "wrong-key"}).status_code
        == 401
    )

    res = client.get("/v1/runs", headers={"X-API-Key": "prod-secret-999"})
    assert res.status_code == 200

    assert client.get("/health").status_code == 200


def test_demo_token_rejected_on_production_endpoints(demo_env: None) -> None:
    client = TestClient(app)
    token = _issue_session(client)
    demo_headers = {"X-Demo-Token": token}

    assert client.post("/v1/runs", json={}, headers=demo_headers).status_code == 401
    assert client.get("/v1/runs", headers=demo_headers).status_code == 401


def test_demo_seed_with_demo_token(demo_env: None) -> None:
    client = TestClient(app)
    token = _issue_session(client)
    headers = {"X-Demo-Token": token}

    res = client.post("/v1/demo/seed", headers=headers)
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "seeded"
    assert "run_id" in body
    assert body["numerator"] > 0
    assert body["denominator"] > 0
    assert body["discrepancy_count"] > 0


def test_demo_run_and_discrepancy_records_are_complete(demo_env: None) -> None:
    client = TestClient(app)
    token = _issue_session(client)
    headers = {"X-Demo-Token": token}

    runs = client.get("/v1/demo/runs", headers=headers).json()["runs"]
    assert len(runs) == 1
    run = runs[0]
    assert run["discrepancy_count"] == 7
    assert len(run["run_id"]) == 64

    discrepancies = client.get("/v1/demo/discrepancies", headers=headers).json()[
        "discrepancies"
    ]
    assert len(discrepancies) == run["discrepancy_count"]
    for discrepancy in discrepancies:
        assert discrepancy["run_id"] == run["run_id"]
        assert "contributing_records" in discrepancy
        assert "resolution_history" in discrepancy

    detail = client.get(
        f"/v1/demo/discrepancies/{discrepancies[0]['discrepancy_id']}",
        headers=headers,
    )
    assert detail.status_code == 200
    assert detail.json()["run_id"] == run["run_id"]


def test_demo_history_is_deterministic_and_stable(demo_env: None) -> None:
    client = TestClient(app)
    token = _issue_session(client)
    headers = {"X-Demo-Token": token}
    run_id = client.get("/v1/demo/runs", headers=headers).json()["runs"][0]["run_id"]

    first = client.get(f"/v1/demo/runs/{run_id}/history", headers=headers)
    second = client.get(f"/v1/demo/runs/{run_id}/history", headers=headers)
    assert first.status_code == 200
    assert first.json() == second.json()
    entries = first.json()["entries"]
    assert first.json()["count"] == len(entries)
    assert entries[0]["event"] == "RUN_COMPLETED"
    assert any(entry["event"] == "DISCREPANCY_DETECTED" for entry in entries)


def test_demo_trace_uses_real_constituent_records(demo_env: None) -> None:
    client = TestClient(app)
    token = _issue_session(client)
    headers = {"X-Demo-Token": token}
    discrepancies = client.get("/v1/demo/discrepancies", headers=headers).json()[
        "discrepancies"
    ]
    target = next(
        d for d in discrepancies if len(d.get("contributing_records") or []) > 0
    )
    run_id = target["run_id"]

    trace = client.get(
        f"/v1/demo/runs/{run_id}/trace/{target['constituent_id']}",
        headers=headers,
    )
    assert trace.status_code == 200
    assert len(trace.json()["nodes"]) > 0

    missing = client.get(
        f"/v1/demo/runs/{run_id}/trace/does-not-exist", headers=headers
    )
    assert missing.status_code == 404


def test_short_demo_secret_is_rejected_as_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SETTLEIQ_DEMO_SECRET", "too-short")
    app_module._IP_REQUEST_TIMESTAMPS.clear()
    app_module._DEMO_SESSION_CREATION_TIMESTAMPS.clear()
    client = TestClient(app)
    res = client.post("/v1/demo/session")
    assert res.status_code == 503
    assert "demo secret" in res.json()["detail"].lower()


def test_demo_token_issued_in_the_future_is_rejected(demo_env: None) -> None:
    client = TestClient(app)
    future = _issue_test_token(iat_offset=3600.0)
    res = client.get("/v1/demo/runs", headers={"X-Demo-Token": future})
    assert res.status_code == 401


def test_api_responses_are_not_cacheable(demo_env: None) -> None:
    client = TestClient(app)
    token = _issue_session(client)
    res = client.get("/v1/demo/runs", headers={"X-Demo-Token": token})
    assert res.headers["Cache-Control"] == "no-store"
    session = client.post("/v1/demo/session")
    assert session.headers["Cache-Control"] == "no-store"

