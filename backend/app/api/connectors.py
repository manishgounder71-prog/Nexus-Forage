"""
connectors.py — REST API for the Organization Connector Platform.

Endpoints:
  • GET  /platform/catalog                  — discoverable connector catalog
  • POST /platform/orgs                     — create an organization
  • GET  /platform/orgs                     — list organizations
  • POST /platform/orgs/{org_id}/users      — provision an org user (API key)
  • POST /platform/orgs/{org_id}/connectors — register a connector
  • GET  /platform/orgs/{org_id}/connectors
  • POST /platform/orgs/{org_id}/connectors/{cid}/webhook  — ingest a payload
  • GET  /platform/orgs/{org_id}/events
  • GET  /platform/orgs/{org_id}/incidents
  • POST /platform/orgs/{org_id}/incidents/{iid}/command   — command center
  • GET  /platform/orgs/{org_id}/audit
  • POST /platform/demo/crisis              — launch the demo crisis sequence
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_role, require_action
from app.connectors.registry import connector_registry
from app.core.config import settings
from app.db import models as M
from app.db.session import get_db
from app.pipeline.ingestion import event_ingestion_pipeline, incident_store

router = APIRouter(prefix="/platform", tags=["Connector Platform"])


# ── Request/Response schemas ────────────────────────────────────
class CreateOrgRequest(BaseModel):
    name: str
    slug: str
    org_type: str = "startup"


class ProvisionUserRequest(BaseModel):
    username: str
    email: Optional[str] = None
    role: str = "ANALYST"


class RegisterConnectorRequest(BaseModel):
    connector_type: str
    name: str
    description: str = ""
    config: Dict[str, Any] = Field(default_factory=dict)
    permissions: Dict[str, bool] = Field(default_factory=lambda: {"read": True, "propose": True, "execute": False})
    allowed_agents: List[str] = Field(default_factory=list)
    allowed_event_types: List[str] = Field(default_factory=list)


class CommandRequest(BaseModel):
    action: str = Field(description="e.g. escalate, dismiss, resolve, run_mission")
    payload: Dict[str, Any] = Field(default_factory=dict)


class WebhookEnvelope(BaseModel):
    payload: Dict[str, Any] = Field(description="The raw connector event body")


class DemoTarget(BaseModel):
    org_id: str = settings.DEMO_ORG_ID


# ── Catalog ─────────────────────────────────────────────────────
@router.get("/catalog")
async def get_catalog():
    items = connector_registry.catalog()
    return {"catalog": items, "count": len(items)}


# ── Organizations ───────────────────────────────────────────────
@router.post("/orgs")
async def create_org(req: CreateOrgRequest, db: AsyncSession = Depends(get_db)):
    org = M.OrganizationModel(id=f"org_{req.slug}", name=req.name, slug=req.slug,
                              org_type=req.org_type, status="ACTIVE")
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return {"status": "created", "org": {"id": org.id, "name": org.name, "slug": org.slug}}


@router.get("/orgs")
async def list_orgs(db: AsyncSession = Depends(get_db)):
    orgs = (await db.execute(select(M.OrganizationModel))).scalars().all()
    return {"orgs": [{"id": o.id, "name": o.name, "slug": o.slug, "status": o.status} for o in orgs]}


# ── Users / API key provisioning ────────────────────────────────
@router.post("/orgs/{org_id}/users", dependencies=[Depends(require_role("ADMIN"))])
async def provision_user(org_id: str, req: ProvisionUserRequest, db: AsyncSession = Depends(get_db),
                         principal=Depends(require_action("manage"))):
    from app.core.security import hash_webhook_token
    api_key = f"org_{org_id}_{uuid.uuid4().hex[:16]}"
    user = M.OrgUserModel(org_id=org_id, username=req.username, email=req.email, role=req.role,
                          api_key_hash=hash_webhook_token(api_key))
    db.add(user)
    await db.commit()
    await _write_audit(db, org_id, principal.actor, "user_provisioned", "org_user", user.id, {"role": req.role})
    return {"status": "provisioned", "user_id": user.id, "api_key": api_key}


# ── Connectors ──────────────────────────────────────────────────
@router.post("/orgs/{org_id}/connectors")
async def register_connector(org_id: str, req: RegisterConnectorRequest,
                             db: AsyncSession = Depends(get_db),
                             principal=Depends(require_role("OPERATOR"))):
    if not connector_registry.validate_type(req.connector_type):
        raise HTTPException(400, f"Unknown connector type: {req.connector_type}")

    from app.core.security import hash_webhook_token
    cid = f"conn_{org_id[:12]}_{uuid.uuid4().hex[:8]}"
    webhook_token = f"wh_{org_id}_{uuid.uuid4().hex[:16]}"
    webhook_url = f"/api/v1/platform/orgs/{org_id}/connectors/{cid}/webhook"

    config = dict(req.config)
    config.setdefault("webhook_url", webhook_url)

    conn = M.ConnectorModel(
        id=cid, org_id=org_id, connector_type=req.connector_type, name=req.name,
        description=req.description, config=config, status="CONNECTED", enabled=True,
        permissions=req.permissions, allowed_agents=req.allowed_agents,
        allowed_event_types=req.allowed_event_types,
        webhook_token_hash=hash_webhook_token(webhook_token), webhook_url=webhook_url,
    )
    db.add(conn)
    await db.commit()

    await _write_audit(db, org_id, principal.actor, "connector_connected", "connector", cid,
                       {"connector_type": req.connector_type})
    return {
        "status": "connected", "connector_id": cid, "webhook_url": webhook_url,
        "webhook_token": webhook_token,  # shown once
        "connector_type": req.connector_type,
    }


@router.get("/orgs/{org_id}/connectors")
async def list_connectors(org_id: str, db: AsyncSession = Depends(get_db),
                          principal=Depends(require_role("VIEWER"))):
    rows = (await db.execute(select(M.ConnectorModel).where(M.ConnectorModel.org_id == org_id))).scalars().all()
    return {"connectors": [
        {"id": c.id, "connector_type": c.connector_type, "name": c.name, "status": c.status,
         "enabled": c.enabled, "description": c.description, "events_count": c.events_count,
         "failed_events": c.failed_events,
         "last_event_at": c.last_event_at.isoformat() if c.last_event_at else None,
         "permissions": c.permissions, "webhook_url": c.webhook_url}
        for c in rows
    ], "count": len(rows)}


# ── Webhook ingestion ───────────────────────────────────────────
@router.post("/orgs/{org_id}/connectors/{cid}/webhook", dependencies=[Depends(require_role("VIEWER"))])
async def webhook_ingest(org_id: str, cid: str, envelope: WebhookEnvelope,
                         db: AsyncSession = Depends(get_db),
                         x_org_api_key: Optional[str] = Header(None, alias="X-Org-API-Key")):
    conn = (await db.execute(select(M.ConnectorModel).where(
        M.ConnectorModel.id == cid, M.ConnectorModel.org_id == org_id))).scalar_one_or_none()
    if conn is None:
        raise HTTPException(404, "Connector not found for org")
    if not conn.enabled:
        raise HTTPException(409, "Connector is disabled")

    allowlist = conn.allowed_event_types or None
    result = await event_ingestion_pipeline.ingest(
        org_id, cid, conn.connector_type, envelope.payload, conn.config or {}, allowlist,
    )
    await _write_audit(db, org_id, "system", "event_received", "event",
                       result.get("event", {}).get("dedupe_hash", ""), {"status": result.get("status")})
    return result


# ── Events ──────────────────────────────────────────────────────
@router.get("/orgs/{org_id}/events")
async def list_events(org_id: str, limit: int = Query(50, le=500), db: AsyncSession = Depends(get_db),
                      principal=Depends(require_role("VIEWER"))):
    rows = (await db.execute(
        select(M.NexusEventModel).where(M.NexusEventModel.org_id == org_id)
        .order_by(M.NexusEventModel.received_at.desc()).limit(limit))).scalars().all()
    return {"events": [
        {"id": e.id, "event_type": e.event_type, "severity": e.severity, "resource": e.resource,
         "summary": e.summary, "connector_type": e.connector_id,
         "received_at": e.received_at.isoformat()}
        for e in rows
    ], "count": len(rows)}


# ── Incidents + command center ──────────────────────────────────
@router.get("/orgs/{org_id}/incidents")
async def list_incidents(org_id: str, principal=Depends(require_role("VIEWER"))):
    incidents = incident_store.list(org_id)
    return {"incidents": incidents, "count": len(incidents)}


@router.post("/orgs/{org_id}/incidents/{incident_id}/command")
async def incident_command(org_id: str, incident_id: str, cmd: CommandRequest,
                           db: AsyncSession = Depends(get_db),
                           principal=Depends(require_role("OPERATOR"))):
    incident = incident_store.get(incident_id)
    if incident is None or incident.get("org_id") != org_id:
        raise HTTPException(404, "Incident not found")

    action = cmd.action
    if action == "dismiss":
        incident["status"] = "DISMISSED"
    elif action == "resolve":
        incident["status"] = "RESOLVED"
    elif action == "escalate":
        incident["status"] = "INVESTIGATING"
    elif action == "run_mission":
        from app.pipeline.incident_bridge import incident_bridge
        crisis = incident.get("crisis") or {"is_crisis": True, "reasons": ["manual-trigger"], "priority": "P1"}
        mission_id = await incident_bridge._launch(incident_id, crisis, incident)
        incident["mission_id"] = mission_id
    else:
        raise HTTPException(400, f"Unsupported action: {action}")

    await _write_audit(db, org_id, principal.actor, f"incident_{action}", "incident", incident_id,
                       {"payload": cmd.payload})
    return {"status": "ok", "incident": incident}


# ── Audit log ───────────────────────────────────────────────────
@router.get("/orgs/{org_id}/audit")
async def list_audit(org_id: str, limit: int = Query(100, le=500), db: AsyncSession = Depends(get_db),
                     principal=Depends(require_role("ANALYST"))):
    rows = (await db.execute(
        select(M.AuditLogModel).where(M.AuditLogModel.org_id == org_id)
        .order_by(M.AuditLogModel.created_at.desc()).limit(limit))).scalars().all()
    return {"audit": [
        {"id": a.id, "actor": a.actor, "action": a.action, "resource_type": a.resource_type,
         "resource_id": a.resource_id, "details": a.details,
         "created_at": a.created_at.isoformat()}
        for a in rows
    ], "count": len(rows)}


# ── Demo crisis sequence ────────────────────────────────────────
@router.post("/demo/crisis")
async def launch_demo_crisis(req: DemoTarget, db: AsyncSession = Depends(get_db)):
    org_id = req.org_id
    now_ts = int(datetime.now(timezone.utc).timestamp())

    # Resolve demo connector ids (create lightweight ones on first run).
    c_mon = await _seed_demo_connector(db, org_id, "monitoring", "Payment Monitor")
    c_gh = await _seed_demo_connector(db, org_id, "github", "Payment Service Deploys")
    c_sup = await _seed_demo_connector(db, org_id, "support", "Support Queue")

    sequence = [
        (c_mon, "monitoring", {
            "resource": "payment-api", "summary": "Payment API error rate at 47%",
            "severity": "critical", "event_type": "error_rate_spike",
            "metrics": {"error_rate": "47%"}, "source_event_id": f"pay_{now_ts}",
            "deployment_recent": True, "related_services": ["payment-api"]}),
        (c_gh, "github", {
            "repository": {"full_name": "payment-service"},
            "deployment_status": {"state": "success"},
            "deployment": {"ref": "main", "id": "dep-1234"},
            "id": f"dep_{now_ts}", "deployment_recent": True, "seconds_ago": 480,
            "related_services": ["payment-api"]}),
        (c_mon, "monitoring", {
            "resource": "database-primary", "summary": "DB primary latency spiked above 2s",
            "severity": "medium", "event_type": "latency_spike",
            "metrics": {"latency_ms": 2400}, "source_event_id": f"db_{now_ts}",
            "related_services": ["payment-api"]}),
        (c_sup, "support", {
            "product": "payment-api", "subject": "Payment failures", "submitted_count": 12,
            "severity": "medium", "source_event_id": f"spt_{now_ts}",
            "related_services": ["payment-api"]}),
    ]

    results = []
    for cid, ctype, payload in sequence:
        if not cid:
            continue
        try:
            results.append(await event_ingestion_pipeline.ingest(org_id, cid, ctype, payload, {}, None))
        except Exception as e:
            results.append({"status": "error", "error": str(e)[:200]})

    await _write_audit(db, org_id, "system", "demo_crisis_launched", "demo", None, {})
    return {"status": "crisis_sequence_fired", "results": results, "count": len(results)}


@router.post("/simulate-burst")
async def simulate_connector_event_burst(
    req: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    High-velocity burst injection endpoint for stress-testing signal correlation,
    cross-source anomaly detection, and automated crisis mission triggers.
    """
    org_id = req.get("org_id", settings.DEMO_ORG_ID)
    count = min(int(req.get("event_count", 5)), 25)
    severity = req.get("severity", "critical")
    source = req.get("source", "monitoring")
    now_ts = int(datetime.now(timezone.utc).timestamp())

    burst_events = []
    for i in range(count):
        payload = {
            "source_event_id": f"burst_{source}_{now_ts}_{i+1}",
            "resource": f"cluster-node-0{i%3 + 1}",
            "summary": f"Synthetic anomaly burst #{i+1} - High packet drop and memory thrashing detected",
            "severity": severity,
            "event_type": "telemetry_anomaly_burst",
            "metrics": {
                "cpu_utilization": 92.5 + (i * 1.2),
                "packet_drop_pct": 14.8 + (i * 0.8),
                "latency_p99_ms": 1850 + (i * 45)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        cid = await _seed_demo_connector(db, org_id, source, f"Burst Sim {source.title()}")
        try:
            res = await event_ingestion_pipeline.ingest(org_id, cid, source, payload, {}, None)
            burst_events.append(res)
        except Exception as e:
            burst_events.append({"status": "failed", "error": str(e)[:150]})

    return {
        "status": "BURST_INJECTION_COMPLETED",
        "org_id": org_id,
        "events_injected": len(burst_events),
        "source": source,
        "severity": severity,
        "results": burst_events
    }



async def _seed_demo_connector(db: AsyncSession, org_id: str, ctype: str, name: str) -> Optional[str]:
    existing = (await db.execute(select(M.ConnectorModel).where(
        M.ConnectorModel.org_id == org_id, M.ConnectorModel.connector_type == ctype))).scalar_one_or_none()
    if existing:
        return existing.id
    cid = f"conn_{org_id[:12]}_{ctype}_{uuid.uuid4().hex[:6]}"
    from app.core.security import hash_webhook_token
    db.add(M.ConnectorModel(
        id=cid, org_id=org_id, connector_type=ctype, name=name, status="CONNECTED", enabled=True,
        webhook_token_hash=hash_webhook_token(f"wh_{org_id}_{uuid.uuid4().hex[:16]}"),
        webhook_url=f"/api/v1/platform/orgs/{org_id}/connectors/{cid}/webhook"))
    await db.commit()
    return cid


async def _write_audit(db: AsyncSession, org_id, actor, action, resource_type, resource_id, details):
    db.add(M.AuditLogModel(org_id=org_id, actor=actor, action=action, resource_type=resource_type,
                           resource_id=resource_id, details=details or {}))
    try:
        await db.commit()
    except Exception:
        await db.rollback()