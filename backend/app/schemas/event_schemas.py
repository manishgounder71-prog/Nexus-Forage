from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class MissionEventSchema(BaseModel):
    event_id: str
    mission_id: str
    event_type: str  # MISSION_CREATED, MISSION_ANALYZED, MEMORY_RETRIEVED, ORGANIZATION_FORMED, AGENT_STARTED, TASK_COMPLETED, DEBATE_MESSAGE, CONSENSUS_REACHED, RED_TEAM_STARTED, REFLECTION_COMPLETED, MISSION_COMPLETED
    stage: str
    message: str
    timestamp: str
    data: Dict[str, Any] = Field(default_factory=dict)
