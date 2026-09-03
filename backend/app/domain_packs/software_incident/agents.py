from typing import List, Dict, Any

def get_software_incident_agents() -> List[Dict[str, Any]]:
    return [
        {
            "agent_id": "commander_sw",
            "name": "Incident Commander",
            "division": "Strategy",
            "specialization": "Production Outage Incident Command & SLA Management",
            "capabilities": ["mission_coordination", "command", "stakeholder_communication"],
            "reputation_score": 0.99,
            "speed_score": 0.95,
            "cost_weight": 0.7
        },
        {
            "agent_id": "root_cause_01",
            "name": "Root Cause Analyst Agent",
            "division": "Intelligence",
            "specialization": "Log Inspection, Stack Tracing & Regression Triaging",
            "capabilities": ["root_cause_analysis", "incident_analysis", "system_analysis"],
            "reputation_score": 0.96,
            "speed_score": 0.92,
            "cost_weight": 0.75
        },
        {
            "agent_id": "infra_sw_01",
            "name": "Infrastructure Agent",
            "division": "Infrastructure",
            "specialization": "Kubernetes Cluster, Load Balancer & Database Health Audit",
            "capabilities": ["infrastructure_analysis", "infrastructure_recovery"],
            "reputation_score": 0.94,
            "speed_score": 0.91,
            "cost_weight": 0.8
        },
        {
            "agent_id": "dep_sw_01",
            "name": "Dependency Agent",
            "division": "Intelligence",
            "specialization": "Downstream Microservice & Third-Party API Degradation Mapping",
            "capabilities": ["dependency_analysis", "incident_intelligence"],
            "reputation_score": 0.93,
            "speed_score": 0.90,
            "cost_weight": 0.7
        },
        {
            "agent_id": "rollback_sw_01",
            "name": "Rollback Agent",
            "division": "Strategy",
            "specialization": "Canary Rollback, Blue-Green Traffic Shifting & Hotfix Packaging",
            "capabilities": ["rollback_planning", "recovery_strategy"],
            "reputation_score": 0.97,
            "speed_score": 0.96,
            "cost_weight": 0.85
        },
        {
            "agent_id": "risk_sw_01",
            "name": "Risk Agent",
            "division": "Risk & Operations",
            "specialization": "Data Loss Verification & Database Lock Contention Audit",
            "capabilities": ["risk_assessment", "adversarial_analysis"],
            "reputation_score": 0.95,
            "speed_score": 0.89,
            "cost_weight": 0.8
        }
    ]
