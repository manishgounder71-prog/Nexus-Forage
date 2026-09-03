import httpx
import time
import json

def clean(s):
    if s is None:
        return ""
    if isinstance(s, str):
        return s.encode('ascii', 'ignore').decode('ascii')
    return s

client = httpx.Client(timeout=30.0)

test_prompts = [
    "b2b saas incident",
    "power grid blackout",
    "server crash",
    "supply chain delay"
]

print("=" * 75)
print("TESTING SHORT / TERSE INPUT PHRASES (2-3 WORDS EACH)")
print("=" * 75)

for p in test_prompts:
    res = client.post("http://localhost:8000/api/v1/missions", json={"raw_prompt": p})
    data = res.json()
    mid = data["mission_id"]
    print(f"\n[+] SUBMITTED SHORT PROMPT: '{p}' -> Mission: {mid}")
    time.sleep(7.5)
    
    rep_res = client.get(f"http://localhost:8000/api/v1/missions/{mid}")
    rep = rep_res.json()
    exec_rep = rep.get("executive_report", {})
    
    print(f"    * Status: {rep.get('status')}")
    print(f"    * Domain: {clean(rep.get('domain'))} ({clean(rep.get('domain_pack'))}) [Confidence: {int(rep.get('confidence',0)*100)}%]")
    print(f"    * Title: {clean(exec_rep.get('title'))}")
    print(f"    * Severity: {clean(exec_rep.get('severity'))}")
    print(f"    * Strategy: {clean(exec_rep.get('recommended_strategy'))}")
    print(f"    * Rationale: {clean(exec_rep.get('why_this_strategy'))}")
    
    if "alternative_strategies" in exec_rep:
        print("    * Alternatives:")
        for alt in exec_rep["alternative_strategies"]:
            print(f"      - {clean(alt.get('plan'))}: {clean(alt.get('estimated_impact'))}")

print("\n" + "=" * 75)
