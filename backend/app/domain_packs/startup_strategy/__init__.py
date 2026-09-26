from typing import List, Dict, Any, Optional
from app.domain_packs.base import BaseDomainPack, DomainRiskFactor, WorkflowTaskTemplate
from app.domain_packs.startup_strategy.config import DOMAIN_ID, DISPLAY_NAME, DESCRIPTION, ICON, DEFAULT_CAPABILITIES
from app.domain_packs.startup_strategy.agents import get_startup_strategy_agents
from app.domain_packs.startup_strategy.workflow import generate_startup_strategy_workflow
from app.domain_packs.startup_strategy.schemas import StartupStrategyReportSchema
from app.domain_packs.startup_strategy.output import build_startup_strategy_executive_report

class StartupStrategyPack(BaseDomainPack):
    domain_id = DOMAIN_ID
    display_name = DISPLAY_NAME
    description = DESCRIPTION
    icon = ICON
    category = "VENTURE"

    def get_required_capabilities(self, prompt: str) -> List[str]:
        return DEFAULT_CAPABILITIES

    def get_agent_profiles(self) -> List[Dict[str, Any]]:
        return get_startup_strategy_agents()

    def generate_workflow(self, prompt: str, selected_agents: List[Dict[str, Any]]) -> List[WorkflowTaskTemplate]:
        return generate_startup_strategy_workflow(prompt, selected_agents)

    def get_risk_framework(self) -> List[DomainRiskFactor]:
        return [
            DomainRiskFactor(name="Capital Depletion & Insolvency", severity="CRITICAL", mitigation_strategy="Enforce milestone commitments and structured cost control."),
            DomainRiskFactor(name="Market / Positioning Churn", severity="HIGH", mitigation_strategy="Focus roadmap on high-retention, high-ACV customers."),
            DomainRiskFactor(name="Key Contributor Flight Risk", severity="MEDIUM", mitigation_strategy="Re-align retention equity grants and leadership responsibilities.")
        ]

    def get_output_schema(self) -> Dict[str, Any]:
        return StartupStrategyReportSchema.model_json_schema()

    def get_simulation_strategies(self, mission_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Stochastic Monte-Carlo strategy comparison computed from the shared engine."""
        from app.orchestration.simulation_engine import simulation_engine
        return simulation_engine.simulate_strategies(
            mission_type="startup_strategy",
            domain_id=DOMAIN_ID,
            mission_context=mission_context,
        )

    def get_debate_template(self, prompt: str) -> Dict[str, Any]:
        from app.agents.llm_reasoning import llm_reasoning_engine
        delib = llm_reasoning_engine.generate_parliament_deliberation_sync(prompt, [])
        score = delib.get("consensus_score") or 0.90
        return {
            "motion": f"Which strategy should be executed for: '{prompt[:60]}'?",
            "selected_strategy": delib.get("selected_strategy") or "PLAN_B_STRATEGIC_REALIGNMENT",
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
                "id": "demo-startup-runway-decision",
                "title": "🚀 Startup Runway Decision",
                "subtitle": "3 months runway remaining: reduce costs, raise funding, or pivot?",
                "prompt": "We have three months of runway left ($140k cash, $44k/mo burn). Should we reduce costs, raise an insider bridge note, or pivot to enterprise B2B?",
                "domain": "STARTUP_STRATEGY",
                "badge": "VENTURE STRATEGY",
                "estimated_rto": "30 Days Plan"
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
        return build_startup_strategy_executive_report(prompt, consensus, selected_strategy, simulations, agent_findings, evidence)
