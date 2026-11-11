"""Test production via vercel curl to bypass edge cache."""
import subprocess
import json
import sys

BASE = "https://settleiq-zeta.vercel.app"
API_KEY = "settleiq-test-key-2024"
PASS = 0
FAIL = 0


def vercel_curl(method, path, data=None):
    cmd = ["npx", "vercel", "curl", BASE + path, "-X", method, "-H", f"X-API-Key: {API_KEY}", "-H", "Content-Type: application/json"]
    if data:
        cmd.extend(["-d", json.dumps(data)])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        return None, f"Command failed: {result.stderr}"
    try:
        # vercel curl output includes curl progress info, need to find JSON
        output = result.stdout
        # Find the JSON part (after curl progress)
        lines = output.strip().split("\n")
        json_line = None
        for line in reversed(lines):
            line = line.strip()
            if line.startswith("{"):
                json_line = line
                break
        if json_line:
            return json.loads(json_line), None
        return None, f"No JSON found in output: {output[:200]}"
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}, output: {output[:200]}"


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
        {"id": "chg-301", "amount": "100.00", "currency": "USD",
         "batch": "BATCH-301", "reference": "REF-301",
         "created": "2026-10-01", "narration": "Charge REF-301"},
    ]},
    {"kind": "fee", "records": [
        {"id": "fee-301", "amount": "10.00", "currency": "USD",
         "batch": "BATCH-301", "reference": "REF-301",
         "created": "2026-10-01", "narration": "Fee REF-301"},
    ]},
    {"kind": "charge", "records": [
        {"id": "chg-302", "amount": "200.00", "currency": "USD",
         "batch": "BATCH-301", "reference": "REF-302",
         "created": "2026-10-02", "narration": "Charge REF-302"},
    ]},
    {"kind": "fee", "records": [
        {"id": "fee-302", "amount": "20.00", "currency": "USD",
         "batch": "BATCH-301", "reference": "REF-302",
         "created": "2026-10-02", "narration": "Fee REF-302"},
    ]},
    {"kind": "charge", "records": [
        {"id": "chg-303", "amount": "300.00", "currency": "USD",
         "batch": "BATCH-302", "reference": "REF-303",
         "created": "2026-10-03", "narration": "Charge REF-303"},
    ]},
    {"kind": "fee", "records": [
        {"id": "fee-303", "amount": "30.00", "currency": "USD",
         "batch": "BATCH-302", "reference": "REF-303",
         "created": "2026-10-03", "narration": "Fee REF-303"},
    ]},
    {"kind": "payout", "records": [
        {"id": "pay-301", "amount": "90.00", "currency": "USD",
         "batch": "BATCH-301", "reference": "REF-301",
         "created": "2026-10-05", "narration": "Payout REF-301"},
    ]},
    {"kind": "payout", "records": [
        {"id": "pay-302", "amount": "150.00", "currency": "USD",
         "batch": "BATCH-301", "reference": "REF-302",
         "created": "2026-10-06", "narration": "Payout REF-302 (short paid)"},
    ]},
]

print("=== PRODUCTION VERIFICATION VIA VERCEL CURL ===")
print(f"URL: {BASE}")

status, body = vercel_curl("POST", "/v1/runs", {
    "records": records,
    "window_start": "2026-10-01",
    "window_end": "2026-10-31",
    "settlement_window_days": 3,
})
if body is None:
    print(f"  Create run FAILED: {status}")
    sys.exit(1)
check("Create run: 201", status == 201, f"got {status} {body}")
check("Run not replayed", body.get("replayed") == False, f"got {body.get('replayed')}")
run_id = body["run_id"]
print(f"  Run ID: {run_id}")

status, metrics = vercel_curl("GET", f"/v1/runs/{run_id}/metrics")
check("Metrics: 200", status == 200, f"got {status}")
if status == 200:
    print(f"  Metrics: numerator={metrics.get('numerator')}, denominator={metrics.get('denominator')}, rate={metrics.get('rate')}")
    check("Denominator is 8", metrics.get("denominator") == 8, f"got {metrics.get('denominator')}")
    check("Numerator is 2", metrics.get("numerator") == 2, f"got {metrics.get('numerator')}")
    check("Rate is 0.25", metrics.get("rate") == 0.25, f"got {metrics.get('rate')}")

status, disc_body = vercel_curl("GET", f"/v1/runs/{run_id}/discrepancies")
check("Discrepancies: 200", status == 200, f"got {status}")
check("Has at least 3 discrepancies", disc_body.get("count", 0) >= 3, f"got {disc_body.get('count')}")

for d in disc_body.get("discrepancies", []):
    print(f"  {d['discrepancy_id']}: type={d['type']} constituent={d['constituent_kind']}:{d['constituent_id']} severity={d['severity']}")
    print(f"    reason: {d['reason'][:100]}")

pay001_breaks = [d for d in disc_body.get("discrepancies", []) if d["discrepancy_id"] == "dsc:NET_GROSS_BREAK:pay-301"]
check("REF-301: no NET_GROSS_BREAK for pay-301 (closes exactly)", len(pay001_breaks) == 0, f"got {len(pay001_breaks)}")

pay002_breaks = [d for d in disc_body.get("discrepancies", []) if d["discrepancy_id"] == "dsc:NET_GROSS_BREAK:pay-302"]
check("REF-302: NET_GROSS_BREAK for pay-302", len(pay002_breaks) == 1, f"got {len(pay002_breaks)}")
if pay002_breaks:
    check("REF-302: reason mentions residual 30.00", "30.00" in pay002_breaks[0]["reason"], f"got: {pay002_breaks[0]['reason']}")
    check("REF-302: severity HIGH", pay002_breaks[0]["severity"] == "HIGH", f"got {pay002_breaks[0]['severity']}")

phantom_chg = [d for d in disc_body.get("discrepancies", []) if d["discrepancy_id"] == "dsc:PHANTOM_PROCESSOR:chg-303"]
check("REF-303: PHANTOM_PROCESSOR for chg-303", len(phantom_chg) == 1, f"got {len(phantom_chg)}")

phantom_fee = [d for d in disc_body.get("discrepancies", []) if d["discrepancy_id"] == "dsc:PHANTOM_PROCESSOR:fee-303"]
check("REF-303: PHANTOM_PROCESSOR for fee-303", len(phantom_fee) == 1, f"got {len(phantom_fee)}")

if phantom_chg:
    check("REF-303: chg-303 reason mentions BATCH-302", "BATCH-302" in phantom_chg[0]["reason"], f"got: {phantom_chg[0]['reason']}")
    check("REF-303: chg-303 severity HIGH", phantom_chg[0]["severity"] == "HIGH", f"got {phantom_chg[0]['severity']}")

input_ids = {"chg-301", "fee-301", "chg-302", "fee-302", "chg-303", "fee-303", "pay-301", "pay-302"}
for d in disc_body.get("discrepancies", []):
    check(f"Discrepancy {d['discrepancy_id']} maps to valid source record", d["constituent_id"] in input_ids, f"constituent_id={d['constituent_id']} not in {input_ids}")

status, body = vercel_curl("GET", "/health")
check("Health endpoint: 200", status == 200, f"got {status}")

print(f"\n=== RESULTS: {PASS} passed, {FAIL} failed ===")
sys.exit(0 if FAIL == 0 else 1)