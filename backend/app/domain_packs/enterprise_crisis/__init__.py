from typing import List, Dict, Any
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
        lowered = str(mission_context.get("prompt", "")).lower()
        if "power grid" in lowered or "substation" in lowered or "cyber-attack" in lowered:
            return [
                {
                    "id": "PLAN_A",
                    "title": "Plan A: Immediate Substation Breaker Tripping",
                    "success_likelihood": 0.71,
                    "risk_score": 0.52,
                    "estimated_time_mins": 25,
                    "cost_usd": 4200,
                    "recommended": False,
                    "methodology": "HEURISTIC_SIMULATION",
                    "explanation": "Fastest reaction but carries high probability of cascading frequency collapse across adjacent feeder lines."
                },
                {
                    "id": "PLAN_B",
                    "title": "Plan B: Automated Microgrid Failover & Air-Gapped Key Exchange",
                    "success_likelihood": 0.94,
                    "risk_score": 0.06,
                    "estimated_time_mins": 45,
                    "cost_usd": 9800,
                    "recommended": True,
                    "methodology": "HISTORICAL_COMPARISON",
                    "explanation": "Highest overall success rate. Isolates compromised SCADA nodes on substations 04 & 09 while deploying encrypted microgrid power loops."
                },
                {
                    "id": "PLAN_C",
                    "title": "Plan C: Total Regional Blackout Reset",
                    "success_likelihood": 0.78,
                    "risk_score": 0.30,
                    "estimated_time_mins": 180,
                    "cost_usd": 18500,
                    "recommended": False,
                    "methodology": "AGENT_ESTIMATION",
                    "explanation": "Complete containment but causes total metropolitan outage lasting up to 3 hours."
                }
            ]

        return [
            {
                "id": "PLAN_A",
                "title": "Plan A: Emergency Payment Engine Restart & Cache Flush",
                "success_likelihood": 0.68,
                "risk_score": 0.49,
                "estimated_time_mins": 15,
                "cost_usd": 2500,
                "recommended": False,
                "methodology": "HEURISTIC_SIMULATION",
                "explanation": "Quick reboot but risks duplicate payment processing for queued transactions."
            },
            {
                "id": "PLAN_B",
                "title": "Plan B: Secondary Payment Gateway Switchover & Idempotent Buffer",
                "success_likelihood": 0.94,
                "risk_score": 0.07,
                "estimated_time_mins": 30,
                "cost_usd": 6800,
                "recommended": True,
                "methodology": "HISTORICAL_COMPARISON",
                "explanation": "Safest and most resilient. Zero duplicate debits and full transactional audit trail."
            },
            {
                "id": "PLAN_C",
                "title": "Plan C: Offline Batch Settlement Mode",
                "success_likelihood": 0.79,
                "risk_score": 0.28,
                "estimated_time_mins": 90,
                "cost_usd": 11200,
                "recommended": False,
                "methodology": "AGENT_ESTIMATION",
                "explanation": "High throughput but exposes company to merchant chargeback liability."
            }
        ]

    def get_debate_template(self, prompt: str) -> Dict[str, Any]:
        lowered = prompt.lower()
        if "power grid" in lowered or "substation" in lowered or "cyber-attack" in lowered:
            return {
                "motion": f"Which defense protocol should be executed for grid cyber incident: '{prompt[:60]}'?",
                "selected_strategy": "PLAN_B_MICROGRID_FAILOVER_AIRGAP",
                "consensus_score": 0.94,
                "reasoning_summary": "Plan B selected: Air-gap compromised SCADA nodes on Substations 04 & 09 immediately, failover feeder load to Substation 02 microgrid, and deploy signed RTU firmware.",
                "supporting_agents": ["Crisis Commander", "Incident Intelligence Agent", "Operations Agent"],
                "dissenting_agents": ["Risk & Compliance Agent (warned of feeder overload risk during transition)"]
            }

        return {
            "motion": f"Which containment strategy should be executed for enterprise crisis: '{prompt[:60]}'?",
            "selected_strategy": "PLAN_B_SECONDARY_GATEWAY_SWITCHOVER",
            "consensus_score": 0.93,
            "reasoning_summary": "Plan B selected: Instant failover to secondary clearing network while buffering transactions prevents $2.4M in potential duplicate charge liabilities.",
            "supporting_agents": ["Crisis Commander", "Incident Intelligence Agent", "Operations Agent", "Resource Agent"],
            "dissenting_agents": ["Risk & Compliance Agent (emphasized strict SEC/regulatory filing timing)"]
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
        agent_findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return build_enterprise_crisis_executive_report(prompt, consensus, selected_strategy, simulations, agent_findings)
