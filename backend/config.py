# backend/config.py

# This file manages application configuration and environment variables
# using pydantic-settings, ensuring model names and endpoints are configurable.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "qwen2.5-coder:3b"
    llm_api_key: str = "ollama"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
