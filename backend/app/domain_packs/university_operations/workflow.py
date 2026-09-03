from typing import List, Dict, Any
from app.domain_packs.base import WorkflowTaskTemplate

def generate_university_operations_workflow(prompt: str, agents: List[Dict[str, Any]]) -> List[WorkflowTaskTemplate]:
    return [
        WorkflowTaskTemplate(
            task_id="univ_task_01",
            name="LMS Examination Portal & Database Diagnostics",
            preferred_capability="technical_recovery",
            role_title="Technical Recovery Agent",
            dependencies=[],
            description="Isolate connection pool exhaustion on exam DB and deploy read-only mirror servers."
        ),
        WorkflowTaskTemplate(
            task_id="univ_task_02",
            name="Student Impact & Academic Fairness Triage",
            preferred_capability="student_impact_mitigation",
            role_title="Student Impact Agent",
            dependencies=[],
            description="Audit affected cohorts (12,000 undergraduates) and evaluate grace periods vs retakes."
        ),
        WorkflowTaskTemplate(
            task_id="univ_task_03",
            name="Alternative Timetable & Proctoring Slot Rescheduling",
            preferred_capability="scheduling_coordination",
            role_title="Scheduling Coordinator Agent",
            dependencies=[],
            description="Calculate staggered exam sitting windows and reserve physical campus test centers."
        ),
        WorkflowTaskTemplate(
            task_id="univ_task_04",
            name="Student & Faculty Crisis Communication Broadcast",
            preferred_capability="stakeholder_communication",
            role_title="University Communications Agent",
            dependencies=["univ_task_01", "univ_task_02", "univ_task_03"],
            description="Draft unified transparent guidance preventing panic on social channels and student forums."
        ),
        WorkflowTaskTemplate(
            task_id="univ_task_05",
            name="Parliament Academic Contingency Strategy Deliberation",
            preferred_capability="risk_assessment",
            role_title="Academic Operations Commander",
            dependencies=["univ_task_04"],
            description="Deliberate hybrid portal deployment vs staggered 48h take-home assessment."
        )
    ]
