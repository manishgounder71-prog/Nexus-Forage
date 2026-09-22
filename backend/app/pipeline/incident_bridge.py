"""
incident_bridge.py — connects the event pipeline to the NEXUS mission engine.

When the crisis engine declares a crisis-grade incident, this bridge builds an
operational prompt from the evidence, persists a MissionModel, updates the
incident with a mission_id, and launches the multi-agent mission in the
background — the "autonomous AI builder" loop.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import select

from app.db import models as db
from app.db.session import AsyncSessionLocal
from app.orchestration.mission_engine import master_mission_engine
from app.api.websocket import websocket_manager


def build_incident_prompt(verdict: Dict, incident: Dict) -> str:
    """Frames an operational resolution mission from a crisis verdict."""
    reasons = verdict.get("reasons") or []
    resources = incident.get("resource") or "systems"
    types = incident.get("event_types") or []
    evidence = incident.get("source_events") or []
    evidence_lines = []
    for e in evidence[:6]:
        evidence_lines.append(
            f"- [{e.get('severity')}] {e.get('event_type')} @ {e.get('resource')}: {e.get('summary')}"
        )
    evidence_txt = "\n".join(evidence_lines) or "- (no evidence attached)"

    return (
        f"CRITICAL INCIDENT RESPONSE for organization '{incident.get('org_id')}'. "
        f"Priority {verdict.get('priority')}. A crisis-grade operational incident was detected "
        f"affecting: {resources}. Trigger signals: {', '.join(reasons) or 'none'}. "
        f"Event types observed: {', '.join(types) or 'none'}.\n\n"
        f"EVIDENCE:\n{evidence_txt}\n\n"
        f"OBJECTIVE: Diagnose the root cause from this evidence and produce a clear, "
        f"prioritized remediation plan (immediate stabilization > root cause > prevention) "
        f"with concrete actions, owner roles, and verification steps. State assumptions "
        f"and confidence for each recommendation."
    )


class IncidentBridge:
    def __init__(self):
        self._bus_subscriber = None
        self._launching: set = set()

    async def on_crisis(self, message: Dict) -> None:
        """Callback wired to the crisis topic; launches a mission per incident."""
        incident_id = message.get("incident_id")
        verdict = message.get("verdict") or {}
        incident = verdict.get("incident") or {}
        if not incident_id or incident_id in self._launching:
            return
        self._launching.add(incident_id)
        try:
            await self._launch(incident_id, verdict, incident)
        finally:
            self._launching.discard(incident_id)

    async def _launch(self, incident_id: str, verdict: Dict, incident: Dict) -> Optional[str]:
        org_id = incident.get("org_id") or "unknown"
        prompt = build_incident_prompt(verdict, incident)
        mission_id = f"msn_{uuid.uuid4().hex[:8]}"

        # Persist mission + incident.mission_id
        async with AsyncSessionLocal() as session:
            async with session.begin():
                rec = db.MissionModel(
                    id=mission_id,
                    org_id=org_id,
                    title=f"Crisis response: {incident.get('resource') or 'systems'}",
                    raw_prompt=prompt,
                    mission_type="incident_response",
                    severity=incident.get("severity", "critical"),
                    urgency=1.0,
                    deadline_hours=24,
                    status="CREATED",
                    required_capabilities=incident.get("related_services") or [],
                )
                session.add(rec)
                res = await session.execute(
                    select(db.IncidentModel).where(
                        db.IncidentModel.id == incident_id, db.IncidentModel.org_id == org_id))
                inc = res.scalar_one_or_none()
                if inc:
                    inc.mission_id = mission_id
                    inc.status = "INVESTIGATING"
                    if verdict.get("signals"):
                        inc.signals = verdict.get("signals")

        # Reflect mission id on the shared in-memory incident (incident_store object).
        incident["mission_id"] = mission_id
        incident["status"] = "INVESTIGATING"

        async def run_bg():
            await master_mission_engine.run_mission_safely(
                mission_id=mission_id,
                raw_prompt=prompt,
                event_broadcaster=lambda evt: websocket_manager.broadcast_event(mission_id, evt),
                organization_id=org_id,
            )
            await websocket_manager.broadcast_org(
                org_id,
                {"type": "mission_launched", "mission_id": mission_id, "incident_id": incident_id},
            )

        asyncio.create_task(run_bg())
        return mission_id


incident_bridge = IncidentBridge()