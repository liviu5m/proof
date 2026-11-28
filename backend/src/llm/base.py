from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class LLMResponse:
    """Normalized response returned by every LLM provider.

    No matter which provider is underneath (Google, OpenAI, Anthropic, Ollama),
    the rest of the app (runner.py, judge.py) only sees this shape.

    Token fields: ``None`` means "unknown" (e.g. the call failed). A real
    zero is ``0``.
    """

    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: Decimal | None = None
    raw: Any = None

    # --- extra per-call usage / diagnostics -------------------------------
    cached_tokens: int = 0  # input tokens served from cache
    reasoning_tokens: int = 0  # thinking tokens (already inside output_tokens)
    latency_s: float = 0.0  # wall-clock time of the call
    attempts: int = 1  # retry attempts (accurate for Google only)
    usage_estimated: bool = False  # True if token counts were estimated
    error: str | None = None  # set when the call failed

    @property
    def total_tokens(self) -> int:
        return (self.input_tokens or 0) + (self.output_tokens or 0)

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass
class LLMProviderConfig:
    """Configuration shared by all providers."""

    api_key: str | None = None
    base_url: str | None = None
    timeout: int = 60
    max_retries: int = 3
    default_models: list[str] = field(default_factory=list)
    input_cost_per_1m: Decimal | None = None
    output_cost_per_1m: Decimal | None = None


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
        """Count tokens in a text string (fast, possibly approximate)."""
        ...

    async def acount_tokens(
        self,
        prompt: str,
        model: str,
        system_instruction: str | None = None,
    ) -> int:
        """Token count before sending. Providers override this with an exact,
        possibly network-based count; the default falls back to count_tokens."""
        text = f"{system_instruction}\n{prompt}" if system_instruction else prompt
        return self.count_tokens(text)

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Stable provider identifier (e.g. ``google``, ``openai``)."""
        ...
