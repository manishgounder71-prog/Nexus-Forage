"""
Canonical event normalization utilities shared by every connector adapter.
"""
import json
from typing import Any, Dict, Optional

from app.core.security import compute_dedupe_hash
from .schemas import NexusCanonicalEvent, normalize_severity, infer_severity_from_text


def build_canonical_event(
    connector_type: str,
    connector_id: str,
    event_type: str,
    resource: str = "",
    summary: str = "",
    severity: Any = None,
    metadata: Optional[Dict[str, Any]] = None,
    raw_payload: Optional[Dict[str, Any]] = None,
    source_event_id: str = "",
    text_for_severity: str = "",
    error_rate: Optional[str] = None,
    avg_latency_ms: Optional[float] = None,
    deployment_recent: bool = False,
    related_services: Optional[list] = None,
) -> NexusCanonicalEvent:
    """Builds a canonical event, computing severity + dedupe hash automatically."""
    if severity is None:
        severity = infer_severity_from_text(text_for_severity or summary, error_rate)
    sev = normalize_severity(severity)
    evt = NexusCanonicalEvent(
        connector_type=connector_type,
        connector_id=connector_id,
        event_type=event_type,
        severity=sev,
        resource=resource or "",
        summary=summary or "",
        metadata=metadata or {},
        raw_payload=raw_payload or {},
        source_event_id=source_event_id or "",
    )
    evt.deployment_recent = deployment_recent
    evt.related_services = related_services or []
    evt.error_rate = error_rate
    evt.avg_latency_ms = avg_latency_ms
    evt.dedupe_hash = compute_dedupe_hash(connector_id, event_type, evt.resource, evt.source_event_id)
    return evt


def safe_get(obj: Any, *path: str, default: Any = None) -> Any:
    """Case-insensitive deep get on dict/list structures with a dotted path."""
    current = obj if isinstance(obj, dict) else {}
    for key in path:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list) and current and isinstance(current[0], dict):
            current = current[0].get(key)
        else:
            return default
        if current is None:
            return default
    return current


def try_json(value: Any) -> Any:
    """Parse a string that might be JSON, returning it unmapped otherwise."""
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return value
    return value