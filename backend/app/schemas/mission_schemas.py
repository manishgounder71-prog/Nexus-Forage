from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class MissionCreateRequest(BaseModel):
    raw_prompt: str = Field(..., description="Spoken or typed mission scenario text")
    source: str = Field("web_voice", description="Source device or input channel")

class MissionAnalysisOutput(BaseModel):
    mission_title: str
    mission_type: str
    primary_domain: str = "SOFTWARE_INCIDENT"
    confidence: float = 0.94
    is_hybrid: bool = False
    secondary_domains: List[str] = Field(default_factory=list)
    domain_pack_name: str = "Software Incident Response"
    domain_pack_icon: str = "💻"
    reasoning_summary: str = ""
    severity: str = "CRITICAL"
    urgency: float = 0.95
    deadline_hours: int = 24
    constraints: List[str] = Field(default_factory=list)
    required_capabilities: List[str] = Field(default_factory=list)

class MissionResponse(BaseModel):
    id: str
    title: str
    raw_prompt: str
    primary_domain: str = "SOFTWARE_INCIDENT"
    confidence: float = 0.94
    is_hybrid: bool = False
    secondary_domains: List[str] = Field(default_factory=list)
    mission_type: str
    severity: str
    urgency: float
    deadline_hours: int
    status: str
    constraints: List[str] = Field(default_factory=list)
    required_capabilities: List[str] = Field(default_factory=list)
    created_at: str

    model_config = ConfigDict(from_attributes=True)
