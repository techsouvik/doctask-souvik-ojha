"""Configuration management for DocuMesh."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App info
    app_name: str = "DocuMesh Engine"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./documesh.db"

    # Multi-Model LLM Settings
    default_provider: str = "gemini"  # "gemini", "openai", "openai_compatible", "anthropic"
    openai_api_key: str = ""
    openai_base_url: str = ""        # Custom base URL (Together, Ollama, OpenRouter, vLLM)
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    google_api_key: str = ""

    default_model: str = "gemini-3.8-flash"
    default_claude_model: str = "claude-3-5-sonnet-20241022"
    default_gemini_model: str = "gemini-3.8-flash"
    fallback_model: str = "gpt-3.5-turbo"
    mock_llm_if_no_key: bool = True

    # Direct paths
    seed_corpus_dir: str = "/Users/souvikojha/doctask-souvik-ojha/test_data/greenfield_tech_park"

    # Multi-Tenancy
    default_tenant_id: str = "tenant_default"
    default_project_id: str = "proj_greenfield_tech_park"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
