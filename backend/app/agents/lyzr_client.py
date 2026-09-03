"""
Real Lyzr Agent Framework v3 HTTP client.

Wraps the Lyzr Agents API (https://agix.studio.lyzr.ai / agent-prod.studio.lyzr.ai) so the
orchestration engine can genuinely delegate task execution to Lyzr when a valid
LYZR_API_KEY + base URL are configured. Falls back to a deterministic local runtime
(Documented in runtime.py) when no credentials are present, so the system keeps
working offline and in demo mode.

Documented endpoints used:
  - POST /v3/agents/                          create an agent -> {agent_id}
  - POST /v3/agents/{agent_id}/execute        invoke an agent with a query (Agent API)
  - POST /v3/workflows/                       register a multi-agent workflow (Manager/Orchestration)
  - POST /v3/workflows/run                    execute a registered workflow (DAG orchestration)

Auth is provided via the `x-api-key` header (Lyzr v3 API key).
"""
import uuid
import httpx
import datetime
from typing import Dict, Any, Optional, List, Callable

from app.core.config import settings

LYZR_BASE_URL = getattr(settings, "LYZR_BASE_URL", None) or "https://agent-prod.studio.lyzr.ai"

_is_placeholder = lambda k: not (k and k.strip())


def lyzr_configured() -> bool:
    """True when a Lyzr API key is supplied via env/.env (any non-empty value)."""
    return bool(settings.LYZR_API_KEY and settings.LYZR_API_KEY.strip())


class LyzrClientError(Exception):
    pass


class LyzrClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.LYZR_API_KEY
        self.base_url = (base_url or LYZR_BASE_URL).rstrip("/")

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------
    async def _post(self, path: str, payload: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{self.base_url}{path}", json=payload, headers=headers)
        if resp.status_code >= 400:
            raise LyzrClientError(f"Lyzr API {path} -> {resp.status_code}: {resp.text[:300]}")
        try:
            return resp.json()
        except Exception:
            return {"raw": resp.text}

    # ------------------------------------------------------------------
    # Agent lifecycle
    # ------------------------------------------------------------------
    async def create_agent(
        self,
        name: str,
        agent_role: str,
        agent_instructions: str,
        agent_goal: str = "",
        agent_context: str = "",
        agent_output: str = "Provide a concise, actionable markdown summary.",
        provider_id: str = "openai",
        model: str = "gpt-4o-mini",
        temperature: float = 0.5,
        top_p: float = 0.9,
    ) -> str:
        """Creates a Lyzr agent and returns its agent_id."""
        payload = {
            "name": name,
            "description": agent_role,
            "agent_role": agent_role,
            "agent_instructions": agent_instructions,
            "agent_goal": agent_goal or agent_role,
            "agent_context": agent_context,
            "agent_output": agent_output,
            "provider_id": provider_id,
            "model": model,
            "temperature": temperature,
            "top_p": top_p,
            "store_messages": True,
        }
        data = await self._post("/v3/agents/", payload)
        agent_id = data.get("agent_id") or data.get("id")
        if not agent_id:
            raise LyzrClientError(f"Lyzr create_agent returned no agent_id: {data}")
        return agent_id

    async def invoke_agent(self, agent_id: str, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Invokes a single agent by ID with a query (Lyzr inference endpoint)."""
        payload: Dict[str, Any] = {
            "messages": [{"role": "user", "content": query}],
        }
        if session_id:
            payload["session_id"] = session_id
        return await self._post(f"/v3/inference/{agent_id}/generate_response/", payload, timeout=120.0)

    # ------------------------------------------------------------------
    # Manager / orchestration
    # ------------------------------------------------------------------
    async def run_dag_workflow(
        self,
        flow_name: str,
        run_name: str,
        tasks: List[Dict[str, Any]],
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes a multi-agent workflow (DAG) on Lyzr. `tasks` is a list of task nodes
        referencing agent ids, matching the Lyzr run-dag workflow_data schema.
        """
        payload = {
            "workflow_data": {
                "tasks": tasks,
                "flow_name": flow_name,
                "run_name": run_name,
                "default_inputs": {},
                "edges": [],
            },
            "inputs": inputs or {},
        }
        return await self._post("/v3/workflows/run", payload)

    async def manager_agent(
        self,
        manager_agent_id: str,
        query: str,
        managed_agents: List[Dict[str, str]],
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sends a query to a Lyzr Manager Agent, providing the `managed_agents` array so it
        can route subtasks to specialist sub-agents. This is the primary mechanism for
        'supervisor delegates to specialized division' orchestration.
        """
        payload: Dict[str, Any] = {
            "messages": [{"role": "user", "content": query}],
            "managed_agents": managed_agents,
        }
        if session_id:
            payload["session_id"] = session_id
        return await self._post(f"/v3/inference/{manager_agent_id}/generate_response/", payload, timeout=120.0)


lyzr_client = LyzrClient()