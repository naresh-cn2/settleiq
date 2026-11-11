"""Complete end-to-end workflow test on production."""
import urllib.request
import json
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


print("=== COMPLETE WORKFLOW TEST ===")

# 1. Authentication
status, body = api("GET", "/v1/health")
check("Auth: valid key works", status == 200, f"got {status}")

# 2. Create reconciliation run with synthetic data
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
check("Create run: 201", status == 201, f"got {status}")
check("Create run: not replayed", body.get("replayed") == False)
check("Create run: has discrepancies", body.get("discrepancy_count", 0) > 0)
run_id = body["run_id"]
print(f"  Run ID: {run_id}")

# 3. Get run details
status, body = api("GET", f"/v1/runs/{run_id}")
check("Get run: 200", status == 200)
check("Get run: has run object", "run" in body)

# 4. List discrepancies
status, disc_body = api("GET", f"/v1/runs/{run_id}/discrepancies")
check("List discrepancies: 200", status == 200)
check("List discrepancies: has items", disc_body.get("count", 0) > 0)
disc_id = disc_body["discrepancies"][0]["discrepancy_id"]
print(f"  Discrepancy: {disc_id}")

# 5. Get discrepancy detail
status, body = api("GET", f"/v1/discrepancies/{disc_id}")
check("Get discrepancy: 200", status == 200)

# 6. Investigate discrepancy
status, inv = api("GET", f"/v1/runs/{run_id}/discrepancies/{disc_id}/investigate")
check("Investigate: 200", status == 200, f"got {status}")
if status == 200:
    check("Investigation has trace", "trace" in inv)
    check("Investigation has hypotheses", "hypotheses" in inv and len(inv.get("hypotheses", [])) > 0)
    check("Investigation has recommended_action", "recommended_action" in inv)
    for h in inv.get("hypotheses", []):
        check(f"Hypothesis has confidence", "confidence" in h)
        check(f"Hypothesis has description", len(h.get("description", "")) > 0)

# 7. Journal verification
status, body = api("POST", "/v1/journal/verify")
check("Journal verify: 200", status == 200)
if status == 200:
    check("Journal intact", body.get("intact") == True, f"got {body}")

# 8. Run metrics
status, body = api("GET", f"/v1/runs/{run_id}/metrics")
check("Run metrics: 200", status == 200, f"got {status}")
if status == 200:
    check("Metrics has rate", "rate" in body)

# 9. Export run
status, body = api("GET", f"/v1/runs/{run_id}/export")
check("Export run: 200", status == 200, f"got {status}")
if status == 200:
    check("Export has run data", "run" in body)
    check("Export has discrepancies", "discrepancies" in body)

# 10. Resolve discrepancy
status, body = api("POST", f"/v1/discrepancies/{disc_id}/resolve", {
    "reason": "Test resolution - short payout confirmed",
    "resolution": "resolved",
    "resolved_by": "test-investigator"
})
check("Resolve discrepancy: 200", status == 200, f"got {status} {body}")

# 11. Verify resolution persisted
status, body = api("GET", f"/v1/discrepancies/{disc_id}")
check("Resolved discrepancy accessible: 200", status == 200)

# 12. List all runs
status, body = api("GET", "/v1/runs")
check("List runs: 200", status == 200)
check("List runs: at least 1", body.get("count", 0) >= 1)

# 13. Unauthorized access rejected
status, body = api("GET", "/v1/runs", key="wrong")
check("Unauthorized rejected: 401", status == 401)

# 14. Health endpoint
status, body = api("GET", "/health")
check("Health endpoint: 200", status == 200, f"got {status}")

print(f"\n=== RESULTS: {PASS} passed, {FAIL} failed ===")
sys.exit(0 if FAIL == 0 else 1)