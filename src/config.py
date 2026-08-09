"""Configuration management for DocuMesh."""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App info
    app_name: str = "DocuMesh Engine"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    # Default to local SQLite database in project directory
    database_url: str = "sqlite+aiosqlite:///./documesh.db"

    # LLM Settings
    openai_api_key: str = ""
    default_model: str = "gpt-4o-mini"
    fallback_model: str = "gpt-3.5-turbo"
    mock_llm_if_no_key: bool = True  # Allows running offline tests without an API key

    # Direct paths
    seed_corpus_dir: str = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"

    # Multi-tenancy
    default_tenant_id: str = "tenant_default"
    default_project_id: str = "proj_greenfield_tech_park"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
