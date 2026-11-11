"""Test deployment-specific URL for corrected SettleIQ code at 4fe20b4."""
import urllib.request
import json
import sys

BASE = "https://settleiq-2m0sovwhp-naresh-cn2s-projects.vercel.app"
API_KEY = open('C:/Users/nares/Workspace/settleiq/.new_api_key').read().strip()
PASS = 0
FAIL = 0


def api(method, path, data=None):
    url = BASE + path
    req = urllib.request.Request(url, method=method)
    req.add_header("X-API-Key", API_KEY)
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


records = [
    {"kind": "charge", "records": [
        {"id": "chg-601", "amount": "100.00", "currency": "USD",
         "batch": "BATCH-601", "reference": "REF-601",
         "created": "2026-10-01", "narration": "Charge REF-601"},
    ]},
    {"kind": "fee", "records": [
        {"id": "fee-601", "amount": "10.00", "currency": "USD",
         "batch": "BATCH-601", "reference": "REF-601",
         "created": "2026-10-01", "narration": "Fee REF-601"},
    ]},
    {"kind": "charge", "records": [
        {"id": "chg-602", "amount": "200.00", "currency": "USD",
         "batch": "BATCH-601", "reference": "REF-602",
         "created": "2026-10-02", "narration": "Charge REF-602"},
    ]},
    {"kind": "fee", "records": [
        {"id": "fee-602", "amount": "20.00", "currency": "USD",
         "batch": "BATCH-601", "reference": "REF-602",
         "created": "2026-10-02", "narration": "Fee REF-602"},
    ]},
    {"kind": "charge", "records": [
        {"id": "chg-603", "amount": "300.00", "currency": "USD",
         "batch": "BATCH-602", "reference": "REF-603",
         "created": "2026-10-03", "narration": "Charge REF-603"},
    ]},
    {"kind": "fee", "records": [
        {"id": "fee-603", "amount": "30.00", "currency": "USD",
         "batch": "BATCH-602", "reference": "REF-603",
         "created": "2026-10-03", "narration": "Fee REF-603"},
    ]},
    {"kind": "payout", "records": [
        {"id": "pay-601", "amount": "90.00", "currency": "USD",
         "batch": "BATCH-601", "reference": "REF-601",
         "created": "2026-10-05", "narration": "Payout REF-601"},
    ]},
    {"kind": "payout", "records": [
        {"id": "pay-602", "amount": "150.00", "currency": "USD",
         "batch": "BATCH-601", "reference": "REF-602",
         "created": "2026-10-06", "narration": "Payout REF-602 (short paid)"},
    ]},
]

print("=== DEPLOYMENT-SPECIFIC VERIFICATION: COMMIT 4fe20b4 ===")
print(f"URL: {BASE}")

status, body = api("POST", "/v1/runs", {
    "records": records,
    "window_start": "2026-10-01",
    "window_end": "2026-10-31",
    "settlement_window_days": 3,
})
check("Create run: 201", status == 201, f"got {status} {body}")
check("Run not replayed", body.get("replayed") == False, f"got {body.get('replayed')}")
run_id = body["run_id"]
print(f"  Run ID: {run_id}")

status, metrics = api("GET", f"/v1/runs/{run_id}/metrics")
check("Metrics: 200", status == 200, f"got {status}")
if status == 200:
    print(f"  Metrics: numerator={metrics.get('numerator')}, denominator={metrics.get('denominator')}, rate={metrics.get('rate')}")
    check("Denominator is 8", metrics.get("denominator") == 8, f"got {metrics.get('denominator')}")
    check("Numerator is 2", metrics.get("numerator") == 2, f"got {metrics.get('numerator')}")
    check("Rate is 0.25", metrics.get("rate") == 0.25, f"got {metrics.get('rate')}")

status, disc_body = api("GET", f"/v1/runs/{run_id}/discrepancies")
check("Discrepancies: 200", status == 200)
check("Has at least 3 discrepancies", disc_body.get("count", 0) >= 3, f"got {disc_body.get('count')}")

for d in disc_body.get("discrepancies", []):
    print(f"  {d['discrepancy_id']}: type={d['type']} constituent={d['constituent_kind']}:{d['constituent_id']} severity={d['severity']}")
    print(f"    reason: {d['reason'][:100]}")

pay001_breaks = [d for d in disc_body.get("discrepancies", []) if d["discrepancy_id"] == "dsc:NET_GROSS_BREAK:pay-601"]
check("REF-601: no NET_GROSS_BREAK for pay-601 (closes exactly)", len(pay001_breaks) == 0, f"got {len(pay001_breaks)}")

pay002_breaks = [d for d in disc_body.get("discrepancies", []) if d["discrepancy_id"] == "dsc:NET_GROSS_BREAK:pay-602"]
check("REF-602: NET_GROSS_BREAK for pay-602", len(pay002_breaks) == 1, f"got {len(pay002_breaks)}")
if pay002_breaks:
    check("REF-602: reason mentions residual 30.00", "30.00" in pay002_breaks[0]["reason"], f"got: {pay002_breaks[0]['reason']}")
    check("REF-602: severity HIGH", pay002_breaks[0]["severity"] == "HIGH", f"got {pay002_breaks[0]['severity']}")

phantom_chg = [d for d in disc_body.get("discrepancies", []) if d["discrepancy_id"] == "dsc:PHANTOM_PROCESSOR:chg-603"]
check("REF-603: PHANTOM_PROCESSOR for chg-603", len(phantom_chg) == 1, f"got {len(phantom_chg)}")

phantom_fee = [d for d in disc_body.get("discrepancies", []) if d["discrepancy_id"] == "dsc:PHANTOM_PROCESSOR:fee-603"]
check("REF-603: PHANTOM_PROCESSOR for fee-603", len(phantom_fee) == 1, f"got {len(phantom_fee)}")

if phantom_chg:
    check("REF-603: chg-603 reason mentions BATCH-602", "BATCH-602" in phantom_chg[0]["reason"], f"got: {phantom_chg[0]['reason']}")
    check("REF-603: chg-603 severity HIGH", phantom_chg[0]["severity"] == "HIGH", f"got {phantom_chg[0]['severity']}")

input_ids = {"chg-601", "fee-601", "chg-602", "fee-602", "chg-603", "fee-603", "pay-601", "pay-602"}
for d in disc_body.get("discrepancies", []):
    check(f"Discrepancy {d['discrepancy_id']} maps to valid source record", d["constituent_id"] in input_ids, f"constituent_id={d['constituent_id']} not in {input_ids}")

status, body = api("GET", "/health")
check("Health endpoint: 200", status == 200, f"got {status}")

# Test unauthorized access is rejected
status, body = api("GET", "/v1/runs", key="wrong-key")
check("Unauthorized access rejected: 401", status == 401, f"got {status}")

print(f"\n=== RESULTS: {PASS} passed, {FAIL} failed ===")
sys.exit(0 if FAIL == 0 else 1)