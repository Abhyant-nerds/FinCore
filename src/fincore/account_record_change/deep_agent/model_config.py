"""Configurable chat-model construction for Deep Agents."""

from __future__ import annotations

import os
from typing import Any, Literal

from pydantic import BaseModel, Field


ModelProvider = Literal["ollama", "openai"]


class ModelProfile(BaseModel):
    """Serializable model profile used before constructing the model object."""

    provider: ModelProvider = "ollama"
    model: str = "qwen2.5:3b"
    temperature: float = 0.0
    timeout: float | None = None
    max_retries: int = 2
    base_url: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


def default_model_profile() -> ModelProfile:
    """Build the default profile from environment variables.

    Defaults to local Ollama with qwen2.5:3b.
    """

    provider = os.getenv("FINCORE_LLM_PROVIDER", "ollama").lower()
    model = os.getenv("FINCORE_LLM_MODEL", "qwen2.5:3b")
    base_url = os.getenv("FINCORE_LLM_BASE_URL") or None
    temperature = float(os.getenv("FINCORE_LLM_TEMPERATURE", "0"))
    return ModelProfile(
        provider=provider,  # type: ignore[arg-type]
        model=model,
        base_url=base_url,
        temperature=temperature,
    )


def create_chat_model(profile: ModelProfile | None = None):
    """Create a concrete LangChain chat model instance from a profile."""

    selected = profile or default_model_profile()
    if selected.provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Install langchain-ollama to use Ollama model profiles.") from exc

        kwargs: dict[str, Any] = {
            "model": selected.model,
            "temperature": selected.temperature,
            **selected.extra,
        }
        if selected.base_url:
            kwargs["base_url"] = selected.base_url
        if selected.timeout is not None:
            kwargs["timeout"] = selected.timeout
        return ChatOllama(**kwargs)

    if selected.provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Install langchain-openai to use OpenAI model profiles.") from exc

        kwargs = {
            "model": selected.model,
            "temperature": selected.temperature,
            "max_retries": selected.max_retries,
            **selected.extra,
        }
        if selected.timeout is not None:
            kwargs["timeout"] = selected.timeout
        return ChatOpenAI(**kwargs)

    raise ValueError(f"Unsupported model provider: {selected.provider}")


QWEN_OLLAMA_PROFILE = ModelProfile(provider="ollama", model="qwen2.5:3b", temperature=0.0)

