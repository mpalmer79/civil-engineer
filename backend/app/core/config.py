"""Application configuration for the Civil Engineer AI backend.

Settings are read from environment variables (and an optional .env file), with
sensible local defaults so the backend runs out of the box.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings sourced from the environment or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    PROJECT_NAME: str = "Civil Engineer AI Backend"
    PHASE: str = "10"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./civil_engineer_ai.db"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # AI provider configuration. The default is the deterministic mock provider
    # so the project runs and tests pass without any paid API key. Live calls
    # are disabled by default and require both a provider key and an explicit
    # opt in. Only the OpenAI live provider is implemented today.
    AI_PROVIDER: str = "mock"
    AI_MODEL: str = "mock-review-v1"
    AI_ENABLE_LIVE_CALLS: bool = False
    OPENAI_API_KEY: str = ""
    PROMPT_VERSION: str = "checklist_review_v1"

    @property
    def cors_origins_list(self) -> list[str]:
        """Return the configured CORS origins as a list."""

        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()
