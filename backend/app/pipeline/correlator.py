"""
correlator.py — groups recent canonical events into incidents.

Correlation (per org, rolling 10-minute window):
  • An event joins an existing cluster if it shares a resource OR an overlapping
    related_service with any member of that cluster; otherwise it seeds a new one.
  • Old clusters (older than the window) are dropped.
  • A group is promoted to an INCIDENT when its confidence >= threshold (0.7),
    boosted by severity, deployment-recency and error-rate signals —
    so a "deploy 8 min ago + error-rate spike + complaint spike" sequence
    correlates into a single crisis incident.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional

from app.pipeline.event_bus import event_bus


class CorrelationEngine:
    def __init__(self, window_minutes: int = 10, confidence_threshold: float = 0.7):
        self.window = timedelta(minutes=window_minutes)
        self.confidence_threshold = confidence_threshold
        self.debounce_seconds = 1.0
        self._incident_handler: Optional[Callable[[Dict[str, object]], object]] = None
        # org_id -> {anchor_resource: {created_at, last_seen, events: []}}
        self._clusters: Dict[str, Dict[str, Dict]] = {}
        event_bus.subscribe("*", self._on_event)

    def on_incident(self, handler: Callable[[Dict], object]) -> None:
        self._incident_handler = handler

    async def _on_event(self, message: Dict) -> None:
        topic = message.get("topic", "")
        if not topic.endswith(".events"):
            return
        record = message.get("message") or {}
        org_id = record.get("org_id")
        if not org_id:
            return
        await self._evaluate(org_id, record)

    # ── Cluster management ─────────────────────────────────────
    def _prune(self, org_id: str, now: datetime) -> None:
        clusters = self._clusters.setdefault(org_id, {})
        expired = [k for k, c in clusters.items() if now - c["last_seen"] > self.window]
        for k in expired:
            del clusters[k]

    def _find_cluster_key(self, org_id: str, record: Dict) -> Optional[str]:
        """Returns the anchor key of the cluster this event belongs to, else None."""
        clusters = self._clusters.setdefault(org_id, {})
        resource = record.get("resource")
        related = set(record.get("related_services") or [])
        candidates = list(clusters.keys())
        for key in candidates:
            cluster = clusters[key]
            for member in cluster["events"]:
                if resource and member.get("resource") == resource:
                    return key
                if related and related.intersection(member.get("related_services") or []):
                    return key
        return None

    async def _evaluate(self, org_id: str, record: Dict) -> None:
        now = datetime.now(timezone.utc)
        self._prune(org_id, now)
        event_type = record.get("event_type", "")
        if event_type in ("health_ok", "readiness_ok"):
            return

        clusters = self._clusters.setdefault(org_id, {})
        key = self._find_cluster_key(org_id, record)
        if key is None:
            key = f"res_{len(clusters)}_{record.get('resource') or 'unknown'}_{int(now.timestamp())}"
            clusters[key] = {"created_at": now, "last_seen": now, "events": [], "fired": False}
        cluster = clusters[key]
        cluster["last_seen"] = now
        cluster["events"].append(record)

        if cluster.get("fired"):
            return  # already escalated this cluster in the current window
        group = cluster["events"]
        confidence = self._compute_confidence(group)
        if confidence >= self.confidence_threshold:
            # Debounce so a burst of related signals all contribute evidence to
            # the same incident before it is emitted. Events keep joining during
            # the sleep; 'fired' is set only after the incident is emitted.
            await asyncio.sleep(self.debounce_seconds)
            if cluster.get("fired"):
                return
            frozen = list(cluster["events"])
            final_confidence = self._compute_confidence(frozen)
            if final_confidence < self.confidence_threshold:
                return  # group fell below promotion threshold after collecting
            cluster["fired"] = True
            incident = self._build_incident(org_id, frozen, final_confidence, datetime.now(timezone.utc))
            if self._incident_handler:
                result = self._incident_handler(incident)
                if asyncio.iscoroutine(result):
                    await result

    def _compute_confidence(self, group: List[Dict]) -> float:
        # Incident confidence reflects its strongest corroborated signal, with a
        # modest bonus for additional corroborating evidence within the window.
        scores = []
        raw = 0.0
        for ev in group:
            sev = (ev.get("severity") or "info").lower()
            base = {"info": 0.3, "low": 0.4, "medium": 0.6, "high": 0.8, "critical": 1.0}.get(sev, 0.3)
            score = base
            if ev.get("deployment_recent"):
                score += 0.15
            er = ev.get("error_rate")
            if er:
                try:
                    num = float(str(er).replace("%", ""))
                    if num > 5:
                        score += 0.15
                except Exception:
                    pass
            scores.append(round(min(score, 1.0), 3))
            raw = max(raw, min(score, 1.0))
        # Corroboration bonus: up to +0.15 total as more signals agree.
        bonus = 0.05 * max(0, min(len(scores) - 1, 3))
        return round(min(raw + bonus, 1.0), 3)

    def _build_incident(self, org_id: str, group: List[Dict], confidence: float, now: datetime) -> Dict[str, object]:
        resources = {e.get("resource") or "unknown" for e in group}
        types = {e.get("event_type") for e in group}
        severities = [(e.get("severity") or "info").lower() for e in group]
        severity_rank = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
        top_severity = max(severities, key=lambda s: severity_rank.get(s, 0))
        summary = f"Incident: {', '.join(types)} affecting {', '.join(resources)} (confidence {confidence:.0%})"
        connector_types = {e.get("connector_type") for e in group}

        return {
            "org_id": org_id,
            "title": summary,
            "summary": summary,
            "severity": top_severity,
            "confidence": confidence,
            "status": "detected",
            "resource": ", ".join(sorted(resources)),
            "event_types": sorted(types),
            "connector_types": sorted(connector_types),
            "related_services": sorted({s for e in group for s in e.get("related_services") or []}),
            "event_refs": ["memory://" + (e.get("dedupe_hash") or "") for e in group],
            "source_events": group,
            "meta": {
                "evidence_count": len(group),
                "deployment_recent": any(e.get("deployment_recent") for e in group),
            },
            "detected_at": now.isoformat(),
            "ts": now,
        }


correlation_engine = CorrelationEngine()