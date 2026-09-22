from typing import List, Dict, Any

def get_university_operations_agents() -> List[Dict[str, Any]]:
    return [
        {
            "agent_id": "commander_univ",
            "name": "Academic Operations Commander",
            "division": "Strategy",
            "specialization": "Campus Incident Coordination, Provost Escalation & Academic Continuity",
            "capabilities": ["mission_coordination", "command", "operational_containment"],
            "reputation_score": 0.98,
            "speed_score": 0.94,
            "cost_weight": 0.7
        },
        {
            "agent_id": "tech_rec_univ_01",
            "name": "Technical Recovery Agent",
            "division": "Infrastructure",
            "specialization": "LMS Exam Portal, Database Replicas, SSO Auth & Cloud Scalability",
            "capabilities": ["technical_recovery", "infrastructure_recovery"],
            "reputation_score": 0.96,
            "speed_score": 0.93,
            "cost_weight": 0.8
        },
        {
            "agent_id": "student_univ_01",
            "name": "Student Impact Agent",
            "division": "Intelligence",
            "specialization": "Academic Fairness, Special Accommodations, Stress Mitigation & Exam Integrity",
            "capabilities": ["student_impact_mitigation", "incident_intelligence"],
            "reputation_score": 0.95,
            "speed_score": 0.91,
            "cost_weight": 0.75
        },
        {
            "agent_id": "sched_univ_01",
            "name": "Scheduling Coordinator Agent",
            "division": "Strategy",
            "specialization": "Exam Timetable Slot Reallocation, Hall Proctoring & Retake Staggering",
            "capabilities": ["scheduling_coordination", "resource_allocation"],
            "reputation_score": 0.94,
            "speed_score": 0.92,
            "cost_weight": 0.7
        },
        {
            "agent_id": "comms_univ_01",
            "name": "University Communications Agent",
            "division": "Strategy",
            "specialization": "Student Body Email Broadcasts, Faculty Guidelines & SMS Alert Protocol",
            "capabilities": ["stakeholder_communication"],
            "reputation_score": 0.95,
            "speed_score": 0.95,
            "cost_weight": 0.75
        },
        {
            "agent_id": "risk_univ_01",
            "name": "Academic Risk Agent",
            "division": "Risk & Operations",
            "specialization": "Exam Paper Leak Detection, Academic Integrity Audits & Compliance",
            "capabilities": ["risk_assessment", "adversarial_analysis"],
            "reputation_score": 0.96,
            "speed_score": 0.89,
            "cost_weight": 0.8
        }
    ]
