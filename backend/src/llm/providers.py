from __future__ import annotations
import asyncio
from typing import Any
import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from .base import LLMProvider, LLMResponse, LLMProviderConfig

try:
    from google import genai
    from google.genai import errors as genai_errors
except ImportError:
    genai = None
    genai_errors = None

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None

RETRYABLE_CODES = {429, 500, 502, 503, 504}

def _is_retryable_genai(exc):
    if genai_errors is not None and isinstance(exc, genai_errors.APIError):
        return exc.code in RETRYABLE_CODES
    return isinstance(exc, (asyncio.TimeoutError, TimeoutError))


class GoogleGenAIProvider(LLMProvider):
    provider_name = "google"

    def __init__(self, config: LLMProviderConfig):
        super().__init__(config)
        if genai is None:
            raise ImportError("google-genai required")
        self._client = genai.Client(api_key=config.api_key)

    async def generate(self, prompt, model, system_instruction=None,
                       response_format=None, config=None) -> LLMResponse:
        gen_config: dict[str, Any] = {}
        if response_format:
            gen_config["response_mime_type"] = "application/json"
            gen_config["response_schema"] = response_format
        if config:
            gen_config.update(config)

        @retry(wait=wait_exponential(multiplier=1, min=2, max=30),
               stop=stop_after_attempt(self.config.max_retries),
               retry=retry_if_exception(_is_retryable_genai), reraise=True)
        async def _call():
            return await asyncio.wait_for(
                self._client.aio.interactions.create(
                    model=model, system_instruction=system_instruction,
                    input=prompt, generation_config=gen_config, store=False),
                timeout=self.config.timeout)

        try:
            interaction = await _call()
        except Exception as e:
            return LLMResponse(text="", raw={"error": f"{type(e).__name__}: {e}"})

        return LLMResponse(text=interaction.output_text or "", raw=interaction)

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)


class OpenAIProvider(LLMProvider):
    provider_name = "openai"

    def __init__(self, config: LLMProviderConfig):
        super().__init__(config)
        if AsyncOpenAI is None:
            raise ImportError("openai required")
        self._client = AsyncOpenAI(api_key=config.api_key,
                                   base_url=config.base_url,
                                   timeout=config.timeout,
                                   max_retries=config.max_retries)

    async def generate(self, prompt, model, system_instruction=None,
                       response_format=None, config=None) -> LLMResponse:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        kwargs = {"model": model, "messages": messages}
        if response_format:
            kwargs["response_format"] = {"type": "json_object"}
        if config:
            kwargs.update(config)
        try:
            response = await self._client.chat.completions.create(**kwargs)
        except Exception as e:
            return LLMResponse(text="", raw={"error": f"{type(e).__name__}: {e}"})
        text = response.choices[0].message.content or ""
        usage = response.usage
        return LLMResponse(
            text=text,
            input_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
            output_tokens=getattr(usage, "completion_tokens", None) if usage else None,
            raw=response)

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)


class AnthropicProvider(LLMProvider):
    provider_name = "anthropic"

    def __init__(self, config: LLMProviderConfig):
        super().__init__(config)
        if AsyncAnthropic is None:
            raise ImportError("anthropic required")
        self._client = AsyncAnthropic(api_key=config.api_key,
                                      base_url=config.base_url,
                                      timeout=config.timeout,
                                      max_retries=config.max_retries)

    async def generate(self, prompt, model, system_instruction=None,
                       response_format=None, config=None) -> LLMResponse:
        kwargs = {"model": model, "max_tokens": 4096,
                  "messages": [{"role": "user", "content": prompt}]}
        if system_instruction:
            kwargs["system"] = system_instruction
        if config:
            kwargs.update(config)
        try:
            response = await self._client.messages.create(**kwargs)
        except Exception as e:
            return LLMResponse(text="", raw={"error": f"{type(e).__name__}: {e}"})
        text = "".join(b.text for b in response.content if hasattr(b, "text"))
        usage = response.usage
        return LLMResponse(
            text=text,
            input_tokens=getattr(usage, "input_tokens", None) if usage else None,
            output_tokens=getattr(usage, "output_tokens", None) if usage else None,
            raw=response)

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)


class OllamaProvider(LLMProvider):
    provider_name = "ollama"

    def __init__(self, config: LLMProviderConfig):
        super().__init__(config)
        self._base_url = (config.base_url or "http://localhost:11434").rstrip("/")

    async def generate(self, prompt, model, system_instruction=None,
                       response_format=None, config=None) -> LLMResponse:
        payload = {"model": model, "prompt": prompt, "stream": False}
        if system_instruction:
            payload["system"] = system_instruction
        if config:
            payload.update(config)
        if response_format:
            payload["format"] = "json"
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as http:
                resp = await http.post(f"{self._base_url}/api/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            return LLMResponse(text="", raw={"error": f"{type(e).__name__}: {e}"})
        return LLMResponse(
            text=data.get("response", "") or "",
            input_tokens=data.get("prompt_eval_count"),
            output_tokens=data.get("eval_count"),
            raw=data)

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)
