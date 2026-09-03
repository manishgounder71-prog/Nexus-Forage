import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "NEXUS FORGE — Autonomous Crisis Command"
    VERSION: str = "3.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    ENV: str = "development"
    DEMO_MODE: bool = True
    CORS_ORIGINS: List[str] = ["*"]

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

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
