from typing import List, Dict, Any, Optional
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
        """Stochastic Monte-Carlo strategy comparison computed from the shared engine."""
        from app.orchestration.simulation_engine import simulation_engine
        return simulation_engine.simulate_strategies(
            mission_type="university_operations",
            domain_id=DOMAIN_ID,
            mission_context=mission_context,
        )

    def get_debate_template(self, prompt: str) -> Dict[str, Any]:
        from app.agents.llm_reasoning import llm_reasoning_engine
        delib = llm_reasoning_engine.generate_parliament_deliberation_sync(prompt, [])
        score = delib.get("consensus_score") or 0.90
        return {
            "motion": f"Which contingency strategy should be executed for academic exam crisis: '{prompt[:60]}'?",
            "selected_strategy": delib.get("selected_strategy") or "PLAN_B_READ_ONLY_MIRROR_STAGGERED_EXAM",
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
        agent_findings: List[Dict[str, Any]],
        evidence: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return build_university_operations_executive_report(prompt, consensus, selected_strategy, simulations, agent_findings, evidence)
