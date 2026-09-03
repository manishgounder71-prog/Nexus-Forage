from typing import List, Dict, Any
from fastapi import APIRouter
from app.agents.registry import agent_registry
from app.core.config import settings

router = APIRouter(prefix="/agents", tags=["Agents"])

@router.get("", response_model=List[Dict[str, Any]])
async def list_agents():
    """Lists registered autonomous Lyzr agents, divisions, and operational scores."""
    agents = agent_registry.get_all_agents()
    return [
        {
            "id": a.agent_id,
            "name": a.name,
            "division": a.division,
            "specialization": a.specialization,
            "capabilities": a.capabilities,
            "reputation_score": a.reputation_score,
            "speed_score": a.speed_score,
            "cost_weight": a.cost_weight,
            "framework": "Lyzr Automata SDK",
            "runtime_state": "READY"
        }
        for a in agents
    ]

@router.get("/lyzr-telemetry", response_model=Dict[str, Any])
async def get_lyzr_orchestration_telemetry():
    """Returns real-time multi-agent orchestration telemetry for Lyzr Solo Agents."""
    agents = agent_registry.get_all_agents()
    return {
        "framework": "Lyzr Automata Multi-Agent Orchestrator",
        "api_configured": bool(settings.LYZR_API_KEY),
        "total_active_agents": len(agents),
        "divisions": list(set(a.division for a in agents)),
        "agents": [a.get_telemetry() if hasattr(a, 'get_telemetry') else {
            "agent_id": a.agent_id,
            "name": a.name,
            "division": a.division,
            "specialization": a.specialization
        } for a in agents]
    }

@router.get("/{agent_id}", response_model=Dict[str, Any])
async def get_agent_detail(agent_id: str):
    """Retrieves specific agent profile."""
    agent = agent_registry.get_agent_by_id(agent_id)
    if not agent:
        return {"error": "Agent not found"}
    return {
        "id": agent.agent_id,
        "name": agent.name,
        "division": agent.division,
        "specialization": agent.specialization,
        "capabilities": agent.capabilities,
        "reputation_score": agent.reputation_score,
        "framework": "Lyzr Automata SDK"
    }
