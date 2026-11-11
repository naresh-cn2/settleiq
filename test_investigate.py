"""Investigate discrepancies in detail on production."""
import urllib.request
import json

BASE = "https://settleiq-zeta.vercel.app"
API_KEY = "settleiq-test-key-2024"


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


# Get latest run
status, body = api("GET", "/v1/runs")
print(f"Runs count: {body.get('count')}")
for r in body.get("runs", [])[:5]:
    print(f"  Run: {r.get('run_id', r.get('id', 'unknown'))[:16]}... disc_count={r.get('discrepancy_count', '?')}")

if not body.get("runs"):
    print("No runs found. Exiting.")
    exit(0)

run_id = body["runs"][0].get("run_id") or body["runs"][0].get("id")
print(f"\nInvestigating run: {run_id}")

# Get discrepancies
status, disc_body = api("GET", f"/v1/runs/{run_id}/discrepancies")
print(f"Discrepancies: {disc_body.get('count')}")
for d in disc_body.get("discrepancies", []):
    disc_id = d["discrepancy_id"]
    print(f"\n  {disc_id}:")
    print(f"    type={d.get('type')} severity={d.get('severity')}")
    print(f"    reason={d.get('reason', 'N/A')[:120]}")

    # Investigate
    status, inv = api("GET", f"/v1/runs/{run_id}/discrepancies/{disc_id}/investigate")
    if status == 200:
        print(f"    Investigation OK: keys={list(inv.keys())}")
        if "hypotheses" in inv:
            for h in inv["hypotheses"][:3]:
                print(f"      Hypothesis: {h.get('description', 'N/A')[:100]} conf={h.get('confidence', 'N/A')}")
        if "trace" in inv:
            trace = inv["trace"]
            if trace:
                nodes = trace.get("nodes", [])
                print(f"      Trace nodes: {len(nodes)}")
    else:
        print(f"    Investigation failed: {status} {inv}")

print("\nDone.")