"""
RBAC permission model for the Connector Platform.

Role hierarchy (most -> least privileged):
  OWNER > ADMIN > OPERATOR > ANALYST > VIEWER

Each role maps to a set of resource actions. `check_permission()` and
`require_role()` are used as FastAPI dependencies on org endpoints.
"""
from typing import Optional
from fastapi import Depends, HTTPException, Header, status

from app.core.security import verify_webhook_token
from app.db.session import get_db
from app.db.models import OrgUserModel, OrganizationModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Resource action vocabulary
READ = "read"
PROPOSE = "propose"
EXECUTE = "execute"

ROLE_HIERARCHY = ["VIEWER", "ANALYST", "OPERATOR", "ADMIN", "OWNER"]

ROLE_ACTIONS = {
    "VIEWER": {READ},
    "ANALYST": {READ, PROPOSE},
    "OPERATOR": {READ, PROPOSE, EXECUTE},
    "ADMIN": {READ, PROPOSE, EXECUTE, "admin", "manage"},
    "OWNER": {READ, PROPOSE, EXECUTE, "admin", "manage"},
}


def role_rank(role: str) -> int:
    return ROLE_HIERARCHY.index(role) if role in ROLE_HIERARCHY else -1


def check_permission(role: str, required_action: str) -> bool:
    if role_rank(role) < 0:
        return False
    return required_action in ROLE_ACTIONS.get(role, set())


class _RequireAction:
    def __init__(self, action: str):
        self.action = action

    async def __call__(
        self,
        org_id: str,
        x_org_api_key: Optional[str] = Header(None, alias="X-Org-API-Key"),
        db: AsyncSession = Depends(get_db),
    ) -> "ResolvedPrincipal":
        principal = await resolve_principal(org_id, x_org_api_key, db)
        if not check_permission(principal.role, self.action):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return principal


class _RequireRole:
    def __init__(self, min_role: str):
        self.min_role = min_role

    async def __call__(
        self,
        org_id: str,
        x_org_api_key: Optional[str] = Header(None, alias="X-Org-API-Key"),
        db: AsyncSession = Depends(get_db),
    ) -> "ResolvedPrincipal":
        principal = await resolve_principal(org_id, x_org_api_key, db)
        if role_rank(principal.role) < role_rank(self.min_role):
            raise HTTPException(status_code=403, detail=f"Requires role >= {self.min_role}")
        return principal


def require_action(action: str) -> _RequireAction:
    """Dependency factory requiring a specific resource action on an org."""
    return _RequireAction(action)


def require_role(min_role: str) -> _RequireRole:
    """Dependency factory requiring at least a given role on an org."""
    return _RequireRole(min_role)


async def resolve_principal(org_id: str, api_key: Optional[str], db: AsyncSession) -> "ResolvedPrincipal":
    """Resolves an org + api key to a resolved principal (actor + role)."""
    org = (await db.execute(select(OrganizationModel).where(OrganizationModel.id == org_id))).scalar_one_or_none()
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    if org.status != "ACTIVE":
        raise HTTPException(status_code=403, detail=f"Organization is {org.status}")

    if api_key:
        users = (await db.execute(select(OrgUserModel).where(OrgUserModel.org_id == org_id))).scalars().all()
        for u in users:
            if u.api_key_hash and verify_webhook_token(api_key, u.api_key_hash):
                return ResolvedPrincipal(org_id=org_id, actor=f"user:{u.id}", role=u.role, org=org)
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Demo/no-auth fallback: treat as OWNER so the demo flow works without login.
    return ResolvedPrincipal(org_id=org_id, actor="system", role="OWNER", org=org)


class ResolvedPrincipal:
    __slots__ = ("org_id", "actor", "role", "org")

    def __init__(self, org_id: str, actor: str, role: str, org):
        self.org_id = org_id
        self.actor = actor
        self.role = role
        self.org = org


def audit_action(actor: str, action: str, resource_type: Optional[str], resource_id: Optional[str],
                 details: Optional[dict] = None) -> dict:
    """Builds an AuditLogModel-compatible dict. Callers persist it against org_id."""
    return {
        "actor": actor,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details or {},
        "created_at": get_current_timestamp(),
    }