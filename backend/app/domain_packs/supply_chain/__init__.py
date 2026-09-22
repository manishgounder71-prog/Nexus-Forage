from typing import List, Dict, Any
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
        return [
            {
                "id": "PLAN_A",
                "title": "Plan A: Emergency Heavy Truck Fleet Dispatch",
                "success_likelihood": 0.68,
                "risk_score": 0.45,
                "estimated_time_mins": 60,
                "cost_usd": 12000,
                "recommended": False,
                "methodology": "HEURISTIC_SIMULATION",
                "explanation": "Requires 400+ trucks on congested highways, causing secondary logistics bottlenecks."
            },
            {
                "id": "PLAN_B",
                "title": "Plan B: Container Vessel Rerouting via Secondary Rail Hubs",
                "success_likelihood": 0.91,
                "risk_score": 0.09,
                "estimated_time_mins": 120,
                "cost_usd": 14500,
                "recommended": True,
                "methodology": "HISTORICAL_COMPARISON",
                "explanation": "Optimal throughput. Reroutes inland freight via automated rail junctions, avoiding port strike choke points."
            },
            {
                "id": "PLAN_C",
                "title": "Plan C: Air Freight Emergency Cargo Airlift",
                "success_likelihood": 0.84,
                "risk_score": 0.22,
                "estimated_time_mins": 90,
                "cost_usd": 45000,
                "recommended": False,
                "methodology": "AGENT_ESTIMATION",
                "explanation": "Rapid delivery for critical goods but extremely cost prohibitive for high-volume cargo."
            }
        ]

    def get_debate_template(self, prompt: str) -> Dict[str, Any]:
        return {
            "motion": f"Which logistics recovery strategy should be executed for supply disruption: '{prompt[:60]}'?",
            "selected_strategy": "PLAN_B_INLAND_RAIL_CORRIDOR_REROUTING",
            "consensus_score": 0.91,
            "reasoning_summary": "Plan B selected: Reroute container freight via automated inland rail junctions, bypassing port strike choke points and preserving cold-chain refrigerated cargo.",
            "supporting_agents": ["Supply Chain Commander", "Supplier Analysis Agent", "Alternative Sourcing Agent", "Cost Optimization Agent"],
            "dissenting_agents": ["Operational Impact Agent (favored air cargo airlift for batch 1 to prevent factory line stop)"]
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
        agent_findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return build_supply_chain_executive_report(prompt, consensus, selected_strategy, simulations, agent_findings)
