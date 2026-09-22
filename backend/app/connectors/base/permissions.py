"""
Connector-level permission model.
"""
from typing import List, Optional

from .schemas import ConnectorPermission, RiskClass


class PermissionSet:
    """Represents the effective read/propose/execute permissions of a connector."""

    def __init__(self, permissions=None, allowed_agents: Optional[List[str]] = None):
        perms = permissions or {}
        self.read = bool(perms.get("read", True))
        self.propose = bool(perms.get("propose", False))
        self.execute = bool(perms.get("execute", False))
        self.allowed_agents: List[str] = allowed_agents or []
        self.risk_class = _infer_risk_class(perms)

    def allows(self, permission: str) -> bool:
        mapping = {
            ConnectorPermission.READ.value: self.read,
            ConnectorPermission.PROPOSE.value: self.propose,
            ConnectorPermission.EXECUTE.value: self.execute,
        }
        return bool(mapping.get(permission, False))

    def agent_allowed(self, agent_id: str) -> bool:
        """Allows all agents when allowed_agents is empty, otherwise restricts."""
        return (not self.allowed_agents) or (agent_id in self.allowed_agents)

    def to_dict(self) -> dict:
        return {"read": self.read, "propose": self.propose, "execute": self.execute,
                "allowed_agents": self.allowed_agents, "risk_class": self.risk_class.value}


def _infer_risk_class(perms) -> RiskClass:
    if bool(perms.get("execute", False)):
        return RiskClass.HIGH
    if bool(perms.get("propose", False)):
        return RiskClass.MEDIUM
    return RiskClass.LOW