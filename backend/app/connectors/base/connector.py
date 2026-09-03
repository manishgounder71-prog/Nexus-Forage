"""
BaseConnector — abstract contract every connector adapter implements.

Connectors translate external system integrations into canonical, normalized
events and (optionally) expose notification / action capabilities. Capabilities
that a connector does not support raise NotImplementedError.
"""
import abc
from typing import Dict, List, Optional

from .schemas import (
    AuthType,
    ConnectorCapability,
    ConnectorStatus,
    ConnectorType,
    ConnectorConfig,
    NexusCanonicalEvent,
    HealthCheckResult,
    ActionResult,
    ActionRequest,
    ValidationResult,
)
from .permissions import PermissionSet


class BaseConnector(abc.ABC):
    connector_type: str = ConnectorType.OTHER.value
    display_name: str = "Connector"
    description: str = ""
    auth_type: AuthType = AuthType.NONE
    capabilities: list = [ConnectorCapability.READ_EVENTS, ConnectorCapability.HEALTH_CHECK]

    def __init__(self, connector_config: Optional[ConnectorConfig] = None, **config_overrides):
        self.config = connector_config or ConnectorConfig()
        if config_overrides:
            for k, v in config_overrides.items():
                setattr(self.config, k, v)
        self.connection_status: ConnectorStatus = ConnectorStatus.DISCONNECTED
        self.permissions = PermissionSet(
            permissions=getattr(self.config, "permissions", None),
            allowed_agents=getattr(self.config, "allowed_agents", None),
        )

    # ── Lifecycle ──────────────────────────────────────────────
    async def connect(self) -> ConnectorStatus:
        """Establishes the connection. Default: validates, marks CONNECTED."""
        validation = await self.validate_credentials()
        if not validation.valid:
            self.connection_status = ConnectorStatus.AUTH_ERROR
        else:
            self.connection_status = ConnectorStatus.CONNECTED
        return self.connection_status

    async def disconnect(self) -> bool:
        self.connection_status = ConnectorStatus.DISCONNECTED
        return True

    @abc.abstractmethod
    async def validate_credentials(self) -> ValidationResult:
        """Validates whether stored credentials are usable."""

    # ── Health ─────────────────────────────────────────────────
    @abc.abstractmethod
    async def health_check(self) -> HealthCheckResult:
        """Returns the connector's current health."""

    # ── Events ─────────────────────────────────────────────────
    def receive_event(self, raw_payload: Dict) -> NexusCanonicalEvent:
        """Alias for normalize_event. Concrete connectors implement normalize_event."""
        return self.normalize_event(raw_payload)

    @abc.abstractmethod
    def normalize_event(self, raw_payload: Dict) -> NexusCanonicalEvent:
        """Maps an external payload to a canonical NexusCanonicalEvent."""

    async def subscribe(self, event_types: List[str]) -> bool:
        raise NotImplementedError(f"{self.display_name} does not support subscriptions")

    async def unsubscribe(self, event_types: List[str]) -> bool:
        raise NotImplementedError(f"{self.display_name} does not support unsubscriptions")

    # ── Capabilities / meta ────────────────────────────────────
    def get_capabilities(self) -> List[ConnectorCapability]:
        return list(self.capabilities)

    def get_permissions(self) -> PermissionSet:
        return self.permissions

    # ── Optional actions ───────────────────────────────────────
    async def send_notification(self, message: Dict) -> bool:
        raise NotImplementedError(f"{self.display_name} does not support notifications")

    async def request_action(self, action_request: ActionRequest) -> ActionResult:
        raise NotImplementedError(f"{self.display_name} does not support action execution")


# Re-export for convenience
__all__ = ["BaseConnector", "ConnectorStatus", "ConnectorType", "ConnectorConfig",
           "ConnectorCapability", "AuthType", "HealthCheckResult", "ActionResult",
           "ActionRequest", "ValidationResult", "PermissionSet", "NexusCanonicalEvent"]