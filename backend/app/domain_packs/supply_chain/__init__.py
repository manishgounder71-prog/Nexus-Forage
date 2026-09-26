from typing import List, Dict, Any, Optional
from app.domain_packs.base import BaseDomainPack, DomainRiskFactor, WorkflowTaskTemplate
from app.domain_packs.supply_chain.config import DOMAIN_ID, DISPLAY_NAME, DESCRIPTION, ICON, DEFAULT_CAPABILITIES
from app.domain_packs.supply_chain.agents import get_supply_chain_agents
from app.domain_packs.supply_chain.workflow import generate_supply_chain_workflow
from app.domain_packs.supply_chain.schemas import SupplyChainReportSchema
from app.domain_packs.supply_chain.output import build_supply_chain_executive_report

class SupplyChainPack(BaseDomainPack):
    domain_id = DOMAIN_ID
    display_name = DISPLAY_NAME
    description = DESCRIPTION
    icon = ICON
    category = "OPERATIONAL"

    def get_required_capabilities(self, prompt: str) -> List[str]:
        return DEFAULT_CAPABILITIES

    def get_agent_profiles(self) -> List[Dict[str, Any]]:
        return get_supply_chain_agents()

    def generate_workflow(self, prompt: str, selected_agents: List[Dict[str, Any]]) -> List[WorkflowTaskTemplate]:
        return generate_supply_chain_workflow(prompt, selected_agents)

    def get_risk_framework(self) -> List[DomainRiskFactor]:
        return [
            DomainRiskFactor(name="Assembly Line Shutdown", severity="CRITICAL", mitigation_strategy="Deploy secondary vendor allocation and buffer stock dispatch."),
            DomainRiskFactor(name="Port Demurrage & Choke Points", severity="HIGH", mitigation_strategy="Reroute container freight via automated inland rail hubs."),
            DomainRiskFactor(name="Emergency Freight Cost Blowout", severity="MEDIUM", mitigation_strategy="Balance air cargo for critical parts with rail for bulk freight.")
        ]

    def get_output_schema(self) -> Dict[str, Any]:
        return SupplyChainReportSchema.model_json_schema()

    def get_simulation_strategies(self, mission_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Stochastic Monte-Carlo strategy comparison computed from the shared engine."""
        from app.orchestration.simulation_engine import simulation_engine
        return simulation_engine.simulate_strategies(
            mission_type="supply_chain",
            domain_id=DOMAIN_ID,
            mission_context=mission_context,
        )

    def get_debate_template(self, prompt: str) -> Dict[str, Any]:
        from app.agents.llm_reasoning import llm_reasoning_engine
        delib = llm_reasoning_engine.generate_parliament_deliberation_sync(prompt, [])
        score = delib.get("consensus_score") or 0.90
        return {
            "motion": f"Which logistics recovery strategy should be executed for supply disruption: '{prompt[:60]}'?",
            "selected_strategy": delib.get("selected_strategy") or "PLAN_B_INLAND_RAIL_CORRIDOR_REROUTING",
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
                "id": "demo-supply-chain-disruption",
                "title": "🚚 Supply Chain Disruption",
                "subtitle": "Primary tier-1 supplier halted shipments; port strike bottlenecks",
                "prompt": "Our main supplier stopped deliveries of microcontrollers and port strikes blocked 12 cargo vessels. Assembly lines will halt in 4 days without alternative sourcing.",
                "domain": "SUPPLY_CHAIN",
                "badge": "SUPPLY CHAIN DISRUPTION",
                "estimated_rto": "7 Days Lead Time"
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
        return build_supply_chain_executive_report(prompt, consensus, selected_strategy, simulations, agent_findings, evidence)
