from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SoftwareIncidentReportSchema(BaseModel):
    incident_title: str
    severity_level: str = "P1_CRITICAL"
    probable_causes: List[str]
    evidence: List[str]
    immediate_actions: List[str]
    recovery_options: List[Dict[str, Any]]
    risks_identified: List[str]
    rollback_recommendation: str
    human_approval_required: bool = True
    verification_checklist: List[str]
    dissenting_opinions: List[str]
    red_team_findings: List[str]
