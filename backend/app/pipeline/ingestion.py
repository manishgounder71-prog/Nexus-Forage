"""
ingestion.py — the event ingestion pipeline.

Coordinates the full path for a raw webhook payload:
  connector.normalize_event() -> canonical record -> dedupe check -> persist
  -> publish on the event bus -> (correlator turns groups into incidents).

Also owns a durable incident store so incidents survive restarts.
"""
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db import models as db
from app.connectors.registry import connector_registry
from app.pipeline.event_bus import event_bus
from app.pipeline.correlator import correlation_engine
from app.pipeline.crisis_detector import crisis_engine


class IncidentStore:
    """Incident + crisis ledger shared with the API layer.

    Incidents are persisted to the SQLite `incidents` table (durable across
    restarts) and mirrored in-process for real-time aggregation. ``list`` and
    ``get`` read from the durable store so incidents survive restarts.
    """

    def __init__(self):
        self.incidents: Dict[str, Dict] = {}  # incident_id -> incident dict (in-memory mirror)
        self.crises: Dict[str, Dict] = {}     # incident_id -> crisis verdict
        self._loaded = False

    async def _load(self) -> None:
        """Eagerly hydrate from the durable incidents table on first access."""
        if self._loaded:
            return
        self._loaded = True
        try:
            async with AsyncSessionLocal() as session:
                rows = (
                    await session.execute(
                        select(db.IncidentModel).order_by(db.IncidentModel.created_at.desc())
                    )
                ).scalars().all()
            for r in rows:
                self.incidents[r.id] = _incident_model_to_dict(r)
        except Exception as e:  # pragma: no cover - resilient on degraded storage
            print(f"[IncidentStore] load failed: {e}")

    async def upsert(self, incident: Dict) -> Dict:
        iid = incident.get("id") or _gen_incident_id(incident)
        incident["id"] = iid
        # Durable write-through to SQLite.
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    res = await session.execute(
                        select(db.IncidentModel).where(db.IncidentModel.id == iid))
                    row = res.scalar_one_or_none()
                    if row is None:
                        row = db.IncidentModel(id=iid, org_id=incident.get("org_id") or "unknown")
                        session.add(row)
                    row.title = incident.get("title") or incident.get("summary") or "Operational incident"
                    row.severity = incident.get("severity") or "medium"
                    row.confidence = float(incident.get("confidence") or 0.0)
                    row.status = (incident.get("status") or "detected").upper()
                    row.affected_resources = incident.get("affected_resources") or []
                    row.signals = incident.get("signals") or []
                    row.event_count = len(incident.get("source_events") or []) or incident.get("event_count") or 0
                    row.mission_id = incident.get("mission_id")
        except Exception as e:  # pragma: no cover
            print(f"[IncidentStore] persist failed: {e}")
        self.incidents[iid] = incident
        return incident

    async def list(self, org_id: Optional[str] = None) -> List[Dict]:
        await self._load()
        items = list(self.incidents.values())
        if org_id:
            items = [i for i in items if i.get("org_id") == org_id]
        return sorted(items, key=lambda i: i.get("detected_at") or i.get("first_seen") or "", reverse=True)

    async def get(self, incident_id: str) -> Optional[Dict]:
        await self._load()
        return self.incidents.get(incident_id)

    async def mark_crisis(self, incident_id: str, verdict: Dict) -> None:
        # Avoid a circular reference: the verdict embeds the incident dict it
        # was derived from. Store only the summary fields on the incident.
        self.crises[incident_id] = verdict
        if incident_id in self.incidents:
            self.incidents[incident_id]["crisis"] = {
                "is_crisis": verdict.get("is_crisis"),
                "reasons": verdict.get("reasons") or [],
                "priority": verdict.get("priority"),
                "confidence": verdict.get("confidence"),
                "detected_at": verdict.get("detected_at"),
            }
        # Persist crisis verdict signals + status to the durable row.
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    res = await session.execute(
                        select(db.IncidentModel).where(db.IncidentModel.id == incident_id))
                    row = res.scalar_one_or_none()
                    if row is not None:
                        row.status = "CRISIS"
                        if verdict.get("signals"):
                            row.signals = verdict.get("signals")
                        if verdict.get("priority"):
                            if hasattr(row, "priority"):
                                row.priority = verdict.get("priority")
                        if verdict.get("confidence"):
                            row.confidence = float(verdict.get("confidence"))
        except Exception as e:  # pragma: no cover
            print(f"[IncidentStore] mark_crisis persist failed: {e}")


def _incident_model_to_dict(row: "db.IncidentModel") -> Dict:
    """Converts a durable IncidentModel row back into an incident dict."""
    signals = row.signals or []
    reasons = [
        s if isinstance(s, str) else (s.get("reason") or s.get("message") or "")
        for s in (signals if isinstance(signals, list) and signals and isinstance(signals[0], str) else [])
    ]
    return {
        "id": row.id,
        "org_id": row.org_id,
        "title": row.title,
        "summary": row.title,
        "severity": row.severity,
        "confidence": row.confidence or 0.0,
        "status": (row.status or "DETECTED").lower(),
        "affected_resources": row.affected_resources or [],
        "signals": row.signals or [],
        "event_types": [],
        "resource": ", ".join(row.affected_resources or []),
        "related_services": [],
        "source_events": [],
        "event_count": row.event_count or 0,
        "mission_id": row.mission_id,
        "first_seen": row.first_seen.isoformat() if row.first_seen else None,
        "last_seen": row.last_seen.isoformat() if row.last_seen else None,
        "detected_at": row.created_at.isoformat() if row.created_at else None,
        "reasons": reasons,
        "priority": None,
    }


incident_store = IncidentStore()


async def _safe_bridge(message: Dict) -> None:
    try:
        from app.pipeline.incident_bridge import incident_bridge
        await incident_bridge.on_crisis(message)
    except Exception as e:
        print(f"[Pipeline] crisis bridge error: {e}")


def _gen_incident_id(incident: Dict) -> str:
    import uuid
    return f"inc_{incident.get('org_id', 'org')[:12]}_{uuid.uuid4().hex[:8]}"


class EventIngestionPipeline:
    def __init__(self):
        # Bind the correlator -> incident persistence -> crisis detection chain.
        correlation_engine.on_incident(self._on_incident)
        # Wire the incident->mission bridge to crisis topics (wildcard catches org.*.crises).
        from app.pipeline.incident_bridge import incident_bridge
        event_bus.subscribe("*", self._relay_crises_to_bridge)

    async def _relay_crises_to_bridge(self, message: Dict) -> None:
        topic = message.get("topic") or ""
        if topic.endswith(".crises"):
            await _safe_bridge(message["message"])

    async def _on_incident(self, incident: Dict) -> None:
        saved = await incident_store.upsert(incident)
        verdict = crisis_engine.evaluate(saved)
        if verdict["is_crisis"]:
            await incident_store.mark_crisis(saved["id"], verdict)
            await self._relay_crisis(saved["id"], verdict)
        await self._relay_incident(saved)

    async def _relay_incident(self, incident: Dict) -> None:
        await event_bus.publish(f"org.{incident.get('org_id')}.incidents", incident)

    async def _relay_crisis(self, incident_id: str, verdict: Dict) -> None:
        await event_bus.publish(
            f"org.{verdict['incident'].get('org_id')}.crises",
            {"incident_id": incident_id, "verdict": verdict},
        )

    async def ingest(self, org_id: str, connector_id: str, connector_type: str,
                     payload: Dict, config: Dict, allowlist: Optional[List[str]] = None) -> Dict:
        """Accepts a raw payload for a registered connector and runs it through the pipeline."""
        connector = await connector_registry.create_connector(connector_type, {
            **config, "connector_id": connector_id})
        canonical = connector.normalize_event(payload)

        from app.pipeline.normalizer import normalize_event_payload
        record = normalize_event_payload(canonical, payload, org_id, allowlist)
        if not record:
            return {"status": "filtered", "reason": "event_type not in allow-list"}

        # Dedupe
        existed = await self._dedupe_exists(org_id, record["dedupe_hash"])
        if existed:
            return {"status": "duplicate", "dedupe_hash": record["dedupe_hash"]}

        # Persist
        await self._persist_event(org_id, connector_id, record)

        # Publish to bus (triggers correlator)
        await event_bus.publish(f"org.{org_id}.events", record)

        return {"status": "ingested", "event": record}

    async def _dedupe_exists(self, org_id: str, dedupe_hash: str) -> bool:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(db.NexusEventModel.id).where(
                    db.NexusEventModel.org_id == org_id,
                    db.NexusEventModel.dedupe_hash == dedupe_hash,
                ).limit(1)
            )
            return result.scalar_one_or_none() is not None

    async def _persist_event(self, org_id: str, connector_id: str, record: Dict) -> None:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                ev = db.NexusEventModel(
                    org_id=org_id,
                    connector_id=connector_id,
                    source_event_id=record.get("source_event_id"),
                    event_type=record.get("event_type", "unknown"),
                    severity=record.get("severity", "info"),
                    resource=record.get("resource"),
                    summary=record.get("summary", ""),
                    metadata_json=record.get("metadata") or {},
                    raw_payload=record.get("raw_payload") or {},
                    dedupe_hash=record.get("dedupe_hash"),
                    processed=True,
                )
                session.add(ev)
            await self._bump_connector_count(org_id, connector_id)

    async def _bump_connector_count(self, org_id: str, connector_id: str) -> None:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                res = await session.execute(
                    select(db.ConnectorModel).where(
                        db.ConnectorModel.id == connector_id, db.ConnectorModel.org_id == org_id))
                conn = res.scalar_one_or_none()
                if conn:
                    conn.events_count = (conn.events_count or 0) + 1
                    conn.last_event_at = datetime.now(timezone.utc)

    async def ingest_canonical(self, canonical_event: Dict) -> Dict:
        """Processes a pre-normalized canonical event directly through correlation."""
        org_id = canonical_event.get("organization_id")
        if org_id:
            await correlation_engine._evaluate(org_id, canonical_event)
        return {"status": "processed", "event": canonical_event}


event_ingestion_pipeline = EventIngestionPipeline()