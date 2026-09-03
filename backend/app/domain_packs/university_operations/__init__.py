from typing import List, Dict, Any
from app.domain_packs.base import BaseDomainPack, DomainRiskFactor, WorkflowTaskTemplate
from app.domain_packs.university_operations.config import DOMAIN_ID, DISPLAY_NAME, DESCRIPTION, ICON, DEFAULT_CAPABILITIES
from app.domain_packs.university_operations.agents import get_university_operations_agents
from app.domain_packs.university_operations.workflow import generate_university_operations_workflow
from app.domain_packs.university_operations.schemas import UniversityOperationsReportSchema
from app.domain_packs.university_operations.output import build_university_operations_executive_report

class UniversityOperationsPack(BaseDomainPack):
    domain_id = DOMAIN_ID
    display_name = DISPLAY_NAME
    description = DESCRIPTION
    icon = ICON
    category = "OPERATIONAL"

    def get_required_capabilities(self, prompt: str) -> List[str]:
        return DEFAULT_CAPABILITIES

    def get_agent_profiles(self) -> List[Dict[str, Any]]:
        return get_university_operations_agents()

    def generate_workflow(self, prompt: str, selected_agents: List[Dict[str, Any]]) -> List[WorkflowTaskTemplate]:
        return generate_university_operations_workflow(prompt, selected_agents)

    def get_risk_framework(self) -> List[DomainRiskFactor]:
        return [
            DomainRiskFactor(name="Student Panic & Social Media Escalation", severity="CRITICAL", mitigation_strategy="Rapid transparent email broadcast and grace period policy within 20 minutes."),
            DomainRiskFactor(name="Exam Integrity & Paper Leakage", severity="HIGH", mitigation_strategy="Algorithmic variable randomization per exam paper copy."),
            DomainRiskFactor(name="Secondary Database Pool Crash", severity="HIGH", mitigation_strategy="Scale stateless read mirrors with PgBouncer connection pooler.")
        ]

    def get_output_schema(self) -> Dict[str, Any]:
        return UniversityOperationsReportSchema.model_json_schema()

    def get_simulation_strategies(self, mission_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "id": "PLAN_A",
                "title": "Plan A: Force Instant Server Reboot & Proceed on Schedule",
                "success_likelihood": 0.65,
                "risk_score": 0.54,
                "estimated_time_mins": 30,
                "cost_usd": 1200,
                "recommended": False,
                "methodology": "HEURISTIC_SIMULATION",
                "explanation": "High risk of immediate secondary crash during 9:00 AM synchronized login rush."
            },
            {
                "id": "PLAN_B",
                "title": "Plan B: Read-Only Mirror & Staggered 24-Hour Exam Windows",
                "success_likelihood": 0.93,
                "risk_score": 0.08,
                "estimated_time_mins": 90,
                "cost_usd": 3800,
                "recommended": True,
                "methodology": "HISTORICAL_COMPARISON",
                "explanation": "Optimal academic resilience. Matches historical 2024 university outage resolution with zero student penalty."
            },
            {
                "id": "PLAN_C",
                "title": "Plan C: Total Semester Exam Cancellation & Pro-Rata Grading",
                "success_likelihood": 0.72,
                "risk_score": 0.44,
                "estimated_time_mins": 240,
                "cost_usd": 15000,
                "recommended": False,
                "methodology": "AGENT_ESTIMATION",
                "explanation": "Eliminates technical stress but causes extreme academic fairness complaints from graduating seniors."
            }
        ]

    def get_debate_template(self, prompt: str) -> Dict[str, Any]:
        return {
            "motion": f"Which contingency strategy should be executed for academic exam crisis: '{prompt[:60]}'?",
            "selected_strategy": "PLAN_B_READ_ONLY_MIRROR_STAGGERED_EXAM",
            "consensus_score": 0.93,
            "reasoning_summary": "Plan B selected: Read-only mirror portal deployed for student authentication while chunked database snapshot restore executes in background, accompanied by a 24-hour staggered exam window.",
            "supporting_agents": ["Academic Operations Commander", "Technical Recovery Agent", "Student Impact Agent", "University Communications Agent"],
            "dissenting_agents": ["Academic Risk Agent (cautioned on take-home exam integrity)"]
        }

    def get_sample_scenarios(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "demo-examination-portal-crisis",
                "title": "🎓 Examination Portal Crisis",
                "subtitle": "Central exam portal crashed 24h before finals, 12,000 students locked out",
                "prompt": "The university examination portal crashed 24 hours before final exams. 12,000 students cannot access their test papers and database connections are exhausted.",
                "domain": "UNIVERSITY_OPERATIONS",
                "badge": "ACADEMIC CRISIS",
                "estimated_rto": "4h Recovery + 24h Reschedule"
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
        return build_university_operations_executive_report(prompt, consensus, selected_strategy, simulations, agent_findings)
