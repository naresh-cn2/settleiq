"""End-to-End Demonstration Journey Verification Script.

Executes the complete 8-step forensic reconciliation workflow:
1. Seed realistic synthetic ledger data (POST /v1/demo/seed)
2. Retrieve and inspect run metrics (GET /v1/runs/{id}/metrics)
3. Query and inspect discrepancy queue (GET /v1/runs/{id}/discrepancies)
4. Invoke Autonomous AI Forensic Investigator (GET /v1/discrepancies/{id}/investigate)
5. Reconstruct visual fund journey trace (GET /v1/runs/{id}/trace/{cid})
6. Authorize and commit draft resolution (POST /v1/discrepancies/{id}/resolve)
7. Confirm persistent database state mutation to RESOLVED
8. Cryptographically verify hash-chained audit journal integrity (POST /v1/journal/verify)

Saves the complete verified execution audit trail into `proof/demo_journey_trace.json`.
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from settleiq.api.app import app  # noqa: E402


def verify_demo_journey() -> dict[str, object]:
    client = TestClient(app)
    trace_events: list[dict[str, object]] = []

    def record_step(step_num: int, title: str, path: str, status: int, data: object) -> None:
        event = {
            "step": step_num,
            "title": title,
            "path": path,
            "http_status": status,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "data_summary": data,
        }
        trace_events.append(event)
        print(f"Step {step_num}: {title} [{status}]")

    print("================================================================================")
    print("EXECUTING SETTLEIQ 8-STEP END-TO-END DEMO WORKFLOW")
    print("================================================================================")

    # Step 1: Seed Demo Run
    res1 = client.post("/v1/demo/seed")
    assert res1.status_code == 201, f"Seed failed: {res1.text}"
    seed_data = res1.json()
    run_id = seed_data["run_id"]
    record_step(
        1, "Seed Enterprise Synthetic Ledger", "/v1/demo/seed", res1.status_code, seed_data
    )

    # Step 2: Query Run Metrics
    res2 = client.get(f"/v1/runs/{run_id}/metrics")
    assert res2.status_code == 200, f"Metrics query failed: {res2.text}"
    metrics_data = res2.json()
    record_step(
        2,
        "Inspect Calculated Reconciliation Metrics",
        f"/v1/runs/{run_id}/metrics",
        res2.status_code,
        metrics_data,
    )

    # Step 3: List Discrepancies
    res3 = client.get(f"/v1/runs/{run_id}/discrepancies")
    assert res3.status_code == 200, f"Discrepancies query failed: {res3.text}"
    disc_data = res3.json()
    discs = disc_data["discrepancies"]
    assert len(discs) > 0, "No discrepancies found in seeded run"
    record_step(
        3,
        "Query Run Discrepancy Queue",
        f"/v1/runs/{run_id}/discrepancies",
        res3.status_code,
        {
            "count": len(discs),
            "types": [d["type"] for d in discs],
        },
    )

    # Pick first discrepancy for deep investigation
    target_disc = discs[0]
    disc_id = target_disc["discrepancy_id"]
    cid = target_disc["constituent_id"]

    # Step 4: AI Forensic Investigation
    res4 = client.get(f"/v1/discrepancies/{disc_id}/investigate")
    assert res4.status_code == 200, f"Investigation failed: {res4.text}"
    inv_data = res4.json()
    top_title = (
        inv_data["hypotheses"][0]["title"] if inv_data.get("hypotheses") else None
    )
    top_conf = (
        inv_data["hypotheses"][0]["confidence"] if inv_data.get("hypotheses") else None
    )
    record_step(
        4,
        "Invoke Autonomous AI Forensic Investigator",
        f"/v1/discrepancies/{disc_id}/investigate",
        res4.status_code,
        {
            "discrepancy_id": disc_id,
            "type": inv_data["type"],
            "hypotheses_count": len(inv_data["hypotheses"]),
            "top_hypothesis": top_title,
            "confidence": top_conf,
            "recommended_action": inv_data["recommended_action"],
        },
    )

    # Step 5: Visual Transaction Trace
    res5 = client.get(f"/v1/runs/{run_id}/trace/{cid}")
    assert res5.status_code == 200, f"Trace failed: {res5.text}"
    trace_data = res5.json()
    record_step(
        5,
        "Reconstruct Visual Fund Journey Trace",
        f"/v1/runs/{run_id}/trace/{cid}",
        res5.status_code,
        {
            "nodes_count": len(trace_data.get("nodes", [])),
            "gross": trace_data.get("gross_amount"),
            "fees": trace_data.get("fee_amount"),
            "net_expected": trace_data.get("net_expected"),
            "net_paid": trace_data.get("net_paid"),
            "residual": trace_data.get("residual"),
            "is_closed": trace_data.get("is_closed"),
        },
    )

    # Step 6: Commit Resolution
    resolve_payload = {
        "reason": inv_data["draft_resolution"]["reason"],
        "resolved_by": "demo_lead_auditor",
    }
    if target_disc.get("type") == "AMBIGUOUS_MATCH":
        resolve_payload["selected_candidate"] = "cand_tie_breaker"

    res6 = client.post(f"/v1/discrepancies/{disc_id}/resolve", json=resolve_payload)
    assert res6.status_code == 200, f"Resolution failed: {res6.text}"
    record_step(
        6,
        "Authorize and Commit Resolution",
        f"/v1/discrepancies/{disc_id}/resolve",
        res6.status_code,
        res6.json(),
    )

    # Step 7: Verify Persisted Discrepancy State
    res7 = client.get(f"/v1/discrepancies/{disc_id}")
    assert res7.status_code == 200
    persisted_disc = res7.json()
    assert persisted_disc["status"] == "RESOLVED"
    record_step(
        7,
        "Confirm Persistent Database State (RESOLVED)",
        f"/v1/discrepancies/{disc_id}",
        res7.status_code,
        {
            "status": persisted_disc["status"],
            "resolution_history_count": len(
                persisted_disc.get("resolution_history", [])
            ),
        },
    )

    # Step 8: Cryptographic Audit Journal Verification
    res8 = client.post("/v1/journal/verify")
    assert res8.status_code == 200
    journal_data = res8.json()
    assert journal_data["intact"] is True
    record_step(
        8,
        "Cryptographically Verify Hash-Chained Audit Journal",
        "/v1/journal/verify",
        res8.status_code,
        journal_data,
    )

    output = {
        "verified_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "workflow_status": "SUCCESS",
        "total_steps": len(trace_events),
        "steps": trace_events,
    }

    out_file = root / "proof" / "demo_journey_trace.json"
    out_file.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print("================================================================================")
    print(f"DEMO WORKFLOW VERIFIED: Saved execution trace to {out_file}")
    print("================================================================================")
    return output


if __name__ == "__main__":
    verify_demo_journey()
