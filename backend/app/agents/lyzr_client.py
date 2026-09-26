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
import hashlib
import httpx
import datetime
from typing import Dict, Any, Optional, List, Callable

from app.core.config import settings
from app.core.costing import usage_register, UsageRecord, estimate_tokens, truncate_tokens
from app.core.caching import llm_cache
from app.core.prompt_guard import (
    sanitize_untrusted_input,
    build_grounding_system_prompt,
    apply_no_fabrication_directive,
)

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
        self._shared_client: Optional[httpx.AsyncClient] = None

    def _client(self) -> httpx.AsyncClient:
        """Returns a lazily-created, reused AsyncClient (no per-request session churn)."""
        if self._shared_client is None or self._shared_client.is_closed:
            self._shared_client = httpx.AsyncClient(timeout=30.0)
        return self._shared_client

    def _record_usage(self, model: str, prompt_text: str, completion_text: str, source: str) -> None:
        """Records deterministic token/cost estimates for one Lyzr call."""
        usage_register.record(UsageRecord(
            model=model,
            prompt_tokens=estimate_tokens(prompt_text),
            completion_tokens=estimate_tokens(completion_text),
            source=source,
        ))

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------
    async def _get(self, path: str, timeout: float = 30.0) -> Dict[str, Any]:
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        async with self._client() as client:
            resp = await client.get(f"{self.base_url}{path}", headers=headers)
        if resp.status_code >= 400:
            raise LyzrClientError(f"Lyzr API {path} -> {resp.status_code}: {resp.text[:300]}")
        try:
            return resp.json()
        except Exception:
            return {"raw": resp.text}

    async def _post(self, path: str, payload: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        async with self._client() as client:
            resp = await client.post(f"{self.base_url}{path}", json=payload, headers=headers)
        if resp.status_code >= 400:
            raise LyzrClientError(f"Lyzr API {path} -> {resp.status_code}: {resp.text[:300]}")
        try:
            return resp.json()
        except Exception:
            return {"raw": resp.text}

    # ------------------------------------------------------------------
    # Agent lookup
    # ------------------------------------------------------------------
    async def find_agent_by_name(self, name: str) -> Optional[str]:
        """Returns the agent_id of the first agent whose name matches, or None."""
        if not name:
            return None
        resp = await self._get("/v3/agents/")
        agents = resp if isinstance(resp, list) else resp.get("agents") or resp.get("data") or []
        for a in agents:
            if a.get("name") == name:
                aid = a.get("_id") or a.get("id") or a.get("agent_id")
                if aid:
                    return aid
        return None

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

    async def invoke_agent(
        self,
        agent_id: str,
        query: str,
        session_id: Optional[str] = None,
        context: Optional[str] = None,
        max_tokens: int = 700,
    ) -> Dict[str, Any]:
        """Invokes a single agent by ID with a query (Lyzr inference endpoint).

        `context` is real retrieved evidence (e.g. Qdrant memory excerpts) injected
        as a grounding message so the LLM is anchored to known facts rather than left
        to fabricate. `max_tokens` bounds spend per call (Pillar 01/02/04).

        The query is treated as DATA (sanitized/escaped into delimited blocks) and a
        no-fabrication contract is appended. Responses are TTL-cached by deterministic
        key (Pillar 05/04).
        """
        safe = sanitize_untrusted_input(query)
        user_text = apply_no_fabrication_directive(safe["raw_text"])
        cache_part = context or ""
        cache_key_parts = (agent_id, hashlib.sha256(cache_part.encode("utf-8")).hexdigest(), user_text[:500])

        cached = llm_cache.get("lyzr_invoke", *cache_key_parts)
        if cached is not None:
            return cached

        messages: List[Dict[str, str]] = []
        if cache_part:
            grounded_context = truncate_tokens(cache_part, settings.MAX_CONTEXT_TOKENS if hasattr(settings, "MAX_CONTEXT_TOKENS") else 1200)
            messages.append({
                "role": "system",
                "content": build_grounding_system_prompt(grounded_context),
            })
        messages.append({"role": "user", "content": user_text})
        payload: Dict[str, Any] = {
            "messages": messages,
            "max_tokens": min(int(max_tokens or 700), settings.MAX_RESPONSE_TOKENS if hasattr(settings, "MAX_RESPONSE_TOKENS") else 700),
        }
        if session_id:
            payload["session_id"] = session_id
        result = await self._post(f"/v3/inference/{agent_id}/generate_response/", payload, timeout=120.0)

        prompt_text = "\n".join(m["content"] for m in messages)
        completion_text = ""
        for key in ("answer", "output", "response", "content"):
            val = result.get(key)
            if isinstance(val, str):
                completion_text = val
                break
        self._record_usage("gpt-4o-mini", prompt_text, completion_text, source="lyzr_live")
        llm_cache.set("lyzr_invoke", result, *cache_key_parts)
        return result

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
        safe = sanitize_untrusted_input(query)
        payload: Dict[str, Any] = {
            "messages": [{"role": "user", "content": apply_no_fabrication_directive(safe["raw_text"])}],
            "managed_agents": managed_agents,
        }
        if session_id:
            payload["session_id"] = session_id
        result = await self._post(f"/v3/inference/{manager_agent_id}/generate_response/", payload, timeout=120.0)
        self._record_usage("gpt-4o", query, str(result), source="lyzr_manager")
        return result


lyzr_client = LyzrClient()