from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class EnterpriseCrisisReportSchema(BaseModel):
    crisis_title: str
    severity: str
    stakeholders_affected: List[str]
    immediate_actions: List[str]
    operational_plan: List[str]
    communication_plan: Dict[str, Any]
    risk_register: List[Dict[str, Any]]
    contingency_plan: str
    dissenting_opinions: List[str]
    red_team_findings: List[str]
