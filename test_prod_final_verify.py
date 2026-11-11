"""Final production verification of corrected SettleIQ deployment."""
import urllib.request
import json
import sys

BASE = "https://settleiq-zeta.vercel.app"
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
        {"id": "chg-501", "amount": "100.00", "currency": "USD",
         "batch": "BATCH-501", "reference": "REF-501",
         "created": "2026-10-01", "narration": "Charge REF-501"},
    ]},
    {"kind": "fee", "records": [
        {"id": "fee-501", "amount": "10.00", "currency": "USD",
         "batch": "BATCH-501", "reference": "REF-501",
         "created": "2026-10-01", "narration": "Fee REF-501"},
    ]},
    {"kind": "charge", "records": [
        {"id": "chg-502", "amount": "200.00", "currency": "USD",
         "batch": "BATCH-501", "reference": "REF-502",
         "created": "2026-10-02", "narration": "Charge REF-502"},
    ]},
    {"kind": "fee", "records": [
        {"id": "fee-502", "amount": "20.00", "currency": "USD",
         "batch": "BATCH-501", "reference": "REF-502",
         "created": "2026-10-02", "narration": "Fee REF-502"},
    ]},
    {"kind": "charge", "records": [
        {"id": "chg-503", "amount": "300.00", "currency": "USD",
         "batch": "BATCH-502", "reference": "REF-503",
         "created": "2026-10-03", "narration": "Charge REF-503"},
    ]},
    {"kind": "fee", "records": [
        {"id": "fee-503", "amount": "30.00", "currency": "USD",
         "batch": "BATCH-502", "reference": "REF-503",
         "created": "2026-10-03", "narration": "Fee REF-503"},
    ]},
    {"kind": "payout", "records": [
        {"id": "pay-501", "amount": "90.00", "currency": "USD",
         "batch": "BATCH-501", "reference": "REF-501",
         "created": "2026-10-05", "narration": "Payout REF-501"},
    ]},
    {"kind": "payout", "records": [
        {"id": "pay-502", "amount": "150.00", "currency": "USD",
         "batch": "BATCH-501", "reference": "REF-502",
         "created": "2026-10-06", "narration": "Payout REF-502 (short paid)"},
    ]},
]

print("=== PRODUCTION VERIFICATION OF CORRECTED SETTLEIQ ===")
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

pay001_breaks = [d for d in disc_body.get("discrepancies", []) if d["discrepancy_id"] == "dsc:NET_GROSS_BREAK:pay-501"]
check("REF-501: no NET_GROSS_BREAK for pay-501 (closes exactly)", len(pay001_breaks) == 0, f"got {len(pay001_breaks)}")

pay002_breaks = [d for d in disc_body.get("discrepancies", []) if d["discrepancy_id"] == "dsc:NET_GROSS_BREAK:pay-502"]
check("REF-502: NET_GROSS_BREAK for pay-502", len(pay002_breaks) == 1, f"got {len(pay002_breaks)}")
if pay002_breaks:
    check("REF-502: reason mentions residual 30.00", "30.00" in pay002_breaks[0]["reason"], f"got: {pay002_breaks[0]['reason']}")
    check("REF-502: severity HIGH", pay002_breaks[0]["severity"] == "HIGH", f"got {pay002_breaks[0]['severity']}")

phantom_chg = [d for d in disc_body.get("discrepancies", []) if d["discrepancy_id"] == "dsc:PHANTOM_PROCESSOR:chg-503"]
check("REF-503: PHANTOM_PROCESSOR for chg-503", len(phantom_chg) == 1, f"got {len(phantom_chg)}")

phantom_fee = [d for d in disc_body.get("discrepancies", []) if d["discrepancy_id"] == "dsc:PHANTOM_PROCESSOR:fee-503"]
check("REF-503: PHANTOM_PROCESSOR for fee-503", len(phantom_fee) == 1, f"got {len(phantom_fee)}")

if phantom_chg:
    check("REF-503: chg-503 reason mentions BATCH-502", "BATCH-502" in phantom_chg[0]["reason"], f"got: {phantom_chg[0]['reason']}")
    check("REF-503: chg-503 severity HIGH", phantom_chg[0]["severity"] == "HIGH", f"got {phantom_chg[0]['severity']}")

input_ids = {"chg-501", "fee-501", "chg-502", "fee-502", "chg-503", "fee-503", "pay-501", "pay-502"}
for d in disc_body.get("discrepancies", []):
    check(f"Discrepancy {d['discrepancy_id']} maps to valid source record", d["constituent_id"] in input_ids, f"constituent_id={d['constituent_id']} not in {input_ids}")

status, body = api("GET", "/health")
check("Health endpoint: 200", status == 200, f"got {status}")

# Test unauthorized access is rejected
status, body = api("GET", "/v1/runs", key="wrong-key")
check("Unauthorized access rejected: 401", status == 401, f"got {status}")

print(f"\n=== RESULTS: {PASS} passed, {FAIL} failed ===")
sys.exit(0 if FAIL == 0 else 1)