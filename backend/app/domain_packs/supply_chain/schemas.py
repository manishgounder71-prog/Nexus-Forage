from typing import List, Dict, Any
from pydantic import BaseModel

class SupplyChainReportSchema(BaseModel):
    situation_assessment: str
    affected_operations: List[str]
    alternative_options: List[Dict[str, Any]]
    cost_comparison: Dict[str, Any]
    timeline_days: int
    supply_risks: List[str]
    recommended_recovery_plan: str
    dissenting_opinions: List[str]
    red_team_findings: List[str]
