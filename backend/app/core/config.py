import os
import json
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "NEXUS FORGE — Autonomous Crisis Command"
    VERSION: str = "3.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    ENV: str = "development"
    DEMO_MODE: bool = True
    CORS_ORIGINS: Union[str, List[str]] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str], None]) -> List[str]:
        if v is None:
            return ["*"]
        if isinstance(v, str):
            v = v.strip()
            if not v or v == "*":
                return ["*"]
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    clean = v[1:-1].replace("'", "").replace('"', "")
                    return [item.strip() for item in clean.split(",") if item.strip()]
            return [item.strip() for item in v.split(",") if item.strip()]
        elif isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        return ["*"]

    # Omi Voice Engine Config (set via .env or environment variables)
    OMI_API_KEY: str = os.getenv("OMI_API_KEY", "")
    OMI_API_URL: str = os.getenv("OMI_API_URL", "https://api.omi.me/v1")

    # Lyzr Agent Framework Config (set via .env or environment variables)
    LYZR_API_KEY: str = os.getenv("LYZR_API_KEY", "")
    LYZR_BASE_URL: str = os.getenv("LYZR_BASE_URL", "https://agent-prod.studio.lyzr.ai")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Gemini LLM Config (set via .env or environment variables)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Qdrant Vector Memory Config (set via .env or environment variables)
    QDRANT_URL: str = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./nexus_forge.db")

    # ═══ Connector Platform Settings ═══
    WEBHOOK_SECRET_KEY: str = os.getenv("WEBHOOK_SECRET_KEY", "nexus-webhook-secret-dev-key-change-in-prod")
    CREDENTIAL_ENCRYPTION_KEY: str = os.getenv("CREDENTIAL_ENCRYPTION_KEY", "nexus-cred-enc-key-32bytes-change!")
    MAX_WEBHOOK_BODY_SIZE: int = int(os.getenv("MAX_WEBHOOK_BODY_SIZE", "1048576"))  # 1MB
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    DEMO_ORG_ID: str = os.getenv("DEMO_ORG_ID", "org_acme_digital")

    model_config = SettingsConfigDict(
        env_file=[
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
            ".env"
        ],
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
