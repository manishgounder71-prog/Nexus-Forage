from typing import List, Dict, Any
from app.domain_packs.base import WorkflowTaskTemplate

def generate_supply_chain_workflow(prompt: str, agents: List[Dict[str, Any]]) -> List[WorkflowTaskTemplate]:
    return [
        WorkflowTaskTemplate(
            task_id="sc_task_01",
            name="Supplier Failure Root Cause & Solvency Triage",
            preferred_capability="supplier_analysis",
            role_title="Supplier Analysis Agent",
            dependencies=[],
            description="Audit supplier default trigger, backlog magnitude, and contract force majeure clauses."
        ),
        WorkflowTaskTemplate(
            task_id="sc_task_02",
            name="Inventory Stockout & Assembly Line Impact Assessment",
            preferred_capability="impact_assessment",
            role_title="Operational Impact Agent",
            dependencies=[],
            description="Model days-of-inventory remaining across warehouses and quantify assembly line halt risks."
        ),
        WorkflowTaskTemplate(
            task_id="sc_task_03",
            name="Alternative Secondary Sourcing & Spot Market Scan",
            preferred_capability="alternative_sourcing",
            role_title="Alternative Sourcing Agent",
            dependencies=[],
            description="Identify pre-qualified Tier-2 vendors with available production capacity and tooling."
        ),
        WorkflowTaskTemplate(
            task_id="sc_task_04",
            name="Expedited Freight & Inland Rail Logistics Optimization",
            preferred_capability="logistics_rerouting",
            role_title="Cost Optimization Agent",
            dependencies=["sc_task_01", "sc_task_02", "sc_task_03"],
            description="Model air freight vs automated inland rail junctions to bypass port demurrage choke points."
        ),
        WorkflowTaskTemplate(
            task_id="sc_task_05",
            name="Parliament Supply Chain Recovery Deliberation",
            preferred_capability="risk_assessment",
            role_title="Supply Chain Commander",
            dependencies=["sc_task_04"],
            description="Synthesize dual-vendor allocation strategy balancing expedited freight cost vs lead time."
        )
    ]
