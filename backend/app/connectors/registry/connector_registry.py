"""
ConnectorRegistry — central registry of available connector adapters.

Holds factory references (class + config schema) for each connector type, and
provides instantiation + metadata lookups used by the API layer and demo.
"""
from typing import Dict, List, Optional, Type
from app.connectors.base import BaseConnector, ConnectorConfig, ValidationResult

# connector_type -> class lookup helper (avoid circular import at module load)
_FACTORY = {
    "github": ("app.connectors.github.connector", "GitHubConnector"),
    "slack": ("app.connectors.slack.connector", "SlackConnector"),
    "monitoring": ("app.connectors.monitoring.connector", "MonitoringConnector"),
    "webhook": ("app.connectors.webhook.connector", "UniversalWebhookConnector"),
    "custom_api": ("app.connectors.custom_api.connector", "CustomAPIConnector"),
    "support": ("app.connectors.support.connector", "SupportConnector"),
}


def _import_class(module_name: str, class_name: str) -> Type[BaseConnector]:
    import importlib
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


class ConnectorRegistry:
    def __init__(self):
        self._connector_classes: Dict[str, Type[BaseConnector]] = {}
        for ctype in _FACTORY:
            try:
                mod, cls = _FACTORY[ctype]
                self._connector_classes[ctype] = _import_class(mod, cls)
            except Exception as e:  # pragma: no cover - dev fallback
                print(f"[ConnectorRegistry] Failed to load {ctype}: {e}")

    # ── Registration / listing ─────────────────────────────────
    def register(self, connector_type: str, connector_class: Type[BaseConnector]) -> None:
        self._connector_classes[connector_type] = connector_class

    def available_types(self) -> List[str]:
        return list(self._connector_classes.keys())

    def get_class(self, connector_type: str) -> Optional[Type[BaseConnector]]:
        return self._connector_classes.get(connector_type)

    # ── Catalog ────────────────────────────────────────────────
    def catalog(self) -> List[dict]:
        items = []
        for ctype, cls in self._connector_classes.items():
            try:
                items.append({
                    "type": ctype,
                    "display_name": cls.display_name,
                    "description": getattr(cls, "description", ""),
                    "auth_type": getattr(cls, "auth_type", "none").value
                        if hasattr(getattr(cls, "auth_type", None), "value") else "none",
                    "capabilities": [c.value for c in getattr(cls, "capabilities", [])],
                })
            except Exception:
                continue
        return items

    # ── Instantiation ──────────────────────────────────────────
    async def create_connector(self, connector_type: str, config: dict) -> BaseConnector:
        cls = self._connector_classes.get(connector_type)
        if cls is None:
            raise ValueError(f"Unknown connector type: {connector_type}")
        cc = build_connector_config(connector_type, config)
        return cls(cc)

    def validate_type(self, connector_type: str) -> bool:
        return connector_type in self._connector_classes


def build_connector_config(connector_type: str, config: dict) -> ConnectorConfig:
    """Builds a ConnectorConfig carrying both generic fields and type-specific keys (in custom)."""
    known = {"name", "description", "enabled", "permissions", "allowed_agents",
             "allowed_event_types", "rate_limit", "health_check_interval"}
    base = {k: config[k] for k in known if k in config}
    extra = {k: v for k, v in config.items() if k not in known}
    return ConnectorConfig(connector_type=connector_type, **base, custom=extra)


connector_registry = ConnectorRegistry()


async def validate_connector_credentials(connector_type: str, config: dict) -> ValidationResult:
    """Validates credentials structurally for a given connector type (no network call)."""
    cls = connector_registry.get_class(connector_type)
    if cls is None:
        return ValidationResult(valid=False, message=f"Unknown connector type: {connector_type}")
    conn = await connector_registry.create_connector(connector_type, config)
    return await conn.validate_credentials()