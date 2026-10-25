"""Typed application settings loaded from environment variables / .env."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProvider = Literal["gemini", "groq"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    llm_provider: LLMProvider = "gemini"
    llm_fallback_enabled: bool = True
    llm_temperature: float = 0.2
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 2
    gemini_model: str = "gemini-2.5-flash"
    groq_model: str = "llama-3.3-70b-versatile"
    embedding_model: str = "gemini-embedding-001"
    google_api_key: SecretStr | None = None
    groq_api_key: SecretStr | None = None

    # Tools
    tavily_api_key: SecretStr | None = None

    # Observability
    langsmith_tracing: bool = False
    langsmith_api_key: SecretStr | None = None
    langsmith_project: str = "job-hunt-copilot"

    # App
    log_level: str = "INFO"
    database_url: str = "sqlite:///data/copilot.db"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (one per process)."""
    return Settings()
