from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class AgentProfile(BaseModel):
    id: str
    name: str
    division: str
    specialization: str
    capabilities: List[str]
    cost_weight: float
    speed_score: float
    reputation_score: float
    total_missions: int

class AgentSelectionResult(BaseModel):
    agent_id: str
    agent_name: str
    division: str
    selection_score: float
    assigned_role: str

class AgentMessageSchema(BaseModel):
    message_id: str
    from_agent: str
    to_agent: str
    mission_id: str
    message_type: str  # EVIDENCE, PROPOSAL, CHALLENGE, AGREEMENT, DISAGREEMENT, DECISION
    content: Dict[str, Any]
    confidence: float
    timestamp: str
