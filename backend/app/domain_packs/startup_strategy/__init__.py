from typing import List, Dict, Any
from app.domain_packs.base import BaseDomainPack, DomainRiskFactor, WorkflowTaskTemplate
from app.domain_packs.startup_strategy.config import DOMAIN_ID, DISPLAY_NAME, DESCRIPTION, ICON, DEFAULT_CAPABILITIES
from app.domain_packs.startup_strategy.agents import get_startup_strategy_agents
from app.domain_packs.startup_strategy.workflow import generate_startup_strategy_workflow
from app.domain_packs.startup_strategy.schemas import StartupStrategyReportSchema
from app.domain_packs.startup_strategy.output import build_startup_strategy_executive_report
from app.domain_packs.scenario_analyzer import scenario_analyzer

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
        prompt = mission_context.get("prompt", "")
        analysis = scenario_analyzer.analyze_startup_scenario(prompt)
        plans = analysis.get("alternative_strategies", [])

        if len(plans) >= 3:
            p_a, p_b, p_c = plans[0], plans[1], plans[2]
            return [
                {
                    "id": "PLAN_A",
                    "title": p_a.get("plan", "Plan A: Defensive Austere Mode"),
                    "success_likelihood": 0.62,
                    "risk_score": 0.55,
                    "estimated_time_mins": 10,
                    "cost_usd": 0,
                    "recommended": False,
                    "methodology": "HEURISTIC_SIMULATION",
                    "explanation": p_a.get("estimated_impact", "High execution risk; potential disruption to core product velocity.")
                },
                {
                    "id": "PLAN_B",
                    "title": p_b.get("plan", "Plan B: High-Leverage Strategic Pivot & Focus"),
                    "success_likelihood": 0.92,
                    "risk_score": 0.12,
                    "estimated_time_mins": 25,
                    "cost_usd": 45000,
                    "recommended": True,
                    "methodology": "HISTORICAL_COMPARISON",
                    "explanation": p_b.get("estimated_impact", "Optimal survival and growth profile balancing execution speed with risk insulation.")
                },
                {
                    "id": "PLAN_C",
                    "title": p_c.get("plan", "Plan C: Alternative Strategic M&A or Niche Realignment"),
                    "success_likelihood": 0.58,
                    "risk_score": 0.65,
                    "estimated_time_mins": 60,
                    "cost_usd": 15000,
                    "recommended": False,
                    "methodology": "AGENT_ESTIMATION",
                    "explanation": p_c.get("estimated_impact", "Prolonged execution window with elevated external dependency risk.")
                }
            ]

        return [
            {
                "id": "PLAN_A",
                "title": "Plan A: Immediate Headcount & Marketing Burn Freeze",
                "success_likelihood": 0.62,
                "risk_score": 0.55,
                "estimated_time_mins": 10,
                "cost_usd": 0,
                "recommended": False,
                "methodology": "HEURISTIC_SIMULATION",
                "explanation": "Extends immediate runway but slows engineering output."
            },
            {
                "id": "PLAN_B",
                "title": "Plan B: Strategic Realignment & Lean High-Value Pivot",
                "success_likelihood": 0.92,
                "risk_score": 0.11,
                "estimated_time_mins": 30,
                "cost_usd": 35000,
                "recommended": True,
                "methodology": "HISTORICAL_COMPARISON",
                "explanation": "Balances rapid cost optimization with upfront cashflow collection."
            },
            {
                "id": "PLAN_C",
                "title": "Plan C: Strategic Partnership / Acqui-Hire Evaluation",
                "success_likelihood": 0.54,
                "risk_score": 0.68,
                "estimated_time_mins": 90,
                "cost_usd": 15000,
                "recommended": False,
                "methodology": "AGENT_ESTIMATION",
                "explanation": "Long closing timeline with deal execution risks."
            }
        ]

    def get_debate_template(self, prompt: str) -> Dict[str, Any]:
        analysis = scenario_analyzer.analyze_startup_scenario(prompt)
        rec = analysis.get("recommended_strategy", "PLAN_B: Strategic Focus")
        
        return {
            "motion": f"Which strategy should be executed for: '{prompt[:60]}'?",
            "selected_strategy": rec,
            "consensus_score": 0.92,
            "reasoning_summary": analysis.get("why_this_strategy", "Optimal balance between runway extension and business value creation."),
            "supporting_agents": ["Venture Strategy Lead", "Financial Analyst", "Product Lead", "Market Strategist"],
            "dissenting_agents": analysis.get("dissenting_opinions", ["Growth Specialist (urged continuing top-of-funnel testing)"])
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
        agent_findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return build_startup_strategy_executive_report(prompt, consensus, selected_strategy, simulations, agent_findings)
