"""Google GenAI SDK client for Gemini 3.8 Flash with streaming, chat, and structured outputs."""

import os
import asyncio
from typing import Optional, AsyncIterator, List, Dict, Any, Type
from google import genai
from google.genai import types
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, AIMessageChunk, ToolMessage
from pydantic import BaseModel

from src.config import settings
from src.logging_config import get_logger

logger = get_logger("documesh.llm.genai")


class GeminiGenAIClient:
    """Official google-genai SDK wrapper compatible with LangChain interfaces and streaming."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.2
    ):
        self.api_key = (
            api_key or
            settings.gemini_api_key or
            settings.google_api_key or
            os.getenv("GEMINI_API_KEY", "") or
            os.getenv("GOOGLE_API_KEY", "")
        )
        self.model_name = model_name or settings.default_gemini_model or "gemini-3.8-flash"
        self.temperature = temperature
        self._client: Optional[genai.Client] = None

        if self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
                logger.info("gemini_genai_client_initialized", model=self.model_name)
            except Exception as e:
                logger.error("gemini_genai_client_init_failed", error=str(e))

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def _prepare_payload(self, messages: Any, system_instruction: Optional[str] = None):
        system_parts = []
        if system_instruction:
            system_parts.append(system_instruction)

        user_parts = []

        if isinstance(messages, str):
            user_parts.append(messages)
        elif isinstance(messages, list):
            for m in messages:
                if isinstance(m, SystemMessage):
                    system_parts.append(str(m.content))
                elif isinstance(m, HumanMessage):
                    user_parts.append(f"User: {m.content}")
                elif isinstance(m, AIMessage):
                    user_parts.append(f"Assistant: {m.content}")
                elif isinstance(m, ToolMessage):
                    user_parts.append(f"Tool Output ({getattr(m, 'tool_call_id', 'tool')}): {m.content}")
                elif isinstance(m, tuple) and len(m) == 2:
                    if m[0] == "system":
                        system_parts.append(str(m[1]))
                    else:
                        user_parts.append(f"{m[0]}: {m[1]}")
                else:
                    content = getattr(m, "content", str(m))
                    user_parts.append(content)

        sys_inst = "\n\n".join(system_parts) if system_parts else None
        contents = "\n\n".join(user_parts) if user_parts else "Hello"

        config = types.GenerateContentConfig(
            system_instruction=sys_inst,
            temperature=self.temperature
        )
        return contents, config

    def bind_tools(self, tools: Any):
        """No-op tool binding to satisfy LangChain tool-calling interface."""
        return self

    def invoke(self, messages: Any, system_instruction: Optional[str] = None) -> AIMessage:
        """Synchronously invoke Gemini 3.8 Flash."""
        if not self._client:
            raise RuntimeError("Gemini GenAI client not initialized with valid API key.")

        contents, config = self._prepare_payload(messages, system_instruction)
        res = self._client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config
        )
        return AIMessage(content=res.text or "")

    async def ainvoke(self, messages: Any, system_instruction: Optional[str] = None) -> AIMessage:
        """Asynchronously invoke Gemini 3.8 Flash."""
        if not self._client:
            raise RuntimeError("Gemini GenAI client not initialized with valid API key.")

        contents, config = self._prepare_payload(messages, system_instruction)

        def _call():
            return self._client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )

        res = await asyncio.to_thread(_call)
        return AIMessage(content=res.text or "")

    async def astream(self, messages: Any, system_instruction: Optional[str] = None) -> AsyncIterator[AIMessageChunk]:
        """Asynchronously stream real tokens from Gemini 3.8 Flash over SSE."""
        if not self._client:
            raise RuntimeError("Gemini GenAI client not initialized with valid API key.")

        contents, config = self._prepare_payload(messages, system_instruction)

        def _stream():
            return self._client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=config
            )

        stream = await asyncio.to_thread(_stream)
        for chunk in stream:
            if chunk.text:
                yield AIMessageChunk(content=chunk.text)
                await asyncio.sleep(0.005)

    def generate_structured(
        self,
        prompt: str,
        schema_class: Type[BaseModel],
        system_instruction: Optional[str] = None
    ) -> BaseModel:
        """Generate strictly structured output adhering to a Pydantic schema."""
        if not self._client:
            raise RuntimeError("Gemini GenAI client not initialized with valid API key.")

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=schema_class,
            temperature=0.0
        )
        res = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config
        )
        return schema_class.model_validate_json(res.text)


def get_genai_client(
    api_key: Optional[str] = None,
    model_name: Optional[str] = None
) -> Optional[GeminiGenAIClient]:
    """Factory helper to obtain an initialized GeminiGenAIClient if keys exist."""
    client = GeminiGenAIClient(api_key=api_key, model_name=model_name)
    if client.is_available:
        return client
    return None
