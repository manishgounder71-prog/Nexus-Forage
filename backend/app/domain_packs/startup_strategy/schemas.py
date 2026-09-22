from typing import List, Dict, Any
from pydantic import BaseModel

class StartupStrategyReportSchema(BaseModel):
    executive_recommendation: str
    runway_status: str
    burn_reduction_target: str
    alternative_strategies: List[Dict[str, Any]]
    assumptions: List[str]
    risks: List[str]
    next_30_days_plan: List[str]
    decision_triggers: List[str]
    dissenting_opinions: List[str]
    red_team_findings: List[str]
