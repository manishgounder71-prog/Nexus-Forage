from typing import List, Dict, Any

def build_university_operations_executive_report(
    prompt: str,
    consensus: Dict[str, Any],
    selected_strategy: str,
    simulations: List[Dict[str, Any]],
    agent_findings: List[Dict[str, Any]]
) -> Dict[str, Any]:
    return {
        "title": "🎓 UNIVERSITY ACADEMIC OPERATIONS CRISIS REPORT",
        "domain": "UNIVERSITY_OPERATIONS",
        "situation": prompt,
        "severity": "🔴 CRITICAL ACADEMIC DISRUPTION",
        "recommended_strategy": consensus.get("selected_strategy", "PLAN B: Read-Only Mirror Deployment + Staggered Exam Windows"),
        "estimated_recovery": "~4 Hours Technical Recovery + 24h Reschedule",
        "confidence": f"{int(consensus.get('consensus_score', 0.93) * 100)}%",
        "why_this_strategy": "Deploys cached read-only exam paper mirror for authentication while chunked database snapshots restore in the background, paired with a 24-hour staggered testing window ensuring no student is penalized.",
        "situation_assessment": "Central examination portal suffered database connection pool exhaustion under 45,000 concurrent student logins 24 hours prior to final examinations.",
        "immediate_actions": [
            "1. Freeze portal countdown clocks and broadcast emergency reassurance banner to student portal",
            "2. Spin up stateless read-only CDN cached paper distribution nodes across 3 cloud regions",
            "3. Notify Department Chairs and Proctoring Leads to suspend scheduled in-person verification penalties"
        ],
        "technical_recovery_plan": [
            "Phase 1 (0-1h): Scale database read replicas from 2 to 12 nodes behind PgBouncer connection pooler",
            "Phase 2 (1-2h): Isolate student SSO authentication gateway from submission write pipelines",
            "Phase 3 (2-4h): Execute synthetic load test with 60,000 simulated student sessions"
        ],
        "student_communication_plan": {
            "official_email": "Mandatory reassuring announcement sent to all 12,000 enrolled students within 20 minutes.",
            "sms_blast": "SMS notification confirming 24-hour exam window extension with no academic penalties.",
            "social_media_desk": "Monitored student forum desk providing live 24/7 technical support."
        },
        "alternative_examination_plan": {
            "rescheduled_window": "Staggered 36-hour submission window (Students select any 3-hour continuous block)",
            "alternative_offline_option": "PDF encrypted paper download available as fallback with timestamped upload",
            "grading_fairness_policy": "No late submission penalties applied; automatic 15-minute grace period"
        },
        "risk_analysis": [
            {"risk": "Academic Integrity / Paper Leakage", "severity": "High", "mitigation": "Dynamic question parameter randomization for each student sitting."},
            {"risk": "Social Media Backlash & Panic", "severity": "Medium", "mitigation": "Transparent hourly status bulletins from Provost Office."},
            {"risk": "Secondary Server Crash at Rescheduled Time", "severity": "High", "mitigation": "Staggered login queues (5,000 students per 30-min block)."}
        ],
        "timeline_hours": 24,
        "dissenting_opinions": consensus.get("dissenting_agents", ["Academic Risk Agent: Expressed concern regarding take-home academic integrity risks"]),
        "red_team_findings": [
            "Red team vulnerability: Single SSO gateway could bottleneck second login wave.",
            "Mitigation: Decoupled anonymous token authentication deployed with offline token signature."
        ],
        "lessons_learned": [
            "Mandate decoupled static paper download mirrors 48 hours prior to campus-wide exam periods.",
            "Implement multi-tiered queueing for SSO authentication during synchronized testing events."
        ]
    }
