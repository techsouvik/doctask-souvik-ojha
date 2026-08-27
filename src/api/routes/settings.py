"""Settings API Router for LLM Provider Configuration & Diagnostics."""

import os
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.config import settings
from src.llm.models import ModelProviderConfig, LLMProviderType
from src.llm.factory import get_llm_instance
from src.logging_config import get_logger

logger = get_logger("documesh.api.settings")
router = APIRouter(prefix="/settings", tags=["System & LLM Settings"])


class UpdateLLMSettingsRequest(BaseModel):
    provider: str = Field(..., description="Target provider: openai, anthropic, gemini, or openai_compatible")
    api_key: Optional[str] = Field(None, description="API Key for provider")
    model_name: Optional[str] = Field(None, description="Model identifier, e.g. gpt-4o-mini, claude-3-5-sonnet, gemini-1.5-flash")
    base_url: Optional[str] = Field(None, description="Custom base URL for OpenAI-compatible providers, e.g. http://localhost:11434/v1")


class TestLLMConnectionRequest(BaseModel):
    provider: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    base_url: Optional[str] = None


@router.get("/llm")
def get_llm_settings():
    """Retrieve current LLM provider configuration and status."""
    has_key = bool(
        settings.openai_api_key or
        settings.anthropic_api_key or
        settings.gemini_api_key or
        settings.google_api_key or
        os.getenv("OPENAI_API_KEY") or
        os.getenv("ANTHROPIC_API_KEY") or
        os.getenv("GEMINI_API_KEY") or
        os.getenv("GOOGLE_API_KEY")
    )
    is_compatible = settings.default_provider == "openai_compatible" or bool(settings.openai_base_url)

    return {
        "provider": settings.default_provider,
        "model_name": settings.default_model,
        "base_url": settings.openai_base_url,
        "is_configured": has_key or is_compatible,
        "providers_available": [
            {"id": "openai", "name": "OpenAI (GPT-4o, GPT-4o-mini)", "needs_key": True},
            {"id": "anthropic", "name": "Anthropic Claude (Claude 3.5 Sonnet)", "needs_key": True},
            {"id": "gemini", "name": "Google Gemini (Gemini 1.5 Pro / Flash)", "needs_key": True},
            {"id": "openai_compatible", "name": "Custom OpenAI-Compatible (Ollama, Together, OpenRouter, vLLM)", "needs_key": False}
        ]
    }


@router.post("/llm")
def update_llm_settings(req: UpdateLLMSettingsRequest):
    """Update runtime LLM settings."""
    try:
        prov = req.provider.lower()
        settings.default_provider = prov

        if req.model_name:
            settings.default_model = req.model_name

        if req.base_url is not None:
            settings.openai_base_url = req.base_url
            os.environ["OPENAI_BASE_URL"] = req.base_url

        if req.api_key:
            if prov == "anthropic":
                settings.anthropic_api_key = req.api_key
                os.environ["ANTHROPIC_API_KEY"] = req.api_key
            elif prov == "gemini":
                settings.gemini_api_key = req.api_key
                settings.google_api_key = req.api_key
                os.environ["GEMINI_API_KEY"] = req.api_key
            else:
                settings.openai_api_key = req.api_key
                os.environ["OPENAI_API_KEY"] = req.api_key

        logger.info("llm_settings_updated", provider=settings.default_provider, model=settings.default_model)
        return {
            "status": "updated",
            "provider": settings.default_provider,
            "model_name": settings.default_model,
            "base_url": settings.openai_base_url
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/llm/test")
async def test_llm_connection(req: TestLLMConnectionRequest):
    """Test connectivity to configured LLM provider."""
    provider = req.provider or settings.default_provider
    api_key = req.api_key or (
        settings.anthropic_api_key if provider == "anthropic" else
        settings.gemini_api_key if provider == "gemini" else
        settings.openai_api_key
    )
    base_url = req.base_url if req.base_url is not None else settings.openai_base_url
    model = req.model_name or settings.default_model

    try:
        cfg = ModelProviderConfig(
            provider_type=LLMProviderType(provider),
            api_key=api_key or "test_key",
            model_name=model,
            base_url=base_url or None
        )
        llm = get_llm_instance(cfg)
        if not llm:
            return {
                "success": False,
                "message": f"Provider '{provider}' requires an API key or reachable endpoint."
            }

        res = await llm.ainvoke("Respond with 'OK' if you can read this message.")
        txt = res.content if hasattr(res, "content") else str(res)
        return {
            "success": True,
            "message": f"Successfully connected to {provider} ({model})!",
            "response": txt.strip()
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}"
        }
