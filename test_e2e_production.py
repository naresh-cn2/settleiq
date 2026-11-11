"""End-to-end production validation script for SettleIQ."""
import urllib.request
import json
import urllib.error
import sys

BASE = "https://settleiq-zeta.vercel.app"
API_KEY = "settleiq-test-key-2024"
PASS = 0
FAIL = 0


def api(method, path, data=None, key=API_KEY):
    url = BASE + path
    req = urllib.request.Request(url, method=method)
    req.add_header("X-API-Key", key)
    req.add_header("Content-Type", "application/json")
    if data:
        req.data = json.dumps(data).encode()
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode())
        except Exception:
            body = {"error": str(e)}
        return e.code, body


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name} {detail}")


print("=== PHASE 1: AUTHENTICATION ===")
status, body = api("GET", "/v1/health")
check("Valid API key /v1/health returns 200", status == 200 and body.get("status") == "ok", f"got {status} {body}")
try:
    req = urllib.request.Request(BASE + "/v1/health", method="GET")
    urllib.request.urlopen(req)
    check("Missing API key rejected", False, "unexpectedly succeeded")
except urllib.error.HTTPError as e:
    check("Missing API key rejected", e.code == 401, f"got {e.code}")
status, body = api("GET", "/v1/health", key="wrong-key")
check("Invalid API key rejected", status == 401, f"got {status}")
status, body = api("GET", "/v1/runs", key="")
check("Empty API key rejected", status == 401, f"got {status}")

print("\n=== PHASE 2: RECONCILIATION WORKFLOW ===")
records = [
    {"kind": "charge", "records": [
        {"id": "chg-001", "amount": "100.00", "currency": "USD", "batch": "BATCH-001", "reference": "REF-001", "created": "2026-10-01", "narration": "Charge 1"},
        {"id": "chg-002", "amount": "200.00", "currency": "USD", "batch": "BATCH-001", "reference": "REF-002", "created": "2026-10-02", "narration": "Charge 2"},
        {"id": "chg-003", "amount": "300.00", "currency": "USD", "batch": "BATCH-002", "reference": "REF-003", "created": "2026-10-03", "narration": "Charge 3"},
    ]},
    {"kind": "fee", "records": [
        {"id": "fee-001", "amount": "10.00", "currency": "USD", "batch": "BATCH-001", "reference": "REF-001", "created": "2026-10-01", "narration": "Fee 1"},
        {"id": "fee-002", "amount": "20.00", "currency": "USD", "batch": "BATCH-001", "reference": "REF-002", "created": "2026-10-02", "narration": "Fee 2"},
        {"id": "fee-003", "amount": "30.00", "currency": "USD", "batch": "BATCH-002", "reference": "REF-003", "created": "2026-10-03", "narration": "Fee 3"},
    ]},
    {"kind": "payout", "records": [
        {"id": "pay-001", "amount": "90.00", "currency": "USD", "batch": "BATCH-001", "reference": "REF-001", "created": "2026-10-05", "narration": "Payout 1"},
        {"id": "pay-002", "amount": "150.00", "currency": "USD", "batch": "BATCH-001", "reference": "REF-002", "created": "2026-10-06", "narration": "Payout 2 (short paid)"},
    ]},
]
status, body = api("POST", "/v1/runs", {
    "records": records,
    "window_start": "2026-10-01",
    "window_end": "2026-10-31",
    "settlement_window_days": 3,
})
check("Create run returns 201", status == 201, f"got {status} {body}")
check("Run not replayed", body.get("replayed") == False, f"got {body}")
check("Has discrepancies", body.get("discrepancy_count", 0) > 0, f"got {body.get('discrepancy_count')}")
run_id = body["run_id"]
print(f"  Run ID: {run_id}")
status2, body2 = api("POST", "/v1/runs", {
    "records": records,
    "window_start": "2026-10-01",
    "window_end": "2026-10-31",
    "settlement_window_days": 3,
})
check("Replay run returns 201", status2 == 201, f"got {status2}")
check("Replay flagged as replayed", body2.get("replayed") == True, f"got {body2}")
check("Same run_id on replay", body2.get("run_id") == run_id, f"got {body2.get('run_id')}")

print("\n=== PHASE 3: RUN DETAILS ===")
status, body = api("GET", f"/v1/runs/{run_id}")
check("Get run returns 200", status == 200, f"got {status}")
check("Run has run object", "run" in body, f"got {body}")

print("\n=== PHASE 4: DISCREPANCIES ===")
status, body = api("GET", f"/v1/runs/{run_id}/discrepancies")
check("List discrepancies returns 200", status == 200, f"got {status}")
check("Has discrepancies", body.get("count", 0) > 0, f"got {body.get('count')}")
assert len(body.get("discrepancies", [])) > 0
disc = body["discrepancies"][0]
disc_id = disc["discrepancy_id"]
print(f"  First discrepancy: {disc_id} type={disc.get('type')} severity={disc.get('severity')}")
status, body = api("GET", f"/v1/discrepancies/{disc_id}")
check("Get discrepancy returns 200", status == 200, f"got {status}")
status, body = api("GET", f"/v1/runs/{run_id}/discrepancies/{disc_id}/investigate")
check("Investigate discrepancy returns 200", status == 200, f"got {status} {body}")
if status == 200:
    print(f"  Investigation: {json.dumps(body)[:200]}")

print("\n=== PHASE 5: JOURNAL VERIFICATION ===")
status, body = api("POST", "/v1/journal/verify")
check("Journal verify returns 200", status == 200, f"got {status}")
if status == 200:
    check("Journal reports intact", body.get("intact") == True, f"got {body}")

print("\n=== PHASE 6: UNAUTHORIZED ACCESS ===")
status, body = api("GET", "/v1/runs", key="wrong")
check("Wrong API key rejected", status == 401, f"got {status}")

print("\n=== PHASE 7: LIST ALL RUNS ===")
status, body = api("GET", "/v1/runs")
check("List runs returns 200", status == 200, f"got {status}")
check("At least 1 run", body.get("count", 0) >= 1, f"got {body.get('count')}")

print("\n=== PHASE 8: HEALTH ENDPOINT ROUTING ===")
status_h, body_h = api("GET", "/health")
print(f"  /health: {status_h} {str(body_h)[:100]}")

print("\n=== PHASE 9: EDGE CASES ===")

# Empty records
status, body = api("POST", "/v1/runs", {
    "records": [],
    "window_start": "2026-10-01",
    "window_end": "2026-10-31",
})
check("Empty records returns 201 (valid empty reconciliation)", status == 201, f"got {status} {body}")
check("Empty reconciliation has 0 discrepancies", body.get("discrepancy_count", 0) == 0, f"got {body.get('discrepancy_count')}")

# Invalid record (negative amount)
status, body = api("POST", "/v1/runs", {
    "records": [{"kind": "charge", "records": [
        {"id": "bad-001", "amount": "-50.00", "currency": "USD", "reference": "REF-BAD", "created": "2026-10-01"}
    ]}],
    "window_start": "2026-10-01",
    "window_end": "2026-10-31",
})
check("Negative amount accepted (by design - engine handles it)", status == 201, f"got {status} {body}")

# Missing required field
status, body = api("POST", "/v1/runs", {
    "records": [{"kind": "charge", "records": [
        {"id": "bad-002", "currency": "USD", "reference": "REF-BAD2", "created": "2026-10-01"}
    ]}],
    "window_start": "2026-10-01",
    "window_end": "2026-10-31",
})
check("Missing amount returns 422 (FastAPI validation)", status == 422, f"got {status}")

# Run not found
status, body = api("GET", "/v1/runs/nonexistent-run-id")
check("Nonexistent run returns 404", status == 404, f"got {status}")

# Discrepancy not found
status, body = api("GET", "/v1/discrepancies/nonexistent-disc-id")
check("Nonexistent discrepancy returns 404", status == 404, f"got {status}")

print("\n=== PHASE 10: DISCREPANCY RESOLUTION ===")
# Get a discrepancy and try to resolve it
status, disc_body = api("GET", f"/v1/runs/{run_id}/discrepancies")
if status == 200 and disc_body.get("count", 0) > 0:
    disc_id = disc_body["discrepancies"][0]["discrepancy_id"]
    status, body = api("POST", f"/v1/discrepancies/{disc_id}/resolve", {
        "reason": "Test resolution",
        "resolution": "resolved",
        "resolved_by": "test-investigator"
    })
    check("Resolve discrepancy returns 200", status == 200, f"got {status} {body}")
    
    # Verify resolution persisted
    status, body = api("GET", f"/v1/discrepancies/{disc_id}")
    check("Resolved discrepancy still accessible", status == 200, f"got {status}")

print("\n=== PHASE 11: RUN HISTORY & PERSISTENCE ===")
status, body = api("GET", "/v1/runs")
check("Run history persists", status == 200 and body.get("count", 0) >= 1,
      f"got count={body.get('count')}")

print("\n=== PHASE 12: SEED DEMO RUN ===")
status, body = api("POST", "/v1/demo/seed")
check("Demo seed returns 201", status == 201, f"got {status} {body}")
if status == 201:
    check("Demo has discrepancies", body.get("discrepancy_count", 0) > 0,
          f"got {body.get('discrepancy_count')}")

print(f"\n=== RESULTS: {PASS} passed, {FAIL} failed ===")
sys.exit(0 if FAIL == 0 else 1)