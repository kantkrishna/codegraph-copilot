# backend/config.py

# This file manages application configuration and environment variables
# using pydantic-settings, ensuring model names and endpoints are configurable.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "qwen2.5-coder:3b"
    llm_api_key: str = "ollama"

    # Neo4j Graph Database Settings
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
