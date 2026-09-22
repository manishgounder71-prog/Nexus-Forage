from typing import List, Dict, Any
from app.domain_packs.base import WorkflowTaskTemplate

def generate_enterprise_crisis_workflow(prompt: str, agents: List[Dict[str, Any]]) -> List[WorkflowTaskTemplate]:
    lowered = prompt.lower()
    is_power_grid = "power grid" in lowered or "substation" in lowered or "scada" in lowered or "cyber-attack" in lowered

    if is_power_grid:
        return [
            WorkflowTaskTemplate(
                task_id="ec_task_01",
                name="SCADA Substation 04 & 09 Air-Gap Isolation",
                preferred_capability="incident_intelligence",
                role_title="SCADA Security Specialist",
                dependencies=[],
                description="Air-gap compromised PLC control networks to prevent lateral exploit spread."
            ),
            WorkflowTaskTemplate(
                task_id="ec_task_02",
                name="Grid Load Rerouting & Feeder Frequency Balancing",
                preferred_capability="operational_containment",
                role_title="Grid Frequency Balancer Agent",
                dependencies=[],
                description="Reroute power feeder circuits to prevent cascade tripping on Substation 11."
            ),
            WorkflowTaskTemplate(
                task_id="ec_task_03",
                name="Encrypted Microgrid Keys & Failover Allocation",
                preferred_capability="resource_allocation",
                role_title="Operations Manager Agent",
                dependencies=[],
                description="Distribute emergency cryptographic RTU token keys to isolated substations."
            ),
            WorkflowTaskTemplate(
                task_id="ec_task_04",
                name="Parliament Grid Defense Strategy Deliberation",
                preferred_capability="risk_assessment",
                role_title="Crisis Commander",
                dependencies=["ec_task_01", "ec_task_02", "ec_task_03"],
                description="Debate immediate breaker trip vs staggered load shed failover."
            )
        ]

    return [
        WorkflowTaskTemplate(
            task_id="ec_task_01",
            name="Incident Telemetry & Fraud/Impact Forensic Triage",
            preferred_capability="incident_intelligence",
            role_title="Incident Intelligence Agent",
            dependencies=[],
            description="Isolate failing transaction nodes, quantify monetary burn rate, and identify attack vector."
        ),
        WorkflowTaskTemplate(
            task_id="ec_task_02",
            name="Secondary Gateway Failover & Circuit Breaker Isolation",
            preferred_capability="operational_containment",
            role_title="Operations Agent",
            dependencies=[],
            description="Activate hot-standby clearing gateway and apply rate-limiting to untrusted ingress."
        ),
        WorkflowTaskTemplate(
            task_id="ec_task_03",
            name="Regulatory Exposure & Sanctions Liability Assessment",
            preferred_capability="regulatory_compliance",
            role_title="Risk & Compliance Agent",
            dependencies=[],
            description="Audit SLA non-compliance penalties, SEC/GDPR mandatory disclosure windows, and loss limits."
        ),
        WorkflowTaskTemplate(
            task_id="ec_task_04",
            name="Parliament Crisis Deliberation & Containment Protocol",
            preferred_capability="risk_assessment",
            role_title="Crisis Commander",
            dependencies=["ec_task_01", "ec_task_02", "ec_task_03"],
            description="Coordinate executive leadership strategy selection and stakeholder communication plan."
        )
    ]
