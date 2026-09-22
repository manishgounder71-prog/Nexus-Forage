"""
GitHubConnector — normalizes GitHub webhook events (deploy, push, issue, alert)
into canonical events, with strong deployment-recency signals used by the
correlation engine.
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
from app.connectors.base.events import build_canonical_event, safe_get, try_json

SOURCE_TYPE = "github"


class GitHubConnector(BaseConnector):
    connector_type = SOURCE_TYPE
    display_name = "GitHub"
    description = "Deployment, push, issue and security-alert webhooks from GitHub."
    auth_type = AuthType.HMAC_SIGNATURE
    capabilities = [ConnectorCapability.READ_EVENTS,
                    ConnectorCapability.WRITE_EVENTS,
                    ConnectorCapability.SUBSCRIBE,
                    ConnectorCapability.HEALTH_CHECK]

    async def validate_credentials(self) -> ValidationResult:
        secret = self.config.get("secret")
        if not secret:
            return ValidationResult(valid=False, message="GitHub connector requires a webhook 'secret'.")
        return ValidationResult(valid=True, message="GitHub credentials valid")

    async def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(healthy=True, status=ConnectorStatus.CONNECTED.value, latency_ms=25)

    def normalize_event(self, raw_payload: Dict) -> NexusCanonicalEvent:
        body = try_json(raw_payload)
        if not isinstance(body, dict):
            body = {"raw": body}

        action = safe_get(body, "action") or ""
        deployment_status = safe_get(body, "deployment_status", "state") or ""
        repo_name = safe_get(body, "repository", "full_name") or safe_get(body, "repository", "name") or "unknown"

        if deployment_status or "deployment" in body:
            event_type = "deployment"
            resource = f"{repo_name}@{safe_get(body, 'deployment', 'ref') or 'main'}"
            severity = "high" if str(deployment_status).lower() != "success" else "info"
            summary = f"Deployment {deployment_status or 'in progress'} on {repo_name}"
            metadata = {"deployment_status": deployment_status, "ref": safe_get(body, "deployment", "ref")}
            deployment_recent = True
        elif action and "issue" in body or "pull_request" in body:
            event_type = f"issue_{action}" if "issue" in body else f"pr_{action}"
            resource = repo_name
            severity = "info"
            summary = f"{event_type.replace('_', ' ').title()} on {repo_name}: {safe_get(body, 'issue', 'title') or safe_get(body, 'pull_request', 'title') or ''}"
            metadata = {"action": action, "number": safe_get(body, "issue", "number") or safe_get(body, "pull_request", "number")}
            deployment_recent = False
        else:
            event_type = "push" if "head_commit" in body or "commits" in body else (f"{action}" if action else "event")
            ref = safe_get(body, "ref") or ""
            resource = f"{repo_name}{ref}" if ref else repo_name
            severity = "info"
            summary = f"GitHub {event_type} on {repo_name}"
            metadata = {"ref": ref, "actor": safe_get(body, "sender", "login")}
            deployment_recent = "refs/heads/main" in str(ref) or "refs/heads/prod" in str(ref)

        payload_related = safe_get(body, "related_services") or []
        if not isinstance(payload_related, list):
            payload_related = [payload_related]
        related_services = list(dict.fromkeys([repo_name] + [str(r) for r in payload_related]))

        return build_canonical_event(
            connector_type=SOURCE_TYPE,
            connector_id=self.config.get("connector_id", ""),
            event_type=event_type,
            resource=str(resource),
            summary=str(summary)[:400],
            severity=severity,
            metadata=metadata,
            raw_payload=body,
            source_event_id=str(safe_get(body, "id") or ""),
            deployment_recent=deployment_recent,
            related_services=related_services,
        )