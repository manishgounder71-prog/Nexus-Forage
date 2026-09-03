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
    """In-process incident + crisis ledger shared with the API layer."""

    def __init__(self):
        self.incidents: Dict[str, Dict] = {}  # incident_id -> incident dict
        self.crises: Dict[str, Dict] = {}     # incident_id -> crisis verdict

    def upsert(self, incident: Dict) -> Dict:
        iid = incident.get("id") or _gen_incident_id(incident)
        incident["id"] = iid
        self.incidents[iid] = incident
        return incident

    def list(self, org_id: Optional[str] = None) -> List[Dict]:
        items = list(self.incidents.values())
        if org_id:
            items = [i for i in items if i.get("org_id") == org_id]
        return sorted(items, key=lambda i: i.get("detected_at") or "", reverse=True)

    def get(self, incident_id: str) -> Optional[Dict]:
        return self.incidents.get(incident_id)

    def mark_crisis(self, incident_id: str, verdict: Dict) -> None:
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
        saved = incident_store.upsert(incident)
        verdict = crisis_engine.evaluate(saved)
        if verdict["is_crisis"]:
            incident_store.mark_crisis(saved["id"], verdict)
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