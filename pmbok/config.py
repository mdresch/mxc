"""Environment-variable-backed settings for the PMBOK system."""

import os
from pathlib import Path
from typing import ClassVar

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from pmbok.models.enums import AuditMode


class Settings(BaseSettings):
    """
    Reads configuration from environment variables with sensible defaults.
    All fields can be overridden by setting the corresponding env var with ADPA_ prefix.

    Azure AI Foundry (cloud):
        PROJECT_ENDPOINT        https://<project>.services.ai.azure.com
        MODEL_DEPLOYMENT_NAME   gpt-4.1-mini
        USE_LOCAL_FOUNDRY       false
        ADPA_AUDIT_MODE         blocking | advisory

    Local AI Foundry / Phi-4:
        USE_LOCAL_FOUNDRY           true
        LOCAL_FOUNDRY_URL           http://127.0.0.1:50268
        LOCAL_MODEL_DEPLOYMENT_NAME phi-4
    """

    # ── Audit Mode ───────────────────────────────────────────────────────────

    AUDIT_MODE: AuditMode = Field(default=AuditMode.BLOCKING)

    @field_validator("AUDIT_MODE", mode="before")
    @classmethod
    def validate_audit_mode(cls, value):
        if isinstance(value, AuditMode):
            return value
        if isinstance(value, str):
            value = value.strip().lower()
            if value in {"blocking", "advisory"}:
                return AuditMode(value)
        raise ValueError("AUDIT_MODE must be 'blocking' or 'advisory'")

    # ── LLM backend ───────────────────────────────────────────────────────────

    # Cloud: Azure AI Foundry project endpoint
    PROJECT_ENDPOINT: str = Field(default="")

    # Cloud: model deployment name
    MODEL_DEPLOYMENT_NAME: str = Field(default="gpt-4.1-mini")

    # Local: use local AI Foundry instead of cloud
    USE_LOCAL_FOUNDRY: bool = Field(default=False)

    # Local: base URL of the local Foundry server
    LOCAL_FOUNDRY_URL: str = Field(default="http://127.0.0.1:50268")

    # Local: model name served by the local Foundry
    LOCAL_MODEL_DEPLOYMENT_NAME: str = Field(default="phi-4")

    # Legacy / Ollama fallback
    LLM_ENDPOINT: str = Field(default="http://localhost:11434/v1")

    # ── OCR ───────────────────────────────────────────────────────────────────

    OCR_ENGINE: str = Field(default="tesseract")

    # ── Storage ───────────────────────────────────────────────────────────────

    STORAGE_PATH: Path = Field(default=Path(".pmbok_store"))

    # ── Retry ─────────────────────────────────────────────────────────────────

    RETRY_MAX_ATTEMPTS: int = Field(default=3)
    RETRY_MIN_WAIT: float = Field(default=2.0)
    RETRY_MAX_WAIT: float = Field(default=30.0)

    # ── Stale process alerting ────────────────────────────────────────────────

    STALE_PROCESS_THRESHOLD_HOURS: float = Field(default=24.0)

    class Config:
        env_prefix = "ADPA_"
        case_sensitive = False


# Module-level singleton
settings = Settings()
