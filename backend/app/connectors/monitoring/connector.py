"""
MonitoringConnector — ingests alert/metric webhook payloads (Datadog, PagerDuty,
Prometheus webhook, or any metric/error-rate alert) and normalizes them into
canonical events. This is the primary connector behind the ACME DIGITAL demo.
"""
from typing import Dict

from app.connectors.base import (
    BaseConnector,
    ConnectorStatus,
    ConnectorCapability,
    AuthType,
    ValidationResult,
    HealthCheckResult,
    NexusCanonicalEvent,
)
from app.connectors.base.events import build_canonical_event, safe_get, try_json

SOURCE_TYPE = "monitoring"


class MonitoringConnector(BaseConnector):
    connector_type = SOURCE_TYPE
    display_name = "Monitoring & Alerts"
    description = "Ingests metric / error-rate / alert webhook payloads from monitoring systems."
    auth_type = AuthType.HMAC_SIGNATURE
    capabilities = [ConnectorCapability.READ_EVENTS,
                    ConnectorCapability.WRITE_EVENTS,
                    ConnectorCapability.SUBSCRIBE,
                    ConnectorCapability.HEALTH_CHECK]

    async def validate_credentials(self) -> ValidationResult:
        secret = self.config.get("secret")
        webhook_token = self.config.get("webhook_token")
        if not secret and not webhook_token:
            return ValidationResult(valid=False, message="Monitoring connector requires a 'secret' or 'webhook_token'.")
        return ValidationResult(valid=True, message="Monitoring credentials valid")

    async def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(
            healthy=True,
            status=ConnectorStatus.CONNECTED.value,
            latency_ms=10,
            detail="Monitoring webhook reachable (static)",
        )

    def normalize_event(self, raw_payload: Dict) -> NexusCanonicalEvent:
        body = try_json(raw_payload)
        if not isinstance(body, dict):
            body = {"raw": body}

        # Support both rich webhook payloads and simple {resource, summary, severity} dicts.
        event_title = safe_get(body, "title") or safe_get(body, "event", "title") or ""
        resource = safe_get(body, "resource") or safe_get(body, "hostname") or \
                   safe_get(body, "alert", "hostname") or safe_get(body, "service") or "unknown"
        severity_raw = safe_get(body, "severity") or safe_get(body, "priority") or \
                       safe_get(body, "alert", "severity")
        summary = safe_get(body, "summary") or safe_get(body, "description") or \
                  safe_get(body, "message") or safe_get(body, "alert", "message") or event_title
        error_rate = safe_get(body, "error_rate") or safe_get(body, "metrics", "error_rate")
        event_type = safe_get(body, "event_type") or safe_get(body, "alert_type") or "metric_alert"
        deployment_recent = bool(safe_get(body, "deployment_recent", default=False))
        related = safe_get(body, "related_services") or safe_get(body, "affected_services") or []

        if isinstance(error_rate, (dict, list)):
            error_rate = None

        return build_canonical_event(
            connector_type=SOURCE_TYPE,
            connector_id=self.config.get("connector_id", ""),
            event_type=str(event_type),
            resource=str(resource),
            summary=str(summary),
            severity=severity_raw,
            text_for_severity=str(summary),
            error_rate=str(error_rate) if error_rate is not None else None,
            metadata={"title": event_title, "metrics": safe_get(body, "metrics", default={})},
            raw_payload=body,
            source_event_id=str(safe_get(body, "source_event_id") or safe_get(body, "id") or ""),
            deployment_recent=deployment_recent,
            related_services=list(related) if isinstance(related, list) else [],
        )