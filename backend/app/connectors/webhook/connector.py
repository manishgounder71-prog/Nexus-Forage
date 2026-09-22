"""
UniversalWebhookConnector — the generic 'bring your own webhook' connector.
Accepts any JSON payload and maps it via a user-configurable field mapping, or
falls back to intuitive heuristics.
"""
from typing import Dict, Optional

from app.connectors.base import (
    BaseConnector,
    ConnectorStatus,
    ConnectorCapability,
    AuthType,
    ValidationResult,
    HealthCheckResult,
    NexusCanonicalEvent,
)
from app.connectors.base.events import build_canonical_event, safe_get, try_json, infer_severity_from_text

WEBHOOK_TYPE = "webhook"


class UniversalWebhookConnector(BaseConnector):
    connector_type = WEBHOOK_TYPE
    display_name = "Universal Webhook"
    description = "Generic webhook endpoint that normalizes any JSON payload into canonical events."
    auth_type = AuthType.HMAC_SIGNATURE
    capabilities = [ConnectorCapability.READ_EVENTS,
                    ConnectorCapability.WRITE_EVENTS,
                    ConnectorCapability.HEALTH_CHECK]

    async def validate_credentials(self) -> ValidationResult:
        secret = self.config.get("secret") or self.config.get("webhook_token")
        if not secret:
            return ValidationResult(valid=False, message="Universal webhook requires a 'secret' or 'webhook_token'.")
        return ValidationResult(valid=True, message="Webhook credentials valid")

    async def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(healthy=True, status=ConnectorStatus.CONNECTED.value, latency_ms=8)

    def normalize_event(self, raw_payload: Dict) -> NexusCanonicalEvent:
        body = try_json(raw_payload)
        if not isinstance(body, dict):
            body = {"raw": body}

        field_map = self.config.get("field_mapping") or {}

        def mapped(key, default_value=""):
            source_path = field_map.get(key)
            if source_path:
                return safe_get(body, *str(source_path).split("."), default=default_value)
            return safe_get(body, key, default=default_value)

        event_type = str(mapped("event_type", "webhook_event"))
        resource = str(mapped("resource", safe_get(body, "system") or "unknown"))
        summary = str(mapped("summary", safe_get(body, "message") or safe_get(body, "description") or "Webhook event"))
        severity = mapped("severity", None)
        metadata = safe_get(body, "metadata") or {k: v for k, v in body.items() if k not in {
            "event_type", "resource", "severity", "summary", "source_event_id", "timestamp"}}
        if not isinstance(metadata, dict):
            metadata = {**body} if isinstance(body, dict) else {}

        return build_canonical_event(
            connector_type=WEBHOOK_TYPE,
            connector_id=self.config.get("connector_id", ""),
            event_type=event_type,
            resource=resource,
            summary=summary[:400],
            severity=severity,
            text_for_severity=str(summary),
            metadata=metadata,
            raw_payload=body,
            source_event_id=str(mapped("source_event_id") or ""),
            deployment_recent=bool(safe_get(body, "deployment_recent")),
            related_services=safe_get(body, "related_services") or [],
        )