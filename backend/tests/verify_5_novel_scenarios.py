import asyncio
import json
import httpx

NOVEL_SCENARIOS = [
    {
        "id": "1. Startup Strategy - Competitor Open-Source AI Disruption",
        "domain_expected": "STARTUP_STRATEGY",
        "prompt": "Our B2B analytics startup is seeing a 25% drop in conversion because a well-funded rival launched an open-source clone. Should we match them with an open-core model, pivot to vertical healthcare AI, or double down on enterprise SOC2 security?"
    },
    {
        "id": "2. Software Incident - Kafka Pipeline Lag & PostgreSQL Desync",
        "domain_expected": "SOFTWARE_INCIDENT",
        "prompt": "Our real-time event streaming pipeline has a 4-hour Kafka consumer lag across 8 partitions following a schema registry update, causing out-of-order transactions in PostgreSQL."
    },
    {
        "id": "3. Enterprise Crisis - Ransomware Extortion on Hospital EHR",
        "domain_expected": "ENTERPRISE_CRISIS",
        "prompt": "DarkSide ransomware has encrypted our regional hospital electronic health records database, demanding $2M in Bitcoin with 12 hours before patient telemetry feeds fail."
    },
    {
        "id": "4. Supply Chain - Semiconductor Foundry Fire & Wafer Shortage",
        "domain_expected": "SUPPLY_CHAIN",
        "prompt": "A major fire at our primary TSMC fabrication facility destroyed 40% of our microcontroller wafer inventory right before Q4 holiday manufacturing."
    },
    {
        "id": "5. University Operations - Admissions Portal DDoS Lockout",
        "domain_expected": "UNIVERSITY_OPERATIONS",
        "prompt": "A massive DDoS attack has brought down the university admissions portal 6 hours before the international early-decision deadline, locking out 8,000 applicants."
    }
]

async def run_test():
    base_url = "http://localhost:8000"
    print("=" * 80)
    print("TESTING 5 NOVEL, UNBUILT SCENARIOS ACROSS NEXUS FORGE ENGINE")
    print("=" * 80)

    async with httpx.AsyncClient(timeout=30.0) as client:
        for idx, sc in enumerate(NOVEL_SCENARIOS, 1):
            print(f"\n" + "="*70)
            print(f"[SCENARIO {idx}/5]: {sc['id']}")
            print(f"PROMPT: \"{sc['prompt']}\"")
            print("="*70)
            
            # 1. Create Mission
            res = await client.post(f"{base_url}/api/v1/missions", json={"raw_prompt": sc["prompt"]})
            if res.status_code != 200:
                print(f"[ERROR] Failed to create mission: {res.text}")
                continue
            
            m_data = res.json()
            mission_id = m_data["mission_id"]
            print(f"[+] Mission Dispatched: {mission_id}")
            
            # 2. Wait for async multi-agent pipeline completion
            print("[...] Swarm Deliberating & Executing DAG in parallel (waiting 6.5s)...")
            await asyncio.sleep(6.5)
            
            # 3. Retrieve Mission Status & Report
            status_res = await client.get(f"{base_url}/api/v1/missions/{mission_id}")
            report_data = status_res.json()
            
            if report_data.get("status") == "COMPLETED":
                exec_report = report_data.get("executive_report", {})
                analysis = report_data.get("analysis", {})
                consensus = report_data.get("consensus", {})
                
                print(f"[+] DOMAIN DETECTED: {report_data.get('domain')} ({report_data.get('domain_pack')})")
                print(f"[+] CONFIDENCE: {int(report_data.get('confidence', 0) * 100)}% | IS HYBRID: {report_data.get('is_hybrid')}")
                print(f"[+] REPORT TITLE: {exec_report.get('title')}")
                print(f"[+] SEVERITY: {exec_report.get('severity')}")
                print(f"[+] RECOMMENDED STRATEGY: {exec_report.get('recommended_strategy')}")
                print(f"[+] ESTIMATED TIMELINE: {exec_report.get('estimated_recovery') or exec_report.get('timeline_hours') or exec_report.get('timeline_days')}")
                print(f"[+] EXECUTIVE RATIONALE: {exec_report.get('why_this_strategy') or exec_report.get('why_strat')}")
                
                if "alternative_strategies" in exec_report:
                    print("[+] DYNAMIC STRATEGIC ALTERNATIVES GENERATED:")
                    for plan in exec_report["alternative_strategies"]:
                        print(f"    * {plan.get('plan')}: {plan.get('estimated_impact')} (Risk: {plan.get('risk')})")
                elif "alternative_options" in exec_report:
                    print("[+] DYNAMIC RECOVERY OPTIONS:")
                    for opt in exec_report["alternative_options"]:
                        print(f"    * {opt.get('option')}: {opt.get('lead_time')} (Cost: {opt.get('cost_premium')}, Risk: {opt.get('risk')})")
                
                print(f"[+] CONSENSUS REASONING: {consensus.get('reasoning_summary')}")
                if exec_report.get('red_team_findings'):
                    print(f"[+] RED TEAM AUDIT: {exec_report.get('red_team_findings')[0]}")
            else:
                print(f"[!] Status: {report_data.get('status')}")

if __name__ == "__main__":
    asyncio.run(run_test())
