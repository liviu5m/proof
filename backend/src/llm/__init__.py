from .base import LLMProvider, LLMProviderConfig, LLMResponse
from .providers import (
    AnthropicProvider,
    GoogleGenAIProvider,
    OllamaProvider,
    OpenAIProvider,
)

PROVIDERS: dict[str, type[LLMProvider]] = {
    "google": GoogleGenAIProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
}

__all__ = [
    "PROVIDERS",
    "AnthropicProvider",
    "GoogleGenAIProvider",
    "LLMProvider",
    "LLMProviderConfig",
    "LLMResponse",
    "OllamaProvider",
    "OpenAIProvider",
]
