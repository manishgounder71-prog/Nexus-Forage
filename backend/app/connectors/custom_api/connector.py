"""
CustomAPIConnector — 'Build Your Own' connector. Connects to an arbitrary REST
endpoint (with configurable auth headers), polls for events, and normalizes them.
Designed to be configured end-to-end from the frontend builder.
"""
import httpx
from typing import Dict, Optional, List

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

CUSTOM_API_TYPE = "custom_api"


class CustomAPIConnector(BaseConnector):
    connector_type = CUSTOM_API_TYPE
    display_name = "Custom API"
    description = "Connect any REST API (with headers/auth) and poll it for operational events."
    auth_type = AuthType.BEARER_TOKEN
    capabilities = [ConnectorCapability.READ_EVENTS, ConnectorCapability.HEALTH_CHECK, ConnectorCapability.SUBSCRIBE]

    async def validate_credentials(self) -> ValidationResult:
        base_url = self.config.get("base_url")
        if not base_url:
            return ValidationResult(valid=False, message="Custom API requires a base_url.")
        if not str(base_url).startswith("http"):
            return ValidationResult(valid=False, message="base_url must be an http(s) URL.")
        return ValidationResult(valid=True, message="Custom API config valid")

    async def health_check(self) -> HealthCheckResult:
        base_url = self.config.get("base_url")
        if not base_url:
            return HealthCheckResult(healthy=False, status=ConnectorStatus.DISCONNECTED.value, detail="No base_url")
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(timeout=8) as client:
                resp = await client.get(f"{base_url.rstrip('/')}/health", headers=headers)
            healthy = resp.status_code < 500
            return HealthCheckResult(
                healthy=healthy,
                status=ConnectorStatus.CONNECTED.value if healthy else ConnectorStatus.DEGRADED.value,
                latency_ms=int(resp.elapsed.total_seconds() * 1000),
                detail=f"HTTP {resp.status_code}",
            )
        except Exception as e:
            return HealthCheckResult(healthy=False, status=ConnectorStatus.DISCONNECTED.value, detail=str(e)[:200])

    def _build_headers(self) -> Dict[str, str]:
        headers = {}
        auth_type = self.auth_type
        if auth_type == AuthType.BEARER_TOKEN and self.config.get("token"):
            headers["Authorization"] = f"Bearer {self.config.get('token')}"
        elif auth_type == AuthType.API_KEY_HEADER and self.config.get("api_key"):
            header_name = self.config.get("api_key_header") or "X-API-Key"
            headers[header_name] = self.config.get("api_key")
        custom_headers = self.config.get("headers") or {}
        if isinstance(custom_headers, dict):
            headers.update(custom_headers)
        return headers

    def normalize_event(self, raw_payload: Dict) -> NexusCanonicalEvent:
        body = try_json(raw_payload)
        if not isinstance(body, dict):
            body = {"raw": body}

        type_key = self.config.get("event_type_key", "event_type")
        resource_key = self.config.get("resource_key", "resource")

        event_type = str(safe_get(body, type_key) or safe_get(body, "event_type") or "custom_event")
        resource = str(safe_get(body, resource_key) or safe_get(body, "system") or "custom")
        summary = str(safe_get(body, "summary") or safe_get(body, "message") or f"Custom API {event_type}")

        return build_canonical_event(
            connector_type=CUSTOM_API_TYPE,
            connector_id=self.config.get("connector_id", ""),
            event_type=event_type,
            resource=resource,
            summary=summary[:400],
            severity=safe_get(body, "severity"),
            text_for_severity=str(summary),
            metadata=safe_get(body, "metadata") or {},
            raw_payload=body,
            source_event_id=str(safe_get(body, "id") or safe_get(body, "source_event_id") or ""),
            deployment_recent=False,
            related_services=safe_get(body, "related_services") or [],
        )