import httpx
import json

def clean(s):
    if s is None:
        return ""
    if isinstance(s, str):
        return s.encode('ascii', 'ignore').decode('ascii')
    return s

m_ids = [
    ("b2b saas incident", "msn_11cd63cf"),
    ("power grid blackout", "msn_31ba3fb3"),
    ("server crash", "msn_f968c0aa"),
    ("supply chain delay", "msn_cf516189")
]

print("=" * 80)
print("FETCHING COMPLETED REPORTS FOR SHORT / TERSE INPUT PHRASES")
print("=" * 80)

for p_text, mid in m_ids:
    r = httpx.get(f"http://localhost:8000/api/v1/missions/{mid}", timeout=10.0)
    data = r.json()
    exec_rep = data.get("executive_report", {})
    consensus = data.get("consensus", {})
    
    print("\n" + "=" * 70)
    print(f"SHORT INPUT: \"{p_text}\" (Mission: {mid})")
    print(f"STATUS: {data.get('status')} | DOMAIN: {clean(data.get('domain'))} ({clean(data.get('domain_pack'))})")
    print(f"REPORT TITLE: {clean(exec_rep.get('title'))}")
    print(f"SEVERITY: {clean(exec_rep.get('severity'))}")
    print(f"RECOMMENDED STRATEGY: {clean(exec_rep.get('recommended_strategy'))}")
    print(f"EXECUTIVE RATIONALE: {clean(exec_rep.get('why_this_strategy'))}")
    
    if "alternative_strategies" in exec_rep:
        print("DYNAMIC STRATEGIC ALTERNATIVES:")
        for alt in exec_rep["alternative_strategies"]:
            print(f"  * {clean(alt.get('plan'))}: {clean(alt.get('estimated_impact'))}")
    elif "alternative_options" in exec_rep:
        print("DYNAMIC RECOVERY OPTIONS:")
        for opt in exec_rep["alternative_options"]:
            print(f"  * {clean(opt.get('option'))}: {clean(opt.get('lead_time'))} ({clean(opt.get('cost_premium'))})")
    elif "immediate_actions" in exec_rep:
        print("IMMEDIATE ACTIONS:")
        for act in exec_rep["immediate_actions"][:3]:
            print(f"  * {clean(act)}")
    print("=" * 70)
