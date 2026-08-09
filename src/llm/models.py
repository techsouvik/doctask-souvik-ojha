"""Data models for Multi-Provider LLM Configuration."""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class LLMProviderType(str, Enum):
    OPENAI = "openai"
    OPENAI_COMPATIBLE = "openai_compatible"  # Custom Base URL (Together, Ollama, OpenRouter, vLLM)
    ANTHROPIC = "anthropic"                  # Claude
    GEMINI = "gemini"                        # Google Gemini


class ModelProviderConfig(BaseModel):
    provider_type: LLMProviderType = LLMProviderType.OPENAI
    api_key: Optional[str] = Field(None, description="API Key for target provider")
    model_name: Optional[str] = Field(None, description="Model ID (e.g. gpt-4o-mini, claude-3-5-sonnet-20241022, gemini-1.5-flash)")
    base_url: Optional[str] = Field(None, description="Custom OpenAI-compatible base URL (e.g. http://localhost:11434/v1)")
    temperature: float = Field(0.0, ge=0.0, le=1.0)
    max_tokens: Optional[int] = 4096
    extra_headers: Optional[Dict[str, str]] = Field(default_factory=dict)
