from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    """Normalized response returned by every LLM provider.

    No matter which provider is underneath (Google, OpenAI, Anthropic, Ollama),
    the rest of the app (runner.py, judge.py) only sees this shape.
    """

    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    raw: Any = None


@dataclass
class LLMProviderConfig:
    """Configuration shared by all providers."""

    api_key: str | None = None
    base_url: str | None = None
    timeout: int = 60
    max_retries: int = 3
    default_models: list[str] = field(default_factory=list)


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    Every concrete provider (GoogleGenAIProvider, OpenAIProvider,
    AnthropicProvider, OllamaProvider) must implement these three members.
    """

    def __init__(self, config: LLMProviderConfig):
        self.config = config

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str,
        system_instruction: str | None = None,
        response_format: dict | None = None,
        config: dict | None = None,
    ) -> LLMResponse:
        """Generate text from the model and return a normalized response."""
        ...

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Stable provider identifier (e.g. ``google``, ``openai``)."""
        ...
