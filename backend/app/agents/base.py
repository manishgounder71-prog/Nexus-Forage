from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class AgentCapability(BaseModel):
    name: str
    description: str

class BaseAgent(ABC):
    def __init__(
        self,
        agent_id: str,
        name: str,
        division: str,
        specialization: str,
        capabilities: List[str],
        cost_weight: float = 0.7,
        speed_score: float = 0.9,
        reputation_score: float = 0.92
    ):
        self.agent_id = agent_id
        self.name = name
        self.division = division
        self.specialization = specialization
        self.capabilities = capabilities
        self.cost_weight = cost_weight
        self.speed_score = speed_score
        self.reputation_score = reputation_score
        self.total_missions = 0

    @abstractmethod
    async def execute_task(self, task_name: str, input_context: Dict[str, Any]) -> Dict[str, Any]:
        """Executes task and returns structured result payload."""
        pass
