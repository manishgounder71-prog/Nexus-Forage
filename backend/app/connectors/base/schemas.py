"""
Connector SDK — shared schemas, enums, and event model.

These Pydantic models are the canonical contract every connector adapter is
normalized into before entering the event pipeline.
"""
import enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConnectorType(str, enum.Enum):
    GITHUB = "github"
    SLACK = "slack"
    MONITORING = "monitoring"        # webhook-based metric/alert source (e.g. Datadog)
    WEBHOOK = "webhook"              # universal webhook
    CUSTOM_API = "custom_api"        # build-your-own REST API
    SUPPORT = "support"              # ticketing / support queue webhook
    EMAIL = "email"
    DATABASE = "database"
    OTHER = "other"


class ConnectorStatus(str, enum.Enum):
    CONNECTED = "CONNECTED"
    DEGRADED = "DEGRADED"
    AUTH_ERROR = "AUTH_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    DISCONNECTED = "DISCONNECTED"
    UNKNOWN = "UNKNOWN"


class AuthType(str, enum.Enum):
    NONE = "none"
    API_KEY_HEADER = "api_key_header"
    BEARER_TOKEN = "bearer"
    BASIC = "basic"
    OAUTH2 = "oauth2"
    HMAC_SIGNATURE = "hmac_signature"


class ConnectorCapability(str, enum.Enum):
    READ_EVENTS = "read_events"
    WRITE_EVENTS = "write_events"
    SEND_NOTIFICATION = "send_notification"
    REQUEST_ACTION = "request_action"
    HEALTH_CHECK = "health_check"
    SUBSCRIBE = "subscribe"


class ConnectorPermission(str, enum.Enum):
    READ = "read"
    PROPOSE = "propose"
    EXECUTE = "execute"


class RiskClass(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConnectorConfig(BaseModel):
    """Base configuration carried by every connector. Concrete schemas extend this."""
    name: str = ""
    description: str = ""
    enabled: bool = True
    connector_type: str = ConnectorType.WEBHOOK.value
    permissions: Dict[str, bool] = Field(default_factory=lambda: {"read": True, "propose": True, "execute": False})
    allowed_agents: List[str] = Field(default_factory=list)
    allowed_event_types: List[str] = Field(default_factory=list)
    rate_limit: int = 60
    health_check_interval: int = 300
    # Type-specific fields (base_url, api_key, headers, event schema, webhook_url, etc.)
    custom: Dict[str, Any] = Field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Returns a custom/type-specific config value."""
        return self.custom.get(key, default)


class ValidationResult(BaseModel):
    valid: bool = False
    message: str = ""
    errors: List[str] = Field(default_factory=list)


class HealthCheckResult(BaseModel):
    healthy: bool = False
    status: str = ConnectorStatus.UNKNOWN.value
    latency_ms: int = 0
    detail: str = ""


class ActionResult(BaseModel):
    success: bool = False
    message: str = ""
    approval_required: bool = False
    approval_state: str = "NONE"  # NONE, WAITING_FOR_APPROVAL, APPROVED, DENIED
    action_id: Optional[str] = None
    reference: Optional[str] = None


class ActionRequest(BaseModel):
    """A requested operational action scoped to a connector (used for EXECUTE)."""
    connector_id: str
    action: str                      # e.g. restart, rollout, isolate, ack
    target_resource: str = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)
    requester_agent_id: str = ""     # which agent proposed/requested it
    mission_id: str = ""
    org_id: str = ""


class NexusCanonicalEvent(BaseModel):
    """The normalized event contract produced by every connector."""
    connector_type: str
    connector_id: str
    event_type: str
    severity: str = "info"                     # info, low, medium, high, critical
    resource: str = ""                          # system/service being affected
    summary: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    source_event_id: str = ""
    received_at: str = Field(default_factory=utc_now_iso)
    dedupe_hash: str = ""
    # Deployment lifecycle / business impact signals (used by correlator)
    deployment_recent: bool = False
    related_services: List[str] = Field(default_factory=list)
    error_rate: Optional[str] = None          # e.g. "47%" or "0.47"
    avg_latency_ms: Optional[float] = None     # e.g. 2400.0

    class Config:
        arbitrary_types_allowed = True


def normalize_severity(raw: Any) -> str:
    """Coerces arbitrary severity input to a canonical level."""
    if raw is None:
        return "info"
    s = str(raw).strip().lower()
    if s in ("critical", "p1", "severe", "crash", "outage", "sev1"):
        return "critical"
    if s in ("high", "p2", "major", "error", "sev2"):
        return "high"
    if s in ("medium", "p3", "warning", "warn", "degraded", "sev3"):
        return "medium"
    if s in ("low", "p4", "notice", "info", "sev4"):
        return "info"
    return "info"


def infer_severity_from_text(text: str, error_rate: Optional[str] = None) -> str:
    """Heuristic severity inference for generic webhook payloads."""
    lowered = (text or "").lower()
    if error_rate and "%" in error_rate:
        try:
            rate = float(error_rate.replace("%", "").strip())
            if rate >= 40:
                return "critical"
            if rate >= 15:
                return "high"
            if rate >= 5:
                return "medium"
        except ValueError:
            pass
    if any(k in lowered for k in ["outage", "critical", "down", "failed", "breach", "attack"]):
        return "critical"
    if any(k in lowered for k in ["error", "spike", "elevated", "degraded", "exception"]):
        return "high"
    if any(k in lowered for k in ["warning", "notice", "slow", "latency"]):
        return "medium"
    return "info"