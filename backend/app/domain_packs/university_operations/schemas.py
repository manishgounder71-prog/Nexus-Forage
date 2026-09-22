from typing import List, Dict, Any
from pydantic import BaseModel

class UniversityOperationsReportSchema(BaseModel):
    situation_assessment: str
    immediate_actions: List[str]
    technical_recovery_plan: List[str]
    student_communication_plan: Dict[str, Any]
    alternative_examination_plan: Dict[str, Any]
    risk_analysis: List[Dict[str, Any]]
    timeline_hours: int
    dissenting_opinions: List[str]
    red_team_findings: List[str]
