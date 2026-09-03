"""
normalizer.py — turns a connector-normalized NexusCanonicalEvent + raw payload
into a fully populated event dict ready for the correlation layer and storage.
Enforces event-type allow-list filtering and fills defaults.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.connectors.base.schemas import NexusCanonicalEvent, normalize_severity
from app.pipeline.event_bus import event_bus
from app.core.security import compute_dedupe_hash


def normalize_event_payload(
    canonical: NexusCanonicalEvent,
    payload: Dict[str, Any],
    org_id: str,
    allowlist: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Builds the canonical, normalized event record from a connector event."""
    if allowlist and canonical.event_type not in allowlist:
        return {}  # filtered out

    now = datetime.now(timezone.utc)
    dedupe = compute_dedupe_hash(
        canonical.connector_id,
        canonical.event_type,
        canonical.resource,
        canonical.source_event_id,
    )

    return {
        "org_id": org_id,
        "connector_type": canonical.connector_type,
        "connector_id": canonical.connector_id,
        "event_type": canonical.event_type,
        "resource": canonical.resource,
        "summary": canonical.summary,
        "severity": canonical.severity,
        "status": "new",
        "dedupe_hash": dedupe,
        "source_event_id": canonical.source_event_id,
        "metadata": canonical.metadata or {},
        "related_services": canonical.related_services or [],
        "deployment_recent": bool(canonical.deployment_recent),
        "error_rate": canonical.error_rate,
        "avg_latency_ms": canonical.avg_latency_ms,
        "raw_payload": {"payload": payload},
        "timestamp": now.isoformat(),
    }


def publish_canonical_event(canonical: NexusCanonicalEvent, payload: Dict[str, Any], org_id: str) -> Dict[str, Any]:
    """Normalizes and publishes an event onto the bus under its org topic."""
    record = normalize_event_payload(canonical, payload, org_id)
    if not record:
        return {}
    asyncio_run(event_bus.publish(f"org.{org_id}.events", record))
    return record


def asyncio_run(coro):
    """Best-effort sync bridge for sync publishing contexts."""
    try:
        import asyncio

        async def _run():
            return await coro

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            # Already inside a loop; schedule and wait is not possible synchronously — return coroutine.
            return coro
    except Exception:
        return None