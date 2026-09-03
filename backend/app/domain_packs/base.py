from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class DomainRiskFactor(BaseModel):
    name: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    mitigation_strategy: str

class WorkflowTaskTemplate(BaseModel):
    task_id: str
    name: str
    preferred_capability: str
    role_title: str
    dependencies: List[str] = Field(default_factory=list)
    description: str = ""

class BaseDomainPack(ABC):
    domain_id: str
    display_name: str
    description: str
    icon: str
    category: str = "OPERATIONAL"

    @abstractmethod
    def get_required_capabilities(self, prompt: str) -> List[str]:
        """Extracts key required capabilities needed for this domain."""
        pass

    @abstractmethod
    def get_agent_profiles(self) -> List[Dict[str, Any]]:
        """Returns standard agent profiles specialized for this domain."""
        pass

    @abstractmethod
    def generate_workflow(self, prompt: str, selected_agents: List[Dict[str, Any]]) -> List[WorkflowTaskTemplate]:
        """Generates DAG task workflow nodes with dependencies tailored to this domain."""
        pass

    @abstractmethod
    def get_risk_framework(self) -> List[DomainRiskFactor]:
        """Returns domain-specific risk matrices and mitigation heuristics."""
        pass

    @abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        """Returns domain-specific report sections structure."""
        pass

    @abstractmethod
    def get_simulation_strategies(self, mission_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Returns domain-specific strategy alternatives for simulation/parliament comparison."""
        pass

    @abstractmethod
    def get_debate_template(self, prompt: str) -> Dict[str, Any]:
        """Returns domain-specific debate motion, candidate strategies, and consensus reasoning."""
        pass

    @abstractmethod
    def get_sample_scenarios(self) -> List[Dict[str, Any]]:
        """Returns realistic demo mission scenarios for this domain."""
        pass

    @abstractmethod
    def generate_executive_report(
        self,
        prompt: str,
        consensus: Dict[str, Any],
        selected_strategy: str,
        simulations: List[Dict[str, Any]],
        agent_findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Builds comprehensive standardized Domain Command Report."""
        pass
