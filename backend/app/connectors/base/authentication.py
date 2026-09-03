"""
Authentication primitives for connectors.

Defines supported auth strategies and how to validate a provided credential set
without necessarily making a network call (e.g., field-presence checks that the
API layer can run before a `connect()`/`test` attempt).
"""
from typing import Any, Dict, List, Optional

from .schemas import AuthType, ValidationResult


REQUIRED_FIELDS = {
    AuthType.NONE: [],
    AuthType.API_KEY_HEADER: ["api_key"],
    AuthType.BEARER_TOKEN: ["token"],
    AuthType.BASIC: ["username", "password"],
    AuthType.OAUTH2: ["client_id", "client_secret", "token_url"],
    AuthType.HMAC_SIGNATURE: ["secret"],
}


def validate_credentials_for_auth(auth_type: AuthType, config: Dict[str, Any]) -> ValidationResult:
    """Structural credential check. Returns valid=True when required fields are present."""
    missing = []
    for field in REQUIRED_FIELDS.get(auth_type, []):
        value = config.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            missing.append(field)
    if missing:
        return ValidationResult(
            valid=False,
            message=f"Missing required credential field(s): {', '.join(missing)}",
            errors=missing,
        )
    return ValidationResult(valid=True, message="Credentials structurally valid")


def redact_credentials(config: Dict[str, Any], secrets: Optional[List[str]] = None) -> Dict[str, Any]:
    """Returns a copy of `config` with known credential fields masked to '••••'."""
    secret_keys = set(secrets or []) | {"api_key", "token", "password", "secret",
                                        "client_secret", "refresh_token", "access_token"}
    redacted = {}
    for k, v in config.items():
        redacted[k] = "••••" if k in secret_keys and v else v
    return redacted


def merge_config_storage(config: Dict[str, Any], secrets: Optional[List[str]] = None) -> Dict[str, Any]:
    """Encrypts credential-bearing fields for at-rest storage.

    Callers should pass a list of field names to encrypt. Values are transformed
    into `enc:<token>` strings via `encrypt_credential`.
    """
    from app.core.security import encrypt_credential
    secret_keys = set(secrets or []) | {"api_key", "token", "password", "secret", "client_secret"}
    merged = dict(config)
    for k in list(merged.keys()):
        v = merged[k]
        if k in secret_keys and isinstance(v, str) and v and not v.startswith("enc:"):
            merged[k] = encrypt_credential(v)
    return merged