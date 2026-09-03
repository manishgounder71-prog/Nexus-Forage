from typing import List, Dict, Any
from app.domain_packs.base import WorkflowTaskTemplate

def generate_software_incident_workflow(prompt: str, agents: List[Dict[str, Any]]) -> List[WorkflowTaskTemplate]:
    """
    Required workflow:
    Incident Detection
          ↓
    Parallel Investigation
          ├── Root Cause Analysis
          ├── Infrastructure Analysis
          └── Dependency Analysis
          ↓
    Rollback Options
          ↓
    Risk Review
          ↓
    Recovery Strategy
          ↓
    Red Team
          ↓
    Final Action Plan
    """
    return [
        WorkflowTaskTemplate(
            task_id="sw_task_01",
            name="Parallel Root Cause Analysis & Log Triage",
            preferred_capability="root_cause_analysis",
            role_title="Root Cause Analyst Agent",
            dependencies=[],
            description="Isolate fatal exceptions, recent git commit SHAs, and failing telemetry indicators."
        ),
        WorkflowTaskTemplate(
            task_id="sw_task_02",
            name="Infrastructure & Cluster Health Audit",
            preferred_capability="infrastructure_analysis",
            role_title="Infrastructure Agent",
            dependencies=[],
            description="Examine Kubernetes pod crashes, CPU/OOM throttles, and connection pool saturation."
        ),
        WorkflowTaskTemplate(
            task_id="sw_task_03",
            name="Downstream Microservice & Dependency Mapping",
            preferred_capability="dependency_analysis",
            role_title="Dependency Agent",
            dependencies=[],
            description="Audit upstream API gateways, cache latency, and database write lock contention."
        ),
        WorkflowTaskTemplate(
            task_id="sw_task_04",
            name="Rollback Matrix & Canary Traffic Drain Planning",
            preferred_capability="rollback_planning",
            role_title="Rollback Agent",
            dependencies=["sw_task_01", "sw_task_02", "sw_task_03"],
            description="Synthesize zero-data-loss rollback procedure vs live database migration hotfix."
        ),
        WorkflowTaskTemplate(
            task_id="sw_task_05",
            name="Parliament Strategy Debate & Consensus Synthesis",
            preferred_capability="recovery_strategy",
            role_title="Incident Commander",
            dependencies=["sw_task_04"],
            description="Host multi-agent parliamentary deliberation to vote on optimal recovery strategy."
        )
    ]
