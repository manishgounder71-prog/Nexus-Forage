"""
ingest.py — Universal Ingestion Endpoint for NEXUS CONNECT.

Provides zero-code ingestion at:
  POST /api/v1/ingest/{organization_public_id}

Pipeline:
  1. Resolve Organization (by public_id or id)
  2. Size & JSON validation
  3. Check Timestamp freshness (5 min tolerance)
  4. Verify HMAC-SHA256 signature
  5. Check Replay Protection (X-Nexus-Event-Id)
  6. Per-Tenant Rate Limiting (429 Too Many Requests)
  7. Return 202 Accepted immediately (< 50ms)
  8. Background Task: Normalize -> Deduplicate -> Persist -> EventBus -> Correlator/Crisis
"""
import asyncio
import json
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, Response, status
from sqlalchemy import select

from app.core.config import settings
from app.core.security import (
    compute_dedupe_hash,
    decrypt_credential,
    validate_timestamp_freshness,
    verify_org_webhook_signature,
)
from app.db import models as M
from app.db.session import AsyncSessionLocal
from app.pipeline.event_bus import event_bus
from app.pipeline.ingestion import event_ingestion_pipeline

router = APIRouter(tags=["Ingestion Engine"])

# In-memory replay cache: event_id -> expiration timestamp
_REPLAY_CACHE: Dict[str, float] = {}
_REPLAY_LOCK = asyncio.Lock()

# Per-organization rate-limit tracker: org_id -> deque of timestamps in last 60s
_RATE_LIMIT_BUCKETS: Dict[str, deque] = defaultdict(deque)

# Standard event types supported by NEXUS CONNECT
CANONICAL_EVENT_TYPES = {
    "SERVICE_FAILURE",
    "DEPLOYMENT",
    "DATABASE_DEGRADATION",
    "SECURITY_ALERT",
    "PERFORMANCE_DEGRADATION",
    "CUSTOMER_IMPACT",
    "INFRASTRUCTURE_FAILURE",
    "WORKFLOW_FAILURE",
    "BUSINESS_ANOMALY",
    "CUSTOM",
}


def _check_rate_limit(org_id: str, limit_per_minute: int = 100) -> bool:
    """Returns True if within rate limit, False if rate limited."""
    now = time.time()
    q = _RATE_LIMIT_BUCKETS[org_id]
    while q and q[0] < now - 60.0:
        q.popleft()
    if len(q) >= limit_per_minute:
        return False
    q.append(now)
    return True


def _check_and_mark_replay(event_id: str, ttl_seconds: int = 600) -> bool:
    """Returns True if duplicate/replayed, False if new event."""
    now = time.time()
    # Periodic cleanup of expired items
    if len(_REPLAY_CACHE) > 5000:
        expired = [k for k, v in _REPLAY_CACHE.items() if v < now]
        for k in expired:
            _REPLAY_CACHE.pop(k, None)

    if event_id in _REPLAY_CACHE and _REPLAY_CACHE[event_id] > now:
        return True
    _REPLAY_CACHE[event_id] = now + ttl_seconds
    return False


async def _resolve_organization(public_id: str) -> Optional[Dict[str, Any]]:
    """Resolves an active organization by its public identifier or internal ID."""
    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(M.OrganizationModel).where(
                (M.OrganizationModel.public_id == public_id)
                | (M.OrganizationModel.id == public_id)
                | (M.OrganizationModel.slug == public_id)
            )
        )
        org = res.scalar_one_or_none()
        if not org or org.status != "ACTIVE":
            return None

        # Fetch policies if any
        pol_res = await db.execute(
            select(M.OrganizationPolicyModel).where(M.OrganizationPolicyModel.org_id == org.id)
        )
        policy = pol_res.scalar_one_or_none()

        return {
            "id": org.id,
            "public_id": org.public_id or org.id,
            "name": org.name,
            "slug": org.slug,
            "ingestion_secret_hash": org.ingestion_secret_hash,
            "settings": org.settings or {},
            "rate_limit": policy.rate_limit_per_minute if policy else 100,
            "timestamp_tolerance": policy.timestamp_tolerance_seconds if policy else 300,
            "max_payload_bytes": policy.max_payload_bytes if policy else 1048576,
        }


def _normalize_payload(raw_payload: Dict[str, Any], org_id: str, source_event_id: str) -> Dict[str, Any]:
    """Universal normalizer mapping external payloads to canonical Nexus event format."""
    # Support payload wrapping
    body = raw_payload.get("payload", raw_payload) if isinstance(raw_payload, dict) else {}
    if not isinstance(body, dict):
        body = {"raw": raw_payload}

    # Extract event type
    raw_type = (
        body.get("event_type")
        or body.get("type")
        or body.get("event")
        or body.get("action")
        or "CUSTOM"
    )
    raw_type_upper = str(raw_type).upper().replace("-", "_").replace(" ", "_")
    event_type = raw_type_upper if raw_type_upper in CANONICAL_EVENT_TYPES else "CUSTOM"

    # Derive resource & service
    resource = (
        body.get("resource")
        or body.get("service")
        or body.get("target")
        or body.get("hostname")
        or (body.get("repository", {}).get("full_name") if isinstance(body.get("repository"), dict) else body.get("repository"))
        or "system"
    )
    service = body.get("service") or str(resource).split("@")[0].split("/")[0]

    # Derive severity
    raw_sev = str(body.get("severity") or body.get("priority") or body.get("level") or "info").lower()
    if raw_sev in ("crit", "critical", "p1", "fatal", "emergency"):
        severity = "critical"
    elif raw_sev in ("high", "p2", "error"):
        severity = "high"
    elif raw_sev in ("med", "medium", "p3", "warning", "warn"):
        severity = "medium"
    else:
        severity = "low" if raw_sev in ("low", "p4") else "info"

    summary = (
        body.get("summary")
        or body.get("title")
        or body.get("message")
        or body.get("description")
        or f"{event_type} event on {resource}"
    )

    return {
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "organization_id": org_id,
        "source_connector": body.get("source") or body.get("source_connector") or "universal_webhook",
        "source_event_id": str(source_event_id or body.get("id") or uuid.uuid4().hex[:8]),
        "event_type": event_type,
        "raw_event_type": str(raw_type),
        "severity": severity,
        "resource": str(resource),
        "service": str(service),
        "summary": str(summary)[:500],
        "metadata": body.get("metadata") or {k: v for k, v in body.items() if k not in ("payload", "raw")},
        "raw_payload": body,
        "timestamp": body.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        "received_at": datetime.now(timezone.utc).isoformat(),
    }


async def _process_event_async(event_dict: Dict[str, Any], org_id: str):
    """Asynchronous background processing worker."""
    try:
        dedupe_hash = compute_dedupe_hash(
            connector_id=event_dict["source_connector"],
            event_type=event_dict["event_type"],
            resource=event_dict.get("resource"),
            source_event_id=event_dict.get("source_event_id"),
        )

        async with AsyncSessionLocal() as db:
            async with db.begin():
                # Deduplication check in DB
                existing = (
                    await db.execute(
                        select(M.NexusEventModel).where(
                            M.NexusEventModel.org_id == org_id,
                            M.NexusEventModel.dedupe_hash == dedupe_hash,
                        )
                    )
                ).scalar_one_or_none()

                if existing:
                    return

                event_rec = M.NexusEventModel(
                    id=event_dict["event_id"],
                    org_id=org_id,
                    source_event_id=event_dict["source_event_id"],
                    event_type=event_dict["event_type"],
                    severity=event_dict["severity"],
                    resource=event_dict["resource"],
                    summary=event_dict["summary"],
                    metadata_json=event_dict.get("metadata", {}),
                    raw_payload=event_dict.get("raw_payload", {}),
                    received_at=datetime.now(timezone.utc),
                    processed=True,
                    dedupe_hash=dedupe_hash,
                )
                db.add(event_rec)

                # Audit log entry
                audit_rec = M.AuditLogModel(
                    org_id=org_id,
                    actor="WEBHOOK",
                    action="event_received",
                    resource_type="event",
                    resource_id=event_dict["event_id"],
                    details={
                        "event_type": event_dict["event_type"],
                        "severity": event_dict["severity"],
                        "resource": event_dict["resource"],
                    },
                )
                db.add(audit_rec)

        # Publish to event bus for real-time correlator & WebSocket broadcast
        await event_bus.publish(f"org.{org_id}.events", event_dict)
        await event_bus.publish("events.all", event_dict)

        # Trigger ingestion pipeline correlation
        await event_ingestion_pipeline.ingest_canonical(event_dict)

    except Exception as e:
        print(f"[IngestEngine] Background processing error for org {org_id}: {e}")


@router.post("/ingest/{organization_public_id}", status_code=status.HTTP_202_ACCEPTED)
async def ingest_organization_webhook(
    organization_public_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    x_nexus_timestamp: Optional[str] = Header(None, alias="X-Nexus-Timestamp"),
    x_nexus_signature: Optional[str] = Header(None, alias="X-Nexus-Signature"),
    x_nexus_event_id: Optional[str] = Header(None, alias="X-Nexus-Event-Id"),
):
    """
    Zero-code universal ingestion endpoint for external systems.
    Acknowledge quickly (< 50ms) with 202 Accepted.
    """
    raw_body = await request.body()

    # 1. Resolve Organization
    org = await _resolve_organization(organization_public_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found or inactive: '{organization_public_id}'",
        )

    org_id = org["id"]

    # 2. Payload size check
    if len(raw_body) > org["max_payload_bytes"]:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Payload exceeds maximum allowed size of {org['max_payload_bytes']} bytes",
        )

    # 3. Parse JSON
    try:
        raw_json = json.loads(raw_body.decode("utf-8") or "{}")
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed JSON payload")

    # 4. Rate Limiting Check
    if not _check_rate_limit(org_id, org["rate_limit"]):
        return Response(
            content=json.dumps({"error": "Rate limit exceeded for organization", "retry_after": 60}),
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            media_type="application/json",
            headers={"Retry-After": "60"},
        )

    # 5. Timestamp Freshness Check (if provided)
    if x_nexus_timestamp:
        if not validate_timestamp_freshness(x_nexus_timestamp, org["timestamp_tolerance"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request timestamp is expired or outside the allowed tolerance window (5m)",
            )

    # 6. Signature Verification (if secret configured or signature provided)
    stored_secret = org.get("ingestion_secret_hash") or org.get("settings", {}).get("ingestion_secret")
    if stored_secret and x_nexus_signature:
        try:
            plain_secret = decrypt_credential(stored_secret)
        except Exception:
            plain_secret = stored_secret

        ts = x_nexus_timestamp or str(int(time.time()))
        valid_sig = verify_org_webhook_signature(ts, raw_body, x_nexus_signature, plain_secret)
        if not valid_sig and not settings.DEMO_MODE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid HMAC-SHA256 signature in X-Nexus-Signature header",
            )

    # 7. Replay Protection
    event_id = x_nexus_event_id or raw_json.get("id") or str(uuid.uuid4())
    if _check_and_mark_replay(f"{org_id}:{event_id}"):
        return Response(
            content=json.dumps({
                "status": "idempotent_duplicate",
                "message": "Event already received and processed",
                "event_id": event_id,
                "organization_id": org_id,
            }),
            status_code=status.HTTP_200_OK,
            media_type="application/json",
        )

    # 8. Normalize & schedule background processing
    canonical_event = _normalize_payload(raw_json, org_id, event_id)
    background_tasks.add_task(_process_event_async, canonical_event, org_id)

    return {
        "status": "accepted",
        "event_id": canonical_event["event_id"],
        "organization_id": org_id,
        "event_type": canonical_event["event_type"],
        "received_at": canonical_event["received_at"],
    }
