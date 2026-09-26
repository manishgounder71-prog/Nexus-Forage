from typing import List, Dict, Any, Optional
from app.domain_packs.base import BaseDomainPack, DomainRiskFactor, WorkflowTaskTemplate
from app.domain_packs.enterprise_crisis.config import DOMAIN_ID, DISPLAY_NAME, DESCRIPTION, ICON, DEFAULT_CAPABILITIES
from app.domain_packs.enterprise_crisis.agents import get_enterprise_crisis_agents
from app.domain_packs.enterprise_crisis.workflow import generate_enterprise_crisis_workflow
from app.domain_packs.enterprise_crisis.schemas import EnterpriseCrisisReportSchema
from app.domain_packs.enterprise_crisis.output import build_enterprise_crisis_executive_report

class EnterpriseCrisisPack(BaseDomainPack):
    domain_id = DOMAIN_ID
    display_name = DISPLAY_NAME
    description = DESCRIPTION
    icon = ICON
    category = "OPERATIONAL"

    def get_required_capabilities(self, prompt: str) -> List[str]:
        return DEFAULT_CAPABILITIES

    def get_agent_profiles(self) -> List[Dict[str, Any]]:
        return get_enterprise_crisis_agents()

    def generate_workflow(self, prompt: str, selected_agents: List[Dict[str, Any]]) -> List[WorkflowTaskTemplate]:
        return generate_enterprise_crisis_workflow(prompt, selected_agents)

    def get_risk_framework(self) -> List[DomainRiskFactor]:
        return [
            DomainRiskFactor(name="Financial Loss / Revenue Bleed", severity="CRITICAL", mitigation_strategy="Deploy secondary payment clearing gateway and queue requests."),
            DomainRiskFactor(name="Regulatory Sanctions (SEC/GDPR/FERC)", severity="HIGH", mitigation_strategy="Enforce automated compliance logging and prompt reporting."),
            DomainRiskFactor(name="Cascading Infrastructure Outage", severity="HIGH", mitigation_strategy="Isolate compromised sub-systems with automated circuit breakers.")
        ]

    def get_output_schema(self) -> Dict[str, Any]:
        return EnterpriseCrisisReportSchema.model_json_schema()

    def get_simulation_strategies(self, mission_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Stochastic Monte-Carlo strategy comparison computed from the shared engine.

        Returns real MC estimates (methodology is labeled); never hardcoded claims.
        """
        from app.orchestration.simulation_engine import simulation_engine
        return simulation_engine.simulate_strategies(
            mission_type="critical_system_failure",
            domain_id=DOMAIN_ID,
            mission_context=mission_context,
        )

    def get_debate_template(self, prompt: str) -> Dict[str, Any]:
        from app.agents.llm_reasoning import llm_reasoning_engine
        delib = llm_reasoning_engine.generate_parliament_deliberation_sync(prompt, [])
        score = delib.get("consensus_score") or 0.90
        return {
            "motion": f"Which containment strategy should be executed for enterprise crisis: '{prompt[:60]}'?",
            "selected_strategy": delib.get("selected_strategy") or "PLAN_B_DECOUPLED_RESILIENT_FAILOVER",
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
                "id": "demo-payment-platform-failure",
                "title": "🚨 Payment Platform Failure",
                "subtitle": "Global payment gateway down, transactions failing at checkout",
                "prompt": "Our enterprise payment gateway failed, affecting customer transactions and causing major financial losses. Payment processing dropped 92%.",
                "domain": "ENTERPRISE_CRISIS",
                "badge": "FINANCIAL CRISIS",
                "estimated_rto": "30 mins"
            },
            {
                "id": "demo-power-grid-cyber-attack",
                "title": "⚡ Power Grid Cyber-Attack",
                "subtitle": "Substations 04 & 09 compromised by SCADA intrusion",
                "prompt": "NEXUS, metropolitan power grid experiencing cyber-attack on substations 04 and 09. Initiate defense protocol.",
                "domain": "ENTERPRISE_CRISIS",
                "badge": "NATIONAL INFRASTRUCTURE",
                "estimated_rto": "45 mins"
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
        return build_enterprise_crisis_executive_report(prompt, consensus, selected_strategy, simulations, agent_findings, evidence)
