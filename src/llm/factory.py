"""Multi-Provider LLM Factory for OpenAI, OpenAI-Compatible (Custom Base URL), Anthropic Claude, & Gemini."""

import os
from typing import Optional, Any
from pydantic import SecretStr

from src.llm.models import ModelProviderConfig, LLMProviderType
from src.config import settings
from src.logging_config import get_logger

logger = get_logger("documesh.llm.factory")


def get_llm_instance(config: Optional[ModelProviderConfig] = None) -> Optional[Any]:
    """Create a LangChain ChatModel instance based on provider configuration."""
    cfg = config or ModelProviderConfig(
        provider_type=LLMProviderType(settings.default_provider or "openai"),
        api_key=settings.openai_api_key or settings.gemini_api_key or settings.anthropic_api_key or "",
        model_name=settings.default_model,
        base_url=settings.openai_base_url or None
    )

    p_type = cfg.provider_type
    api_key = cfg.api_key

    # 1. ANTHROPIC CLAUDE NATIVE
    if p_type == LLMProviderType.ANTHROPIC:
        key = api_key or settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY", "")
        if not key:
            logger.info("anthropic_key_missing_falling_back")
            return None
        from langchain_anthropic import ChatAnthropic
        model = cfg.model_name or settings.default_claude_model
        logger.info("llm_factory_created_anthropic", model=model)
        return ChatAnthropic(
            model=model,
            api_key=SecretStr(key),
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens or 4096
        )

    # 2. GOOGLE GEMINI NATIVE
    elif p_type == LLMProviderType.GEMINI:
        key = api_key or settings.gemini_api_key or settings.google_api_key or os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
        if not key:
            logger.info("gemini_key_missing_falling_back")
            return None
        from langchain_google_genai import ChatGoogleGenerativeAI
        model = cfg.model_name or settings.default_gemini_model
        logger.info("llm_factory_created_gemini", model=model)
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=key,
            temperature=cfg.temperature
        )

    # 3. OPENAI COMPATIBLE (Custom Base URL: Together, Ollama, OpenRouter, vLLM)
    elif p_type == LLMProviderType.OPENAI_COMPATIBLE or cfg.base_url:
        key = api_key or settings.openai_api_key or os.getenv("OPENAI_API_KEY", "custom_key")
        base_url = cfg.base_url or settings.openai_base_url or "http://localhost:11434/v1"
        model = cfg.model_name or "gpt-4o-mini"
        from langchain_openai import ChatOpenAI
        logger.info("llm_factory_created_openai_compatible", base_url=base_url, model=model)
        return ChatOpenAI(
            model=model,
            api_key=SecretStr(key),
            base_url=base_url,
            temperature=cfg.temperature,
            default_headers=cfg.extra_headers
        )

    # 4. OPENAI NATIVE
    else:
        key = api_key or settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")
        if not key:
            logger.info("openai_key_missing_falling_back")
            return None
        from langchain_openai import ChatOpenAI
        model = cfg.model_name or settings.default_model
        logger.info("llm_factory_created_openai", model=model)
        return ChatOpenAI(
            model=model,
            api_key=SecretStr(key),
            temperature=cfg.temperature
        )
