from typing import List, Dict, Any, Optional
from app.agents.registry import agent_registry, LyzrAgentRuntimeAdapter
from app.schemas.agent_schemas import AgentSelectionResult
from app.domain_packs.base import BaseDomainPack

class AdaptiveOrganizationEngine:
    """
    Adaptive Organization Engine:
    Transforms mission requirements into a customized, capability-matched AI team.
    Calculates expertise match, reputation score, speed, and cost efficiency.
    Provides concise explainability for every recruited agent.
    """
    def form_organization(
        self,
        required_capabilities: List[str],
        domain_pack: BaseDomainPack,
        secondary_domains: Optional[List[str]] = None,
        is_hybrid: bool = False
    ) -> List[AgentSelectionResult]:
        selected_results: List[AgentSelectionResult] = []
        recruited_agent_ids = set()
        all_agents = agent_registry.get_all_agents()

        # Always include Mission Commander as the apex coordinator
        commander = agent_registry.get_agent_by_id("commander_01")
        if commander:
            selected_results.append(AgentSelectionResult(
                agent_id=commander.agent_id,
                agent_name=commander.name,
                division=commander.division,
                selection_score=0.99,
                assigned_role="Mission Commander & Orchestration Lead"
            ))
            recruited_agent_ids.add(commander.agent_id)

        # Match capabilities to best agents
        for req_cap in required_capabilities:
            best_agent: Optional[LyzrAgentRuntimeAdapter] = None
            best_score = -1.0

            for agent in all_agents:
                # Direct match score: 1.0 for direct capability, 0.45 fallback
                match_score = 1.0 if req_cap in agent.capabilities else 0.45

                # Weight domain alignment bonus if agent's division/specialization matches
                domain_bonus = 1.05 if domain_pack.domain_id.lower() in agent.specialization.lower() else 1.0

                # Adaptive Scoring Formula: Match * Reputation * Speed * Cost * Bonus
                score = round(
                    match_score * agent.reputation_score * agent.speed_score * agent.cost_weight * domain_bonus,
                    4
                )

                if score > best_score and agent.agent_id not in recruited_agent_ids:
                    best_score = score
                    best_agent = agent

            if best_agent:
                role_title = self._format_role_title(req_cap, best_agent.name)
                selected_results.append(AgentSelectionResult(
                    agent_id=best_agent.agent_id,
                    agent_name=best_agent.name,
                    division=best_agent.division,
                    selection_score=best_score,
                    assigned_role=role_title
                ))
                recruited_agent_ids.add(best_agent.agent_id)

        # Ensure Red Team auditor is always included for adversarial review
        if "red_team_01" not in recruited_agent_ids:
            rt_agent = agent_registry.get_agent_by_id("red_team_01")
            if rt_agent:
                selected_results.append(AgentSelectionResult(
                    agent_id=rt_agent.agent_id,
                    agent_name=rt_agent.name,
                    division=rt_agent.division,
                    selection_score=0.96,
                    assigned_role="Adversarial Red Team Stress-Test Auditor"
                ))
                recruited_agent_ids.add(rt_agent.agent_id)

        return selected_results

    def _format_role_title(self, capability: str, agent_name: str) -> str:
        readable = capability.replace("_", " ").title()
        return f"Lead Specialist for {readable}"

adaptive_org_engine = AdaptiveOrganizationEngine()
