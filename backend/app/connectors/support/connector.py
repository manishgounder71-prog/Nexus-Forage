"""
SupportConnector — ingests support-ticket / complaint webhook payloads and
normalizes them into canonical events with business-impact signals used by the
correlation engine (e.g., customer complaint spikes).
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

SUPPORT_TYPE = "support"


class SupportConnector(BaseConnector):
    connector_type = SUPPORT_TYPE
    display_name = "Support & Ticketing"
    description = "Support queue / complaint webhooks (Zendesk, Zoho, custom ticketing)."
    auth_type = AuthType.HMAC_SIGNATURE
    capabilities = [ConnectorCapability.READ_EVENTS, ConnectorCapability.HEALTH_CHECK]

    async def validate_credentials(self) -> ValidationResult:
        secret = self.config.get("secret") or self.config.get("webhook_token")
        if not secret:
            return ValidationResult(valid=False, message="Support connector requires a 'secret' or 'webhook_token'.")
        return ValidationResult(valid=True, message="Support credentials valid")

    async def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(healthy=True, status=ConnectorStatus.CONNECTED.value, latency_ms=12)

    def normalize_event(self, raw_payload: Dict) -> NexusCanonicalEvent:
        body = try_json(raw_payload)
        if not isinstance(body, dict):
            body = {"raw": body}

        ticket_id = safe_get(body, "ticket_id") or safe_get(body, "id_no") or safe_get(body, "id") or ""
        subject = safe_get(body, "subject") or safe_get(body, "title") or ""
        message = safe_get(body, "message") or safe_get(body, "content") or subject
        submitted_count = safe_get(body, "submitted_count", default=1)
        resource = safe_get(body, "product") or safe_get(body, "service") or "support"

        lowered = f"{subject} {message}".lower()
        if any(k in lowered for k in ["payment", "billing", "charge", "declined"]):
            domain_signal = "payment"
        elif any(k in lowered for k in ["login", "auth", "account", "access"]):
            domain_signal = "auth"
        else:
            domain_signal = "support"

        return build_canonical_event(
            connector_type=SUPPORT_TYPE,
            connector_id=self.config.get("connector_id", ""),
            event_type="support_complaint",
            resource=str(resource),
            summary=f"{subject or 'Support ticket'} {f'#{ticket_id}' if ticket_id else ''}".strip(),
            severity=safe_get(body, "severity") or "medium",
            text_for_severity=f"{subject} {message}",
            metadata={
                "ticket_id": ticket_id,
                "submitted_count": submitted_count,
                "domain_signal": domain_signal,
            },
            raw_payload=body,
            source_event_id=str(safe_get(body, "source_event_id") or ticket_id),
            deployment_recent=False,
            related_services=[str(resource)],
        )