import httpx
import json

def clean(s):
    if s is None:
        return ""
    if isinstance(s, str):
        return s.encode('ascii', 'ignore').decode('ascii')
    return s

m_ids = ["msn_656f8983", "msn_0f2ac937", "msn_071ba9eb", "msn_d47942d6", "msn_e0a66ce8"]
prompts = [
    "1. Startup Strategy: Competitor open-source clone causing 25% drop in conversion",
    "2. Software Incident: 4-hour Kafka consumer lag causing out-of-order PostgreSQL transactions",
    "3. Enterprise Crisis: DarkSide ransomware demanding $2M on hospital EHR",
    "4. Supply Chain: TSMC foundry fire destroying 40% microcontroller wafer inventory",
    "5. University Operations: Admissions portal DDoS attack 6h before deadline"
]

for idx, (mid, p_desc) in enumerate(zip(m_ids, prompts), 1):
    r = httpx.get(f"http://localhost:8000/api/v1/missions/{mid}", timeout=10.0)
    data = r.json()
    print("=" * 75)
    print(f"[SCENARIO {idx}]: {clean(p_desc)}")
    print(f"MISSION ID: {mid} | STATUS: {data.get('status')}")
    print(f"DETECTED DOMAIN: {clean(data.get('domain'))} ({clean(data.get('domain_pack'))}) | CONFIDENCE: {int(data.get('confidence', 0)*100)}%")
    rep = data.get("executive_report", {})
    print(f"REPORT TITLE: {clean(rep.get('title'))}")
    print(f"SEVERITY: {clean(rep.get('severity'))}")
    print(f"RECOMMENDED STRATEGY: {clean(rep.get('recommended_strategy'))}")
    print(f"EXECUTIVE RATIONALE: {clean(rep.get('why_this_strategy'))}")
    
    if "alternative_strategies" in rep:
        print("ALTERNATIVE PLANS:")
        for p in rep["alternative_strategies"]:
            print(f"  - {clean(p.get('plan'))}: {clean(p.get('estimated_impact'))} (Risk: {clean(p.get('risk'))})")
    elif "alternative_options" in rep:
        print("ALTERNATIVE OPTIONS:")
        for o in rep["alternative_options"]:
            print(f"  - {clean(o.get('option'))}: {clean(o.get('lead_time'))} (Cost: {clean(o.get('cost_premium'))}, Risk: {clean(o.get('risk'))})")
    elif "recovery_options" in rep:
        print("RECOVERY OPTIONS:")
        for ro in rep["recovery_options"]:
            print(f"  - {clean(ro.get('option'))}: {clean(ro.get('description'))} (RTO: {clean(ro.get('rto'))}, Risk: {clean(ro.get('risk'))})")
    
    consensus = data.get("consensus", {})
    print(f"PARLIAMENT CONSENSUS: {clean(consensus.get('reasoning_summary'))}")
    print("=" * 75 + "\n")
