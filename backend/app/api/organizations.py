"""
organizations.py — Organization REST API for NEXUS CONNECT.

Implements standard multi-tenant endpoints:
  • POST /organizations
  • GET  /organizations
  • GET  /organizations/{id}
  • POST /organizations/{id}/endpoint
  • GET  /organizations/{id}/connectors
  • POST /organizations/{id}/connectors
  • GET  /organizations/{id}/connectors/{connector_id}
  • POST /organizations/{id}/connectors/{connector_id}/test
  • POST /organizations/{id}/connectors/{connector_id}/disconnect
  • GET  /organizations/{id}/events
  • GET  /organizations/{id}/incidents
  • GET  /organizations/{id}/incidents/{incident_id}
  • GET  /organizations/{id}/missions
  • GET  /organizations/{id}/approvals
  • POST /organizations/{id}/approvals/{approval_id}/approve
  • POST /organizations/{id}/approvals/{approval_id}/reject
  • GET  /organizations/{id}/dashboard
  • GET  /organizations/{id}/audit-logs
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.policy_engine import action_policy_engine
from app.connectors.registry import connector_registry
from app.core.permissions import require_role
from app.core.security import (
    encrypt_credential,
    generate_ingestion_secret,
    generate_public_org_id,
    hash_webhook_token,
)
from app.db import models as M
from app.db.session import get_db
from app.pipeline.ingestion import incident_store

router = APIRouter(prefix="/organizations", tags=["Organizations"])


# ── Schemas ─────────────────────────────────────────────────────
class CreateOrganizationRequest(BaseModel):
    name: str
    industry: Optional[str] = "technology"
    description: Optional[str] = ""
    timezone: Optional[str] = "UTC"
    org_type: Optional[str] = "enterprise"
    rate_limit: Optional[int] = 100


class CreateConnectorRequest(BaseModel):
    connector_type: str
    name: str
    description: Optional[str] = ""
    config: Dict[str, Any] = Field(default_factory=dict)
    permissions: Dict[str, bool] = Field(
        default_factory=lambda: {"read": True, "propose": True, "execute": False}
    )
    allowed_agents: List[str] = Field(default_factory=list)
    allowed_event_types: List[str] = Field(default_factory=list)


class ApprovalActionRequest(BaseModel):
    reason: Optional[str] = ""


# ── Organization Lifecycle ──────────────────────────────────────
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_organization(req: CreateOrganizationRequest, db: AsyncSession = Depends(get_db)):
    """Creates a new workspace with automatic public ID, ingestion secret, and default policies."""
    slug = req.name.lower().replace(" ", "-").replace("_", "-")[:30]
    org_id = f"org_{slug}_{uuid.uuid4().hex[:6]}"
    public_id = generate_public_org_id(slug)
    raw_secret = generate_ingestion_secret()

    org = M.OrganizationModel(
        id=org_id,
        public_id=public_id,
        name=req.name,
        slug=f"{slug}-{uuid.uuid4().hex[:4]}",
        org_type=req.org_type or "enterprise",
        status="ACTIVE",
        settings={
            "industry": req.industry,
            "description": req.description,
            "timezone": req.timezone,
            "ingestion_secret": encrypt_credential(raw_secret),
        },
        ingestion_secret_hash=raw_secret,
    )
    db.add(org)

    # Initialize default policy
    policy = M.OrganizationPolicyModel(
        id=f"pol_{uuid.uuid4().hex[:8]}",
        org_id=org_id,
        rate_limit_per_minute=req.rate_limit or 100,
        timestamp_tolerance_seconds=300,
        auto_approval_risk_threshold="MEDIUM",
        crisis_confidence_threshold=0.85,
    )
    db.add(policy)

    # Add default OWNER user
    owner = M.OrgUserModel(
        id=f"usr_{uuid.uuid4().hex[:8]}",
        org_id=org_id,
        username=f"admin@{slug}.com",
        role="OWNER",
    )
    db.add(owner)

    # Seed default Webhook connector
    webhook_conn = M.ConnectorModel(
        id=f"conn_{org_id[:12]}_webhook_{uuid.uuid4().hex[:6]}",
        org_id=org_id,
        connector_type="webhook",
        name="Universal Webhook Ingest",
        description="Zero-code ingestion adapter for custom APIs, alerts, and webhooks.",
        status="CONNECTED",
        enabled=True,
        webhook_url=f"/api/v1/ingest/{public_id}",
    )
    db.add(webhook_conn)

    # Audit log
    audit = M.AuditLogModel(
        org_id=org_id,
        actor="SYSTEM",
        action="organization_created",
        resource_type="organization",
        resource_id=org_id,
        details={"name": req.name, "public_id": public_id},
    )
    db.add(audit)

    await db.commit()

    return {
        "status": "created",
        "organization": {
            "id": org.id,
            "public_id": public_id,
            "name": org.name,
            "slug": org.slug,
            "ingestion_endpoint": f"/api/v1/ingest/{public_id}",
            "authentication": "HMAC_SHA256",
            "ingestion_secret": raw_secret,  # Shown ONCE
            "created_at": org.created_at.isoformat(),
        },
    }


@router.get("")
async def list_organizations(db: AsyncSession = Depends(get_db)):
    """Lists all active organizations."""
    rows = (await db.execute(select(M.OrganizationModel))).scalars().all()
    return {
        "organizations": [
            {
                "id": o.id,
                "public_id": o.public_id or o.id,
                "name": o.name,
                "slug": o.slug,
                "org_type": o.org_type,
                "status": o.status,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in rows
        ],
        "count": len(rows),
    }


@router.get("/{id}")
async def get_organization(id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves organization details."""
    org = (
        await db.execute(
            select(M.OrganizationModel).where((M.OrganizationModel.id == id) | (M.OrganizationModel.public_id == id))
        )
    ).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return {
        "id": org.id,
        "public_id": org.public_id or org.id,
        "name": org.name,
        "slug": org.slug,
        "status": org.status,
        "settings": org.settings or {},
        "created_at": org.created_at.isoformat() if org.created_at else None,
    }


@router.post("/{id}/endpoint")
async def generate_ingestion_endpoint(id: str, db: AsyncSession = Depends(get_db)):
    """Generates or rotates a secure public ingestion endpoint & HMAC secret."""
    org = (
        await db.execute(select(M.OrganizationModel).where(M.OrganizationModel.id == id))
    ).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    new_public_id = generate_public_org_id(org.slug)
    new_secret = generate_ingestion_secret()

    org.public_id = new_public_id
    org.ingestion_secret_hash = new_secret
    if org.settings is None:
        org.settings = {}
    org.settings["ingestion_secret"] = encrypt_credential(new_secret)

    await db.commit()

    return {
        "status": "active",
        "public_id": new_public_id,
        "endpoint": f"/api/v1/ingest/{new_public_id}",
        "authentication": "HMAC_SHA256",
        "secret": new_secret,  # Displayed once upon rotation
    }


# ── Connectors ──────────────────────────────────────────────────
@router.get("/{id}/connectors")
async def list_organization_connectors(id: str, db: AsyncSession = Depends(get_db)):
    """Lists connectors belonging strictly to this organization."""
    rows = (
        await db.execute(select(M.ConnectorModel).where(M.ConnectorModel.org_id == id))
    ).scalars().all()
    return {
        "connectors": [
            {
                "id": c.id,
                "connector_type": c.connector_type,
                "name": c.name,
                "description": c.description,
                "status": c.status,
                "enabled": c.enabled,
                "events_count": c.events_count,
                "failed_events": c.failed_events,
                "last_event_at": c.last_event_at.isoformat() if c.last_event_at else None,
                "permissions": c.permissions,
                "webhook_url": c.webhook_url,
            }
            for c in rows
        ],
        "count": len(rows),
    }


@router.post("/{id}/connectors")
async def create_organization_connector(
    id: str, req: CreateConnectorRequest, db: AsyncSession = Depends(get_db)
):
    """Registers a new connector for this organization."""
    if not connector_registry.validate_type(req.connector_type):
        raise HTTPException(status_code=400, detail=f"Unknown connector type: {req.connector_type}")

    cid = f"conn_{id[:12]}_{req.connector_type}_{uuid.uuid4().hex[:6]}"
    webhook_url = f"/api/v1/platform/orgs/{id}/connectors/{cid}/webhook"

    conn = M.ConnectorModel(
        id=cid,
        org_id=id,
        connector_type=req.connector_type,
        name=req.name,
        description=req.description or "",
        config=req.config,
        status="CONNECTED",
        enabled=True,
        permissions=req.permissions,
        allowed_agents=req.allowed_agents,
        allowed_event_types=req.allowed_event_types,
        webhook_url=webhook_url,
    )
    db.add(conn)
    await db.commit()

    return {
        "status": "connected",
        "connector_id": cid,
        "name": req.name,
        "connector_type": req.connector_type,
        "webhook_url": webhook_url,
    }


@router.get("/{id}/connectors/{connector_id}")
async def get_connector_details(id: str, connector_id: str, db: AsyncSession = Depends(get_db)):
    conn = (
        await db.execute(
            select(M.ConnectorModel).where(
                M.ConnectorModel.id == connector_id, M.ConnectorModel.org_id == id
            )
        )
    ).scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="Connector not found")
    return {
        "id": conn.id,
        "connector_type": conn.connector_type,
        "name": conn.name,
        "status": conn.status,
        "enabled": conn.enabled,
        "permissions": conn.permissions,
        "events_count": conn.events_count,
        "webhook_url": conn.webhook_url,
    }


@router.post("/{id}/connectors/{connector_id}/test")
async def test_connector(id: str, connector_id: str, db: AsyncSession = Depends(get_db)):
    conn = (
        await db.execute(
            select(M.ConnectorModel).where(
                M.ConnectorModel.id == connector_id, M.ConnectorModel.org_id == id
            )
        )
    ).scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="Connector not found")

    c = await connector_registry.create_connector(
        conn.connector_type, {**(conn.config or {}), "connector_id": conn.id}
    )
    health = await c.health_check()
    return {
        "healthy": health.healthy,
        "status": health.status,
        "latency_ms": health.latency_ms,
        "detail": health.detail,
    }


@router.post("/{id}/connectors/{connector_id}/disconnect")
async def disconnect_connector(id: str, connector_id: str, db: AsyncSession = Depends(get_db)):
    conn = (
        await db.execute(
            select(M.ConnectorModel).where(
                M.ConnectorModel.id == connector_id, M.ConnectorModel.org_id == id
            )
        )
    ).scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="Connector not found")

    conn.status = "DISCONNECTED"
    conn.enabled = False
    await db.commit()
    return {"status": "disconnected", "connector_id": connector_id}


# ── Events & Incidents ──────────────────────────────────────────
@router.get("/{id}/events")
async def list_organization_events(
    id: str, limit: int = Query(50, le=500), db: AsyncSession = Depends(get_db)
):
    rows = (
        await db.execute(
            select(M.NexusEventModel)
            .where(M.NexusEventModel.org_id == id)
            .order_by(M.NexusEventModel.received_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return {
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "severity": e.severity,
                "resource": e.resource,
                "summary": e.summary,
                "received_at": e.received_at.isoformat() if e.received_at else None,
            }
            for e in rows
        ],
        "count": len(rows),
    }


@router.get("/{id}/incidents")
async def list_organization_incidents(id: str, db: AsyncSession = Depends(get_db)):
    incidents = await incident_store.list(id)
    return {"incidents": incidents, "count": len(incidents)}


@router.get("/{id}/incidents/{incident_id}")
async def get_organization_incident(id: str, incident_id: str, db: AsyncSession = Depends(get_db)):
    inc = await incident_store.get(incident_id)
    if not inc or inc.get("org_id") != id:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"incident": inc}


@router.get("/{id}/missions")
async def list_organization_missions(id: str, db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(M.MissionModel)
            .where(M.MissionModel.org_id == id)
            .order_by(M.MissionModel.created_at.desc())
        )
    ).scalars().all()
    return {
        "missions": [
            {
                "id": m.id,
                "title": m.title,
                "status": m.status,
                "severity": m.severity,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in rows
        ],
        "count": len(rows),
    }


# ── Human Approvals ─────────────────────────────────────────────
@router.get("/{id}/approvals")
async def list_organization_approvals(
    id: str, status_filter: Optional[str] = Query(None, alias="status")
):
    approvals = await action_policy_engine.list_approvals(id, status_filter)
    return {"approvals": approvals, "count": len(approvals)}


@router.post("/{id}/approvals/{approval_id}/approve")
async def approve_organization_action(id: str, approval_id: str):
    res = await action_policy_engine.approve_and_execute(
        approval_id=approval_id, reviewer="OPERATOR", reviewer_role="OPERATOR"
    )
    if not res.get("ok"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res


@router.post("/{id}/approvals/{approval_id}/reject")
async def reject_organization_action(id: str, approval_id: str, req: ApprovalActionRequest):
    res = await action_policy_engine.reject(
        approval_id=approval_id, reviewer="OPERATOR", reason=req.reason or "Operator rejected"
    )
    if not res.get("ok"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res


# ── Dashboard & Audit ───────────────────────────────────────────
@router.get("/{id}/dashboard")
async def get_organization_dashboard(id: str, db: AsyncSession = Depends(get_db)):
    """Aggregates telemetry and status for the Organization Command Center."""
    conns = (
        await db.execute(select(M.ConnectorModel).where(M.ConnectorModel.org_id == id))
    ).scalars().all()
    events_count = len(
        (await db.execute(select(M.NexusEventModel.id).where(M.NexusEventModel.org_id == id))).scalars().all()
    )
    incidents = await incident_store.list(id)
    active_incidents = len([i for i in incidents if i.get("status") != "RESOLVED"])
    pending_approvals = len(await action_policy_engine.list_approvals(id, status_filter="PENDING"))
    missions_count = len(
        (await db.execute(select(M.MissionModel.id).where(M.MissionModel.org_id == id))).scalars().all()
    )

    return {
        "organization_id": id,
        "connected_systems": len(conns),
        "healthy_systems": len([c for c in conns if c.status == "CONNECTED"]),
        "degraded_systems": len([c for c in conns if c.status != "CONNECTED"]),
        "events_today": events_count,
        "active_incidents": active_incidents,
        "ai_missions": missions_count,
        "pending_approvals": pending_approvals,
    }


@router.get("/{id}/audit-logs")
async def list_organization_audit_logs(
    id: str, limit: int = Query(100, le=500), db: AsyncSession = Depends(get_db)
):
    rows = (
        await db.execute(
            select(M.AuditLogModel)
            .where(M.AuditLogModel.org_id == id)
            .order_by(M.AuditLogModel.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()

    return {
        "audit_logs": [
            {
                "id": a.id,
                "actor": a.actor,
                "action": a.action,
                "resource_type": a.resource_type,
                "resource_id": a.resource_id,
                "details": a.details,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in rows
        ],
        "count": len(rows),
    }
