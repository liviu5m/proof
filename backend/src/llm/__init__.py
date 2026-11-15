from .base import LLMProvider, LLMResponse, LLMProviderConfig
from .providers import (
    GoogleGenAIProvider,
    OpenAIProvider,
    AnthropicProvider,
    OllamaProvider,
)

PROVIDERS = {
    "google": GoogleGenAIProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
}

__all__ = [
    "LLMProvider",
    "LLMResponse",
    "LLMProviderConfig",
    "GoogleGenAIProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "OllamaProvider",
    "PROVIDERS",
]
