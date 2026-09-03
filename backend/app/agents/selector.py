from typing import List, Dict, Any
from app.agents.registry import agent_registry, LyzrAgentRuntimeAdapter
from app.schemas.agent_schemas import AgentSelectionResult

class DynamicAgentSelector:
    """
    Organization Architect engine that dynamically scores and recruits
    agents based on mission capability requirements and reputation metrics.
    """
    def select_team_for_mission(self, required_capabilities: List[str]) -> List[AgentSelectionResult]:
        selected_results = []
        all_agents = agent_registry.get_all_agents()

        for req_cap in required_capabilities:
            best_agent = None
            best_score = -1.0

            for agent in all_agents:
                # Expertise match score (1.0 if direct match, 0.5 fallback)
                match_score = 1.0 if req_cap in agent.capabilities else 0.5
                
                # Formula: Match x Reputation x Speed x Cost Weight
                score = round(
                    match_score * agent.reputation_score * agent.speed_score * agent.cost_weight, 
                    4
                )

                if score > best_score:
                    best_score = score
                    best_agent = agent

            if best_agent:
                selected_results.append(AgentSelectionResult(
                    agent_id=best_agent.agent_id,
                    agent_name=best_agent.name,
                    division=best_agent.division,
                    selection_score=best_score,
                    assigned_role=f"Lead for {req_cap}"
                ))

        return selected_results

agent_selector = DynamicAgentSelector()
