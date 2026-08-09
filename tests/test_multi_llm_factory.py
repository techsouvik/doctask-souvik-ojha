"""Unit tests for Multi-Provider LLM Factory Engine."""

import os
import pytest
from src.llm.models import ModelProviderConfig, LLMProviderType
from src.llm.factory import get_llm_instance
from src.config import settings


def test_llm_factory_openai_compatible_custom_base_url():
    cfg = ModelProviderConfig(
        provider_type=LLMProviderType.OPENAI_COMPATIBLE,
        api_key="test_custom_key",
        model_name="llama-3.1-70b",
        base_url="https://api.together.xyz/v1",
        temperature=0.0
    )

    llm = get_llm_instance(cfg)
    assert llm is not None
    assert llm.model_name == "llama-3.1-70b"
    assert llm.openai_api_base == "https://api.together.xyz/v1"


def test_llm_factory_offline_fallback():
    cfg = ModelProviderConfig(
        provider_type=LLMProviderType.OPENAI,
        api_key="",
        model_name="gpt-4o-mini",
        base_url=None,
        temperature=0.0
    )

    old_key = os.environ.get("OPENAI_API_KEY")
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]

    old_settings_key = settings.openai_api_key
    settings.openai_api_key = ""

    try:
        llm = get_llm_instance(cfg)
        assert llm is None  # Graceful fallback when no key is available
    finally:
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key
        settings.openai_api_key = old_settings_key
