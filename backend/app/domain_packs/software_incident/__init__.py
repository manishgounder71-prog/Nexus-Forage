from typing import List, Dict, Any
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
        return [
            {
                "id": "PLAN_A",
                "title": "Plan A: Immediate Hard Pod Reboot & Cache Purge",
                "success_likelihood": 0.64,
                "risk_score": 0.58,
                "estimated_time_mins": 10,
                "cost_usd": 1500,
                "recommended": False,
                "methodology": "HEURISTIC_SIMULATION",
                "explanation": "High velocity but triggers thundering herd cache stampede on primary Postgres cluster."
            },
            {
                "id": "PLAN_B",
                "title": "Plan B: Blue-Green Revision Rollback & Read Replica Isolation",
                "success_likelihood": 0.95,
                "risk_score": 0.05,
                "estimated_time_mins": 25,
                "cost_usd": 3200,
                "recommended": True,
                "methodology": "HISTORICAL_COMPARISON",
                "explanation": "Safest recovery. Switches ingress router back to verified healthy release with zero schema loss."
            },
            {
                "id": "PLAN_C",
                "title": "Plan C: In-Flight SQL Patch & Hotfix Deploy",
                "success_likelihood": 0.76,
                "risk_score": 0.38,
                "estimated_time_mins": 60,
                "cost_usd": 4800,
                "recommended": False,
                "methodology": "AGENT_ESTIMATION",
                "explanation": "Avoids rollback but introduces latency while hotfix compile and unit test suite runs."
            }
        ]

    def get_debate_template(self, prompt: str) -> Dict[str, Any]:
        return {
            "motion": f"Which recovery strategy should be executed for production outage: '{prompt[:60]}'?",
            "selected_strategy": "PLAN_B_BLUE_GREEN_ROLLBACK_DRAIN",
            "consensus_score": 0.95,
            "reasoning_summary": "Plan B selected: Blue-Green ingress switchback ensures instantaneous user traffic recovery while isolating problematic migration scripts.",
            "supporting_agents": ["Incident Commander", "Root Cause Analyst Agent", "Rollback Agent", "Infrastructure Agent"],
            "dissenting_agents": ["Risk Agent (raised schema backwards-compatibility caution)"]
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
        agent_findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return build_software_incident_executive_report(prompt, consensus, selected_strategy, simulations, agent_findings)
