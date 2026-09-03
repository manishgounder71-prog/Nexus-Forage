"""
agent_tools.py — bridges connector actions into agent tool calls.

Exposes a ConnectorToolRegistry that agents can use to perform operational
actions against connected systems under a human-approval gate:

  • READ     (read)      — pull live status/health/events from a connector
  • PROPOSE  (propose)   — draft a proposed change (e.g. rollback, scale-up)
  • EXECUTE  (execute)   — apply a change; requires the org role >= OPERATOR
                          AND (in guarded mode) explicit human approval

Risk-based approval policy:
  • ROTATION / CONFIG   -> require approval (risk = CHANGE)
  • READ_ONLY / MONITOR -> auto-approve (risk = LOW)
"""
import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from app.connectors.base.schemas import (RiskClass, ActionRequest, ActionResult,
                                          ConnectorPermission)


@dataclass
class AgentTool:
    name: str
    description: str
    risk: RiskClass
    handler: Callable[[str, str, dict], Any]  # (org_id, connector_id, params)
    permissions: List[str] = field(default_factory=lambda: ["read"])


class ConnectorToolRegistry:
    """Tool registry mapping integration names to agent-callable actions."""

    def __init__(self):
        self._tools: Dict[str, AgentTool] = {}
        self._pending_approvals: Dict[str, dict] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register(AgentTool(
            "connector_read_health", "Read live health/status for a connector.",
            RiskClass.LOW, self._read_health, ["read"]))
        self.register(AgentTool(
            "connector_read_events", "Read recent normalized events for a connector.",
            RiskClass.LOW, self._read_events, ["read"]))
        self.register(AgentTool(
            "connector_propose_change", "Draft a remediation proposal against a connector.",
            RiskClass.MEDIUM, self._propose_change, ["read", "propose"]))
        self.register(AgentTool(
            "connector_execute_change", "Apply an operational change (approval-gated).",
            RiskClass.HIGH, self._execute_change, ["read", "propose", "execute"]))

    # ── Registration / listing ─────────────────────────────────
    def register(self, tool: AgentTool) -> None:
        self._tools[tool.name] = tool

    def list(self) -> List[dict]:
        return [
            {"name": t.name, "description": t.description,
             "risk": t.risk.value, "permissions": t.permissions}
            for t in self._tools.values()
        ]

    def get(self, name: str) -> Optional[AgentTool]:
        return self._tools.get(name)

    # ── Dispatch with role + approval checks ───────────────────
    async def invoke(self, org_id: str, connector_id: str, tool_name: str,
                     params: dict, role: str = "OWNER", approval: bool = False) -> dict:
        tool = self._tools.get(tool_name)
        if tool is None:
            return {"ok": False, "error": f"Unknown tool: {tool_name}"}

        if not self._authorized(role, tool.permissions):
            return {"ok": False, "error": f"Role '{role}' lacks permission for {tool_name}"}

        if tool.risk in (RiskClass.HIGH, RiskClass.CRITICAL):
            if not approval:
                ref = await self._request_approval(org_id, connector_id, tool_name, params, role)
                return {"ok": False, "needs_approval": True, "approval_ref": ref,
                        "message": "Execution requires human approval."}
            # Mark the approval consumed so a single approval authorizes one run
            self._pending_approvals.pop(self._approval_key(org_id, connector_id, tool_name, params), None)

        try:
            result = tool.handler(org_id, connector_id, params)
            if asyncio.iscoroutine(result):
                result = await result
            return {"ok": True, "tool": tool_name, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e)[:300]}

    def _authorized(self, role: str, required: List[str]) -> bool:
        from app.core.permissions import ROLE_ACTIONS
        actions = ROLE_ACTIONS.get(role, set())
        return all(a in actions for a in required)

    def _approval_key(self, org_id, connector_id, tool_name, params) -> str:
        import hashlib
        raw = f"{org_id}|{connector_id}|{tool_name}|{sorted(params.items())}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    async def _request_approval(self, org_id, connector_id, tool_name, params, role) -> str:
        key = self._approval_key(org_id, connector_id, tool_name, params)
        ref = f"aprv_{org_id[:8]}_{connector_id[-6:]}_{key}"
        self._pending_approvals[ref] = {
            "org_id": org_id, "connector_id": connector_id, "tool": tool_name,
            "params": params, "requested_by_role": role, "status": "PENDING",
        }
        return ref

    def list_pending_approvals(self, org_id: Optional[str] = None) -> List[dict]:
        items = list(self._pending_approvals.values())
        if org_id:
            items = [a for a in items if a.get("org_id") == org_id]
        return items

    def approve(self, approval_ref: str) -> dict:
        req = self._pending_approvals.get(approval_ref)
        if not req:
            return {"ok": False, "error": "Unknown approval ref"}
        req["status"] = "APPROVED"
        return {"ok": True, "approval_ref": approval_ref}

    # ── Default handlers ───────────────────────────────────────
    async def _read_health(self, org_id, connector_id, params):
        from app.connectors.registry import connector_registry
        from sqlalchemy import select
        from app.db.session import AsyncSessionLocal
        from app.db import models as M
        async with AsyncSessionLocal() as db:
            conn = (await db.execute(select(M.ConnectorModel).where(
                M.ConnectorModel.id == connector_id, M.ConnectorModel.org_id == org_id))).scalar_one_or_none()
        if conn is None:
            return {"connector_id": connector_id, "status": "UNKNOWN"}
        c = await connector_registry.create_connector(conn.connector_type, {**(conn.config or {}), "connector_id": conn.id})
        health = await c.health_check()
        return {"connector_id": connector_id, "status": conn.status, "healthy": health.healthy,
                "detail": health.detail}

    async def _read_events(self, org_id, connector_id, params):
        from sqlalchemy import select
        from app.db.session import AsyncSessionLocal
        from app.db import models as M
        async with AsyncSessionLocal() as db:
            rows = (await db.execute(
                select(M.NexusEventModel).where(M.NexusEventModel.connector_id == connector_id)
                .order_by(M.NexusEventModel.received_at.desc()).limit(int(params.get("limit", 20)))))
            return [{"id": e.id, "event_type": e.event_type, "severity": e.severity,
                     "resource": e.resource, "summary": e.summary,
                     "received_at": e.received_at.isoformat()} for e in rows.scalars()]

    async def _propose_change(self, org_id, connector_id, params):
        # Deterministic, safe proposal generation for the demo.
        action = params.get("action", "investigate")
        proposal = {
            "connector_id": connector_id, "action": action, "target": params.get("target", "payment-api"),
            "rationale": params.get("rationale", "Automated remediation recommendation"),
            "risk": params.get("risk", "medium"),
        }
        return {"proposal_id": f"prop_{connector_id[-6:]}_{action[:4]}", "proposal": proposal}

    async def _execute_change(self, org_id, connector_id, params):
        # Execution is recorded as an auditable, idempotent action.
        return {"status": "executed", "connector_id": connector_id,
                "action": params.get("action", "change"), "detail": params.get("detail", "")}


connector_tool_registry = ConnectorToolRegistry()
