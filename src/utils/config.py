"""
Centralized type-safe configuration via Pydantic BaseSettings.
Phase 1.0.18: Establishing Environmental SSOT.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


class PhantomLogosConfig(BaseSettings):
    """
    Sovereign configuration model with env var validation.
    Maps legacy environment variables via aliases for backward compatibility.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",  # Don't fail on unknown env vars
        validate_default=True,  # Validate default values as well
    )

    # --- Infrastructure ---
    antigravity_gateway_url: str = Field(
        default="http://localhost:32553", description="Antigravity IDE local proxy endpoint"
    )
    ollama_host: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",  # Support both names, OLLAMA_BASE_URL preferred if set
        description="Ollama API endpoint",
    )

    # --- Hardware & Resource Management ---
    vram_usable_gb: float = Field(
        default=7.0,
        alias="GPU_TOTAL_VRAM_GB",
        ge=0.5,
        le=64.0,
        description="Usable VRAM (total - OS reservation). Alias supports legacy naming.",
    )

    # --- Logging & Diagnostics ---
    log_level: str = Field(default="INFO", description="System-wide logging level")

    # --- Operational Timeouts ---
    orchestrator_node_timeout: float = Field(
        default=60.0, ge=1.0, description="Max execution seconds per graph node"
    )

    @field_validator("log_level")
    @classmethod
    def _coerce_log_level(cls, v: str) -> str:
        """Ensures log level is one of the standard logging levels."""
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid:
            logger.warning(f"Invalid LOG_LEVEL='{v}', falling back to INFO")
            return "INFO"
        return v.upper()

    @field_validator("antigravity_gateway_url", "ollama_host")
    @classmethod
    def _normalize_url(cls, v: str) -> str:
        """Ensures URLs have protocols and no trailing slashes."""
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"URL must start with http/https: {v}")
        return v.rstrip("/")


# --- Lazy Singleton Loader ---
_config: PhantomLogosConfig | None = None


def load_config() -> PhantomLogosConfig:
    """
    Lazy singleton loader. Never raises — always returns a config instance.
    If validation fails, logs a warning and returns a model with defaults (model_construct).
    """
    global _config
    if _config is not None:
        return _config

    try:
        _config = PhantomLogosConfig()
    except Exception as e:
        logger.warning(f"Config validation failed, using default fallback: {e}")
        # Construct model with defaults, bypassing validation for recovery
        _config = PhantomLogosConfig.model_construct()

    return _config
