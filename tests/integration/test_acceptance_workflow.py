"""End-to-End Acceptance Test Workflow for SettleIQ.

Exercises the complete 18-step lifecycle:
1.  Store migration and initialization.
2.  Frontend static mount and SPA routing.
3.  Source adapter normalization (Stripe format).
4.  Data validation and quarantine handling.
5.  Reconciliation execution via API.
6.  Metric computation and match rates.
7.  Discrepancy inspection (top-level and run-scoped).
8.  Investigation detail view.
9.  Discrepancy resolution workflow.
10. Resolution persistence verification.
11. Tamper-evident audit journal event recording.
12. Idempotent rerun verification.
13. Security: API key authentication enforcement (401).
14. Security: Sliding-window rate limiting (429).
15. Security: Payload size limits (413).
16. Security: Decimal enforcement / Float rejection (422).
17. Data persistence across database restarts.
18. Hash-chained audit journal tamper detection.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from settleiq.adapters.stripe import StripeSourceAdapter
from settleiq.api.app import app
from settleiq.fixtures.generator import generate
from settleiq.journal.chain import TamperType, open_journal
from settleiq.model.entities import DataProvenance
from settleiq.money import Money
from settleiq.persistence.store import Persistence, open_store
from settleiq.validation.ingest import validate_records


@pytest.fixture
def clean_db(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "acceptance_test.sqlite3"
    monkeypatch.setenv("SETTLEIQ_DB_PATH", str(db_file))
    store = open_store(db_file)
    journal = open_journal(db_file)
    yield store, journal, db_file


@pytest.fixture
def client(clean_db):
    return TestClient(app)


def test_complete_18_step_acceptance_workflow(clean_db, client, monkeypatch):
    store, journal, db_path = clean_db

    # -------------------------------------------------------------------------
    # STEP 1: Store migration & initialization
    # -------------------------------------------------------------------------
    assert store is not None
    assert journal is not None
    with store._connect() as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    assert "reconciliation_run" in tables
    assert "discrepancy" in tables
    assert "discrepancy_resolution" in tables
    assert "journal_entry" in tables

    # -------------------------------------------------------------------------
    # STEP 2: Dashboard static mount & SPA routing
    # -------------------------------------------------------------------------
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "<!DOCTYPE html>" in res_root.text or "<html" in res_root.text

    res_spa = client.get("/runs/test_run_123")
    assert res_spa.status_code == 200
    assert "<!DOCTYPE html>" in res_spa.text or "<html" in res_spa.text

    # -------------------------------------------------------------------------
    # STEP 3: StripeSourceAdapter normalization
    # -------------------------------------------------------------------------
    stripe_payload = [
        {
            "id": "ch_acc_1",
            "object": "charge",
            "amount": 20000,
            "currency": "usd",
            "created": 1776211200,
            "reference": "pi_acc_1",
            "customer": "cus_test",
            "fee_details": [
                {
                    "amount": 500,
                    "currency": "usd",
                    "type": "stripe_processing_fee",
                }
            ],
        },
        {
            "id": "re_acc_1",
            "object": "refund",
            "amount": 1000,
            "currency": "usd",
            "created": "2026-10-16T12:00:00Z",
            "charge": "ch_acc_1",
        },
        {
            "id": "po_acc_1",
            "object": "payout",
            "amount": 18500,
            "currency": "usd",
            "arrival_date": "2026-10-17T00:00:00Z",
            "batch_id": "po_batch_acc_1",
            "payout_reference": "ref_po_1",
        },
        {
            "id": "bd_acc_1",
            "object": "deposit",
            "amount": 18500,
            "currency": "usd",
            "posted": "2026-10-18T00:00:00Z",
            "narration": "STRIPE PAYOUT po_batch_acc_1",
        },
    ]
    adapter = StripeSourceAdapter()
    batch = adapter.normalize(
        json.dumps(stripe_payload).encode("utf-8"),
        provenance=DataProvenance.SYNTHETIC,
    )
    assert len(batch.charges) == 1
    assert batch.charges[0].amount == Money("200.00", "USD")
    assert len(batch.fees) == 1
    assert batch.fees[0].amount == Money("5.00", "USD")
    assert len(batch.refunds) == 1
    assert batch.refunds[0].amount == Money("10.00", "USD")
    assert len(batch.payouts) == 1
    assert batch.payouts[0].amount == Money("185.00", "USD")
    assert len(batch.deposits) == 1
    assert batch.deposits[0].amount == Money("185.00", "USD")
    assert batch.record_count() >= 5

    # -------------------------------------------------------------------------
    # STEP 4: Ingestion validation & quarantine handling
    # -------------------------------------------------------------------------
    raw_records = [
        (
            "charge",
            {
                "id": "c1",
                "amount": "100.00",
                "currency": "USD",
                "created": "2026-10-15",
                "batch": "b1",
            },
        ),
        (
            "fee",
            {
                "id": "f1",
                "amount": "2.50",
                "currency": "USD",
                "type": "interchange",
                "created": "2026-10-15",
                "batch": "b1",
            },
        ),
        (
            "payout",
            {
                "id": "p1",
                "amount": "97.50",
                "currency": "USD",
                "arrival_date": "2026-10-17",
                "batch": "b1",
            },
        ),
        (
            "deposit",
            {
                "id": "d1",
                "amount": "97.50",
                "currency": "USD",
                "posted": "2026-10-18",
                "narration": "STRIPE PAYOUT b1",
            },
        ),
        (
            "charge",
            {
                "id": "c_bad",
                "amount": "invalid-amt",
                "currency": "USD",
                "created": "2026-10-15",
            },
        ),
    ]
    validated = validate_records(raw_records)
    assert len(validated.accepted) == 4
    assert len(validated.quarantined) == 1
    assert "invalid" in str(validated.quarantined[0]).lower()

    # -------------------------------------------------------------------------
    # STEP 5: Reconciliation execution via API
    # -------------------------------------------------------------------------
    api_headers = {"X-API-Key": "test-key"}
    monkeypatch.setenv("SETTLEIQ_API_KEY", "test-key")

    dataset = generate()
    groups: dict[str, list[dict[str, object]]] = {}
    for kind, record in dataset.records:
        groups.setdefault(kind, []).append(record)

    run_payload = {
        "window_start": "2026-10-01",
        "window_end": "2026-10-31",
        "settlement_window_days": 3,
        "records": [{"kind": k, "records": recs} for k, recs in groups.items()],
    }
    run_resp = client.post("/v1/runs", json=run_payload, headers=api_headers)
    assert run_resp.status_code == 201
    run_data = run_resp.json()
    run_id = run_data["run_id"]
    assert len(run_id) == 64

    # -------------------------------------------------------------------------
    # STEP 6: Metrics & auto-match rate
    # -------------------------------------------------------------------------
    assert run_data["numerator"] == 19
    assert run_data["denominator"] == 25
    assert run_data["rate"] == 0.76

    # -------------------------------------------------------------------------
    # STEP 7: Discrepancy inspection (top-level and run-scoped)
    # -------------------------------------------------------------------------
    dsc_list_resp = client.get("/v1/discrepancies", headers=api_headers)
    assert dsc_list_resp.status_code == 200
    discrepancies = dsc_list_resp.json()["discrepancies"]
    assert len(discrepancies) == 7
    first_dsc = discrepancies[0]
    dsc_id = first_dsc["discrepancy_id"]

    run_dsc_resp = client.get(f"/v1/runs/{run_id}/discrepancies", headers=api_headers)
    assert run_dsc_resp.status_code == 200
    assert len(run_dsc_resp.json()["discrepancies"]) == 7

    # -------------------------------------------------------------------------
    # STEP 8: Investigation detail view
    # -------------------------------------------------------------------------
    dsc_detail_resp = client.get(f"/v1/discrepancies/{dsc_id}", headers=api_headers)
    assert dsc_detail_resp.status_code == 200
    detail = dsc_detail_resp.json()
    assert detail["discrepancy_id"] == dsc_id
    assert detail["status"] == "OPEN"

    # -------------------------------------------------------------------------
    # STEP 9: Discrepancy resolution workflow
    # -------------------------------------------------------------------------
    resolve_payload = {
        "reason": "Unidentified difference verified within tolerable threshold per SOP-42",
        "resolved_by": "audit_agent_01",
    }
    resolve_resp = client.post(
        f"/v1/discrepancies/{dsc_id}/resolve",
        json=resolve_payload,
        headers=api_headers,
    )
    assert resolve_resp.status_code == 200
    res_data = resolve_resp.json()
    assert res_data["status"] == "RESOLVED"
    assert res_data["appended"] is True

    # -------------------------------------------------------------------------
    # STEP 10: Verify resolution persisted in DB
    # -------------------------------------------------------------------------
    dsc_resolved = store.find_discrepancy(dsc_id)
    assert dsc_resolved is not None
    assert dsc_resolved["status"] == "RESOLVED"

    with store._connect() as conn:
        resolutions = conn.execute(
            "SELECT resolution_id, discrepancy_id, reason, resolved_by "
            "FROM discrepancy_resolution WHERE discrepancy_id = ?",
            (dsc_id,),
        ).fetchall()
    assert len(resolutions) == 1
    assert resolutions[0][2] == (
        "Unidentified difference verified within tolerable threshold per SOP-42"
    )
    assert resolutions[0][3] == "audit_agent_01"

    # -------------------------------------------------------------------------
    # STEP 11: Tamper-evident audit journal event recording
    # -------------------------------------------------------------------------
    with store._connect() as conn:
        journal_rows = conn.execute(
            "SELECT payload FROM journal_entry ORDER BY sequence"
        ).fetchall()
    payloads = [json.loads(r[0]) for r in journal_rows]
    assert any(p.get("kind") == "DiscrepancyResolved" for p in payloads)

    # -------------------------------------------------------------------------
    # STEP 12: Idempotent rerun verification
    # -------------------------------------------------------------------------
    replay_resp = client.post("/v1/runs", json=run_payload, headers=api_headers)
    assert replay_resp.status_code == 201
    assert replay_resp.headers.get("Idempotency-Replayed") == "true"
    replay_data = replay_resp.json()
    assert replay_data["replayed"] is True
    assert replay_data["run_id"] == run_id

    # -------------------------------------------------------------------------
    # STEP 13: Security: API key authentication enforcement
    # -------------------------------------------------------------------------
    unauth_resp = client.post("/v1/runs", json=run_payload, headers={"X-API-Key": "wrong-key"})
    assert unauth_resp.status_code == 401

    # -------------------------------------------------------------------------
    # STEP 14: Security: Sliding-window rate limiting
    # -------------------------------------------------------------------------
    monkeypatch.setattr("settleiq.api.app._MAX_REQUESTS_PER_WINDOW", 5)
    from settleiq.api.app import _IP_REQUEST_TIMESTAMPS
    _IP_REQUEST_TIMESTAMPS.clear()
    for _ in range(5):
        r = client.get("/health")
        assert r.status_code == 200
    limited_resp = client.get("/health")
    assert limited_resp.status_code == 429
    assert limited_resp.json()["error"] == "rate_limit_exceeded"
    # Restore rate limit
    monkeypatch.setattr("settleiq.api.app._MAX_REQUESTS_PER_WINDOW", 120)

    # -------------------------------------------------------------------------
    # STEP 15: Security: Payload size limits
    # -------------------------------------------------------------------------
    headers_large = dict(api_headers)
    headers_large["Content-Length"] = str(11 * 1024 * 1024)
    large_resp = client.post(
        "/v1/runs",
        json={"records": []},
        headers=headers_large,
    )
    assert large_resp.status_code == 413

    # -------------------------------------------------------------------------
    # STEP 16: Security: Decimal enforcement / Float rejection
    # -------------------------------------------------------------------------
    float_payload = {
        "window_start": "2026-10-01",
        "window_end": "2026-10-31",
        "records": [
            {
                "kind": "charge",
                "records": [
                    {
                        "id": "fl_1",
                        "amount": 100.50,  # JSON numeric float
                        "currency": "USD",
                    }
                ],
            }
        ],
    }
    float_resp = client.post("/v1/runs", json=float_payload, headers=api_headers)
    assert float_resp.status_code == 422

    # -------------------------------------------------------------------------
    # STEP 17: Persistence across database restart
    # -------------------------------------------------------------------------
    reopened_store = Persistence(str(db_path))
    reopened_runs = reopened_store.all_runs()
    assert len(reopened_runs) == 1
    assert reopened_store.find_discrepancy(dsc_id)["status"] == "RESOLVED"

    # -------------------------------------------------------------------------
    # STEP 18: Hash-chained audit journal tamper detection
    # -------------------------------------------------------------------------
    reopened_journal = open_journal(db_path)
    report = reopened_journal.verify()
    assert report.intact is True
    assert report.entries_verified >= 2

    # Tamper with an entry payload in the database
    with reopened_store._connect() as conn:
        conn.execute(
            "UPDATE journal_entry SET payload = '{\"tampered\": true}' WHERE sequence = 1"
        )
        conn.commit()

    tampered_report = reopened_journal.verify()
    assert tampered_report.intact is False
    assert len(tampered_report.findings) > 0
    assert tampered_report.findings[0][1] == TamperType.PAYLOAD_MODIFIED
