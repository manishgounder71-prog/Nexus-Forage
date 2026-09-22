from typing import List, Dict, Any

def build_software_incident_executive_report(
    prompt: str,
    consensus: Dict[str, Any],
    selected_strategy: str,
    simulations: List[Dict[str, Any]],
    agent_findings: List[Dict[str, Any]]
) -> Dict[str, Any]:
    return {
        "title": f"💻 PRODUCTION INCIDENT RESPONSE REPORT",
        "domain": "SOFTWARE_INCIDENT",
        "situation": prompt,
        "severity": "🔴 P1 CRITICAL OUTAGE",
        "recommended_strategy": consensus.get("selected_strategy", "PLAN B: Canary Revert & Read-Only Replica Drain"),
        "estimated_recovery": "~25-35 minutes",
        "confidence": f"{int(consensus.get('consensus_score', 0.94) * 100)}%",
        "human_approval_required": True,
        "approval_notice": "⚠ High-impact rollback action requires human commander sign-off.",
        "why_this_strategy": consensus.get("reasoning_summary", "Drains active traffic to stable commit revision while preserving database write safety."),
        "probable_causes": [
            "Null pointer exception in authentication middleware deployed at latest release commit",
            "Postgres connection pool saturation (98% utilization) from unindexed join query",
            "Redis cache eviction spike triggering thundering herd on primary database"
        ],
        "key_evidence": [
            "HTTP 500 error rate spiked to 38.4% within 90 seconds of release deploy",
            "APM trace shows 4,200ms latency on /api/v1/auth endpoint",
            "Zero memory leaks detected in database engine itself — issue is application layer"
        ],
        "immediate_actions": [
            "1. Freeze all ongoing deployments and lock deployment pipeline",
            "2. Route 90% ingress traffic to read-only cache mirror cluster",
            "3. Isolate failing container pods and initiate rolling revision revert"
        ],
        "recovery_options": [
            {"option": "Option 1 (Fast Revert)", "rto": "15 mins", "risk": "Low", "description": "Immediate git revert to prior release tag."},
            {"option": "Option 2 (Live Hotfix)", "rto": "45 mins", "risk": "High", "description": "Patch SQL query in-flight without stopping pods."},
            {"option": "Option 3 (Blue-Green Switch)", "rto": "5 mins", "risk": "Minimal", "description": "Redirect DNS/router to previous blue environment."}
        ],
        "risks": [
            "Schema migration mismatch if database tables were altered in new release",
            "Session invalidation for actively connected authenticated users",
            "Delayed webhook delivery during canary drain"
        ],
        "rollback_recommendation": "Execute Automated Blue-Green Environment Switchback (Plan B) with Human Approval.",
        "dissenting_opinions": consensus.get("dissenting_agents", ["Risk Agent: Warns against in-flight database schema rollback"]),
        "red_team_findings": [
            "Identified risk: Reverting app without rolling back schema could break pending checkout sessions.",
            "Mitigation incorporated: Decoupled migration rollforward with backwards-compatible columns."
        ],
        "verification_checklist": [
            "✓ Error rate on APM drops below 0.05%",
            "✓ Database connection pool returns to < 25% utilization",
            "✓ Synthetic end-to-end checkout transaction completes successfully in under 300ms",
            "✓ Canary health checks green for 10 consecutive minutes"
        ],
        "lessons_learned": [
            "Enforce mandatory load-testing on unindexed database query changes in staging CI/CD.",
            "Implement automated canary rollback if error rate exceeds 1% in first 3 minutes of deploy."
        ]
    }
