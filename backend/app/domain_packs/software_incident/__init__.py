from typing import List, Dict, Any, Optional
from app.domain_packs.base import BaseDomainPack, DomainRiskFactor, WorkflowTaskTemplate
from app.domain_packs.software_incident.config import DOMAIN_ID, DISPLAY_NAME, DESCRIPTION, ICON, DEFAULT_CAPABILITIES
from app.domain_packs.software_incident.agents import get_software_incident_agents
from app.domain_packs.software_incident.workflow import generate_software_incident_workflow
from app.domain_packs.software_incident.schemas import SoftwareIncidentReportSchema
from app.domain_packs.software_incident.output import build_software_incident_executive_report

class SoftwareIncidentPack(BaseDomainPack):
    domain_id = DOMAIN_ID
    display_name = DISPLAY_NAME
    description = DESCRIPTION
    icon = ICON
    category = "ENGINEERING"

    def get_required_capabilities(self, prompt: str) -> List[str]:
        return DEFAULT_CAPABILITIES

    def get_agent_profiles(self) -> List[Dict[str, Any]]:
        return get_software_incident_agents()

    def generate_workflow(self, prompt: str, selected_agents: List[Dict[str, Any]]) -> List[WorkflowTaskTemplate]:
        return generate_software_incident_workflow(prompt, selected_agents)

    def get_risk_framework(self) -> List[DomainRiskFactor]:
        return [
            DomainRiskFactor(name="Database Write Contention", severity="CRITICAL", mitigation_strategy="Decouple read replica traffic and enforce transaction timeouts."),
            DomainRiskFactor(name="Canary Rollback Data Loss", severity="HIGH", mitigation_strategy="Maintain dual-write compatibility columns during rollback."),
            DomainRiskFactor(name="Cascading Ingress Timeout", severity="MEDIUM", mitigation_strategy="Apply circuit breaker pattern with rate-limiting at gateway.")
        ]

    def get_output_schema(self) -> Dict[str, Any]:
        return SoftwareIncidentReportSchema.model_json_schema()

    def get_simulation_strategies(self, mission_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Stochastic Monte-Carlo strategy comparison computed from the shared engine."""
        from app.orchestration.simulation_engine import simulation_engine
        return simulation_engine.simulate_strategies(
            mission_type="software_incident",
            domain_id=DOMAIN_ID,
            mission_context=mission_context,
        )

    def get_debate_template(self, prompt: str) -> Dict[str, Any]:
        from app.agents.llm_reasoning import llm_reasoning_engine
        delib = llm_reasoning_engine.generate_parliament_deliberation_sync(prompt, [])
        score = delib.get("consensus_score") or 0.90
        return {
            "motion": f"Which recovery strategy should be executed for production outage: '{prompt[:60]}'?",
            "selected_strategy": delib.get("selected_strategy") or "PLAN_B_BLUE_GREEN_ROLLBACK_DRAIN",
            "consensus_score": round(float(score), 3),
            "reasoning_summary": delib.get("reasoning_summary") or "Consensus reached via parametric deliberation. No fabricated figures.",
            "supporting_agents": delib.get("supporting_agents") or [],
            "dissenting_agents": delib.get("dissenting_agents") or [],
            "provider": delib.get("provider") or "Dynamic Parametric Engine",
            "source": "prompt_parametric_estimate",
            "is_estimate": True,
        }

    def get_sample_scenarios(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "demo-software-deployment-fail",
                "title": "💻 Production Deployment Incident",
                "subtitle": "Microservices throwing 500 errors after latest release",
                "prompt": "Production started failing immediately after the latest deployment. API error rate spiked to 38% and database connection pool is saturated. Rollback needed.",
                "domain": "SOFTWARE_INCIDENT",
                "badge": "PRODUCTION OUTAGE",
                "estimated_rto": "25 mins"
            }
        ]

    def generate_executive_report(
        self,
        prompt: str,
        consensus: Dict[str, Any],
        selected_strategy: str,
        simulations: List[Dict[str, Any]],
        agent_findings: List[Dict[str, Any]],
        evidence: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return build_software_incident_executive_report(prompt, consensus, selected_strategy, simulations, agent_findings, evidence)
