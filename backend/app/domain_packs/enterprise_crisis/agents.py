from typing import List, Dict, Any

def get_enterprise_crisis_agents() -> List[Dict[str, Any]]:
    return [
        {
            "agent_id": "commander_ec",
            "name": "Crisis Commander",
            "division": "Strategy",
            "specialization": "Executive Crisis Escalation, Enterprise Continuity & SLA Governance",
            "capabilities": ["mission_coordination", "command", "operational_containment"],
            "reputation_score": 0.99,
            "speed_score": 0.95,
            "cost_weight": 0.7
        },
        {
            "agent_id": "intel_ec_01",
            "name": "Incident Intelligence Agent",
            "division": "Intelligence",
            "specialization": "Threat Triage, Anomaly Telemetry & Forensic Impact Quantification",
            "capabilities": ["incident_intelligence", "incident_analysis"],
            "reputation_score": 0.96,
            "speed_score": 0.93,
            "cost_weight": 0.75
        },
        {
            "agent_id": "ops_ec_01",
            "name": "Operations Agent",
            "division": "Infrastructure",
            "specialization": "Disaster Recovery, Air-Gap Containment & Secondary Gateway Switchover",
            "capabilities": ["operational_containment", "infrastructure_recovery"],
            "reputation_score": 0.95,
            "speed_score": 0.92,
            "cost_weight": 0.8
        },
        {
            "agent_id": "risk_ec_01",
            "name": "Risk & Compliance Agent",
            "division": "Risk & Operations",
            "specialization": "Regulatory Sanctions, Fraud Exposure & Financial Liability Audit",
            "capabilities": ["risk_assessment", "regulatory_compliance"],
            "reputation_score": 0.94,
            "speed_score": 0.88,
            "cost_weight": 0.8
        },
        {
            "agent_id": "resource_ec_01",
            "name": "Resource Agent",
            "division": "Risk & Operations",
            "specialization": "Emergency Liquidity, Compute Buffer & Failover Key Distribution",
            "capabilities": ["resource_allocation", "dependency_analysis"],
            "reputation_score": 0.93,
            "speed_score": 0.91,
            "cost_weight": 0.7
        },
        {
            "agent_id": "comms_ec_01",
            "name": "Communications Agent",
            "division": "Strategy",
            "specialization": "Executive Briefings, Customer Crisis Updates & Regulatory PR Protocol",
            "capabilities": ["stakeholder_communication"],
            "reputation_score": 0.95,
            "speed_score": 0.94,
            "cost_weight": 0.75
        }
    ]
