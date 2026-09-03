import uuid
import hmac
import hashlib
import base64
from secrets import token_hex
from typing import Optional
from datetime import datetime, timezone, timedelta
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings


def generate_uuid() -> str:
    return str(uuid.uuid4())


def get_current_timestamp() -> str:
    return datetime.utcnow().isoformat()


# ═══════════════════════════════════════════════════════════════
# Credential encryption (Fernet at rest)
# ═══════════════════════════════════════════════════════════════

_fernet = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = settings.CREDENTIAL_ENCRYPTION_KEY
        if len(key.encode("utf-8")) != 44:
            # Derive a stable 32-byte key to build a valid url-safe base64 Fernet key.
            digest = hashlib.sha256(key.encode("utf-8")).digest()
            key = base64.urlsafe_b64encode(digest)
        _fernet = Fernet(key)
    return _fernet


def encrypt_credential(plaintext: str) -> str:
    """Encrypts a secret at rest using Fernet (symmetric). Token is prefixed `enc:`."""
    if plaintext is None or plaintext == "":
        return plaintext
    token = _get_fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")
    return f"enc:{token}"


def decrypt_credential(value: str) -> str:
    """Decrypts a Fernet token previously produced by encrypt_credential."""
    if value is None or value == "":
        return value
    if not value.startswith("enc:"):
        return value
    raw = value[4:]
    try:
        return _get_fernet().decrypt(raw.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        raise ValueError("Credential decryption failed: invalid encryption key or corrupted token.")


# ═══════════════════════════════════════════════════════════════
# Webhook tokens & HMAC signatures
# ═══════════════════════════════════════════════════════════════

def hash_webhook_token(token: str) -> str:
    """Hashes a webhook token for storage (never store raw)."""
    return hashlib.sha256(f"{settings.WEBHOOK_SECRET_KEY}:{token}".encode("utf-8")).hexdigest()


def verify_webhook_token(token: str, token_hash: Optional[str]) -> bool:
    if not token_hash:
        return False
    return hmac.compare_digest(hash_webhook_token(token), token_hash)


def generate_webhook_token() -> str:
    return token_hex(32)


def compute_hmac_signature(payload_body: bytes, token: Optional[str] = None) -> str:
    """Computes an HMAC-SHA256 signature over the raw body using the webhook secret (+ optional token)."""
    key = settings.WEBHOOK_SECRET_KEY if token is None else f"{settings.WEBHOOK_SECRET_KEY}:{token}"
    return "sha256=" + hmac.new(key.encode("utf-8"), payload_body, hashlib.sha256).hexdigest()


def verify_hmac_signature(payload_body: bytes, signature: Optional[str], token: Optional[str] = None) -> bool:
    """Verifies an X-Nexus-Signature header against the raw body."""
    if not signature:
        return False
    expected = compute_hmac_signature(payload_body, token)
    return hmac.compare_digest(signature, expected)


def compute_dedupe_hash(connector_id: str, event_type: str, resource: Optional[str], source_event_id: Optional[str]) -> str:
    """Stable hash used for event deduplication (avoid double-processing)."""
    raw = "|".join(filter(None, [connector_id, event_type, resource or "", source_event_id or ""]))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def validate_timestamp_freshness(timestamp: Optional[str], max_age_seconds: int = 300) -> bool:
    """Rejects message replay by ensuring the provided timestamp is within max_age_seconds of now."""
    if not timestamp:
        return False
    try:
        # Support unix epoch seconds or ISO8601
        if timestamp.isdigit():
            epoch = float(timestamp)
            ts = datetime.fromtimestamp(epoch, tz=timezone.utc)
        else:
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except (ValueError, TypeError, OverflowError):
        return False
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    # Allow a small clock-skew tolerance forward (60s) but reject anything older than max_age.
    return ts <= now + timedelta(seconds=60) and ts >= now - timedelta(seconds=abs(max_age_seconds))


def generate_public_org_id(slug: Optional[str] = None) -> str:
    """Generates an opaque, public organization identifier safe for external webhook URLs."""
    prefix = f"org_{slug[:10]}_" if slug else "org_"
    return f"{prefix}{uuid.uuid4().hex[:12]}"


def generate_ingestion_secret() -> str:
    """Generates a high-entropy secret for HMAC-SHA256 webhook signature validation."""
    return f"whsec_{token_hex(24)}"


def compute_org_webhook_signature(timestamp: str, raw_body: bytes, secret: str) -> str:
    """
    Computes standard HMAC-SHA256 signature from timestamp + raw request body.
    Supports either 'sha256=<hex>' or raw hex matching.
    """
    to_sign = f"{timestamp}.".encode("utf-8") + raw_body
    h = hmac.new(secret.encode("utf-8"), to_sign, hashlib.sha256).hexdigest()
    return f"sha256={h}"


def verify_org_webhook_signature(timestamp: str, raw_body: bytes, signature: Optional[str], secret: str) -> bool:
    """
    Verifies HMAC-SHA256 signature using constant-time comparison.
    Accepts signatures with or without the 'sha256=' prefix, and over timestamp+body or timestamp.body.
    """
    if not signature or not secret or not timestamp:
        return False

    sig_clean = signature.replace("sha256=", "").strip()

    # Strategy 1: timestamp.body
    cand1 = hmac.new(secret.encode("utf-8"), f"{timestamp}.".encode("utf-8") + raw_body, hashlib.sha256).hexdigest()
    if hmac.compare_digest(sig_clean, cand1):
        return True

    # Strategy 2: timestamp + body
    cand2 = hmac.new(secret.encode("utf-8"), timestamp.encode("utf-8") + raw_body, hashlib.sha256).hexdigest()
    if hmac.compare_digest(sig_clean, cand2):
        return True

    # Strategy 3: raw body only (for simpler providers)
    cand3 = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig_clean, cand3)