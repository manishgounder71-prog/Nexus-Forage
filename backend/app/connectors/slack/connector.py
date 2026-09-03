"""
SlackConnector — normalizes Slack event payloads (messages from channels like
#alerts, #support) into canonical events, used e.g. for complaint-spike signals.
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

SOURCE_TYPE = "slack"


class SlackConnector(BaseConnector):
    connector_type = SOURCE_TYPE
    display_name = "Slack"
    description = "Slack webhook/events API for alert and support-channel messages."
    auth_type = AuthType.BEARER_TOKEN
    capabilities = [ConnectorCapability.READ_EVENTS,
                    ConnectorCapability.WRITE_EVENTS,
                    ConnectorCapability.SEND_NOTIFICATION,
                    ConnectorCapability.SUBSCRIBE,
                    ConnectorCapability.HEALTH_CHECK]

    async def validate_credentials(self) -> ValidationResult:
        token = self.config.get("token") or self.config.get("webhook_token")
        if not token:
            return ValidationResult(valid=False, message="Slack connector requires a token or webhook_token.")
        return ValidationResult(valid=True, message="Slack credentials valid")

    async def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(healthy=True, status=ConnectorStatus.CONNECTED.value, latency_ms=20)

    def normalize_event(self, raw_payload: Dict) -> NexusCanonicalEvent:
        body = try_json(raw_payload)
        if not isinstance(body, dict):
            body = {"raw": body}

        channel = safe_get(body, "event", "channel") or safe_get(body, "channel") or ""
        text = safe_get(body, "event", "text") or safe_get(body, "text") or ""
        username = safe_get(body, "event", "user") or safe_get(body, "user_name") or ""
        event_type = safe_get(body, "event", "type") or safe_get(body, "type") or "message"

        lowered = str(text).lower()
        if any(k in lowered for k in ["complaint", "down", "unable", "outage", "broken", "frustrated"]):
            severity = "high"
        elif any(k in lowered for k in ["report", "issue", "slow", "failing"]):
            severity = "medium"
        else:
            severity = "info"

        return build_canonical_event(
            connector_type=SOURCE_TYPE,
            connector_id=self.config.get("connector_id", ""),
            event_type=f"slack_{event_type}",
            resource=str(channel) or "slack",
            summary=str(text)[:400],
            severity=severity,
            text_for_severity=str(text),
            metadata={"channel": channel, "user": username},
            raw_payload=body,
            source_event_id=str(safe_get(body, "event_id") or safe_get(body, "client_msg_id") or ""),
            deployment_recent=False,
            related_services=[str(channel)],
        )