from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from .cost import calculate_cost

from .base import LLMProvider, LLMProviderConfig, LLMResponse

try:
    from google import genai
    from google.genai import errors as genai_errors
except ImportError:
    genai = None  # type: ignore[assignment,misc]
    genai_errors = None  # type: ignore[assignment,misc]

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None  # type: ignore[assignment,misc]

try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None  # type: ignore[assignment,misc]

try:
    import tiktoken
except ImportError:
    tiktoken = None  # type: ignore[assignment]

RETRYABLE_CODES = {429, 500, 502, 503, 504}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _int(obj: Any, name: str) -> int:
    """Safely read an integer attribute (None / missing -> 0)."""
    if obj is None:
        return 0
    return int(getattr(obj, name, 0) or 0)


def _estimate_tokens(text: str) -> int:
    """Rough fallback only. Real counts come from provider usage fields."""
    return max(1, len(text) // 4)


def _error_response(exc: Exception, started: float, attempts: int = 1) -> LLMResponse:
    msg = f"{type(exc).__name__}: {exc}"
    return LLMResponse(
        text="",
        raw={"error": msg},
        error=msg,
        latency_s=time.perf_counter() - started,
        attempts=attempts,
    )


def _is_retryable_genai(exc):
    if genai_errors is not None and isinstance(exc, genai_errors.APIError):
        return exc.code in RETRYABLE_CODES
    return isinstance(exc, (asyncio.TimeoutError, TimeoutError))


# --------------------------------------------------------------------------- #
# Google
# --------------------------------------------------------------------------- #
class GoogleGenAIProvider(LLMProvider):
    provider_name = "google"

    def __init__(self, config: LLMProviderConfig):
        super().__init__(config)
        if genai is None:
            raise ImportError("google-genai required")
        self._client = genai.Client(api_key=config.api_key)

    async def generate(
        self, prompt, model, system_instruction=None, response_format=None, config=None
    ) -> LLMResponse:
        gen_config: dict[str, Any] = {}
        if response_format:
            gen_config["response_mime_type"] = "application/json"
            gen_config["response_schema"] = response_format
        if config:
            gen_config.update(config)

        @retry(
            wait=wait_exponential(multiplier=1, min=2, max=30),
            stop=stop_after_attempt(self.config.max_retries),
            retry=retry_if_exception(_is_retryable_genai),
            reraise=True,
        )
        async def _call():
            return await asyncio.wait_for(
                self._client.aio.interactions.create(
                    model=model,
                    system_instruction=system_instruction,
                    input=prompt,
                    generation_config=gen_config,
                    store=True,
                ),
                timeout=self.config.timeout,
            )

        started = time.perf_counter()
        try:
            interaction = await _call()
        except Exception as e:
            attempts = int(getattr(_call, "statistics", {}).get("attempt_number", 1))
            return _error_response(e, started, attempts)
        latency = time.perf_counter() - started
        attempts = int(getattr(_call, "statistics", {}).get("attempt_number", 1))

        # Interactions API: usage lives on `interaction.usage` (NOT usage_metadata).
        usage = getattr(interaction, "usage", None) or getattr(
            interaction, "usage_metadata", None
        )
        prompt_tokens = _int(usage, "total_input_tokens") or _int(
            usage, "prompt_token_count"
        )
        output_tokens = _int(usage, "total_output_tokens") or _int(
            usage, "candidates_token_count"
        )
        # Thinking tokens are reported separately and billed as output.
        thought_tokens = _int(usage, "total_thought_tokens") or _int(
            usage, "thoughts_token_count"
        )
        cached_tokens = _int(usage, "total_cached_tokens") or _int(
            usage, "cached_content_token_count"
        )
        completion_tokens = output_tokens + thought_tokens

        cost_usd = calculate_cost(
            prompt_tokens,
            completion_tokens,
            self.config.input_cost_per_1m,
            self.config.output_cost_per_1m,
        )
        return LLMResponse(
            text=interaction.output_text or "",
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            cost_usd=cost_usd,
            raw=interaction,
            cached_tokens=cached_tokens,
            reasoning_tokens=thought_tokens,
            latency_s=latency,
            attempts=attempts,
        )

    def count_tokens(self, text: str) -> int:
        return _estimate_tokens(text)

    async def acount_tokens(self, prompt, model, system_instruction=None) -> int:
        """Exact input token count BEFORE sending (network call)."""
        resp = await self._client.aio.models.count_tokens(model=model, contents=prompt)
        return int(resp.total_tokens or 0)


# --------------------------------------------------------------------------- #
# OpenAI (and OpenAI-compatible base_url servers)
# --------------------------------------------------------------------------- #
class OpenAIProvider(LLMProvider):
    provider_name = "openai"

    def __init__(self, config: LLMProviderConfig):
        super().__init__(config)
        if AsyncOpenAI is None:
            raise ImportError("openai required")
        self._client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,  # SDK retries are invisible to us
        )

    async def generate(
        self, prompt, model, system_instruction=None, response_format=None, config=None
    ) -> LLMResponse:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        kwargs: dict[str, Any] = {"model": model, "messages": messages}
        if response_format:
            # json_object mode requires the word "JSON" somewhere in the messages
            kwargs["response_format"] = {"type": "json_object"}
        if config:
            kwargs.update(config)

        started = time.perf_counter()
        try:
            response = await self._client.chat.completions.create(**kwargs)
        except Exception as e:
            return _error_response(e, started)
        latency = time.perf_counter() - started

        text = response.choices[0].message.content or ""
        usage = response.usage
        prompt_tokens = _int(usage, "prompt_tokens")
        completion_tokens = _int(usage, "completion_tokens")  # includes reasoning
        cached_tokens = _int(getattr(usage, "prompt_tokens_details", None), "cached_tokens")
        reasoning_tokens = _int(
            getattr(usage, "completion_tokens_details", None), "reasoning_tokens"
        )

        cost_usd = calculate_cost(
            prompt_tokens,
            completion_tokens,
            self.config.input_cost_per_1m,
            self.config.output_cost_per_1m,
        )
        return LLMResponse(
            text=text,
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            cost_usd=cost_usd,
            raw=response,
            cached_tokens=cached_tokens,
            reasoning_tokens=reasoning_tokens,
            latency_s=latency,
        )

    def count_tokens(self, text: str, model: str | None = None) -> int:
        """Local count with tiktoken when installed, else a rough estimate."""
        if tiktoken is None:
            return _estimate_tokens(text)
        try:
            enc = tiktoken.encoding_for_model(model) if model else tiktoken.get_encoding("o200k_base")
        except KeyError:
            enc = tiktoken.get_encoding("o200k_base")
        return max(1, len(enc.encode(text)))

    async def acount_tokens(self, prompt, model, system_instruction=None) -> int:
        text = f"{system_instruction}\n{prompt}" if system_instruction else prompt
        return self.count_tokens(text, model)


# --------------------------------------------------------------------------- #
# Anthropic
# --------------------------------------------------------------------------- #
class AnthropicProvider(LLMProvider):
    provider_name = "anthropic"

    def __init__(self, config: LLMProviderConfig):
        super().__init__(config)
        if AsyncAnthropic is None:
            raise ImportError("anthropic required")
        self._client = AsyncAnthropic(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

    async def generate(
        self, prompt, model, system_instruction=None, response_format=None, config=None
    ) -> LLMResponse:
        # NOTE: response_format is not used here. For guaranteed JSON, use tool
        # calling with a JSON schema instead.
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_instruction:
            kwargs["system"] = system_instruction
        if config:
            kwargs.update(config)

        started = time.perf_counter()
        try:
            response = await self._client.messages.create(**kwargs)
        except Exception as e:
            return _error_response(e, started)
        latency = time.perf_counter() - started

        text = "".join(b.text for b in response.content if hasattr(b, "text"))
        usage = response.usage
        prompt_tokens = _int(usage, "input_tokens")  # excludes cache read/write tokens
        completion_tokens = _int(usage, "output_tokens")
        cache_read = _int(usage, "cache_read_input_tokens")

        cost_usd = calculate_cost(
            prompt_tokens,
            completion_tokens,
            self.config.input_cost_per_1m,
            self.config.output_cost_per_1m,
        )
        return LLMResponse(
            text=text,
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            cost_usd=cost_usd,
            raw=response,
            cached_tokens=cache_read,
            latency_s=latency,
        )

    def count_tokens(self, text: str) -> int:
        return _estimate_tokens(text)

    async def acount_tokens(self, prompt, model, system_instruction=None) -> int:
        """Exact input token count BEFORE sending (network call)."""
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_instruction:
            kwargs["system"] = system_instruction
        resp = await self._client.messages.count_tokens(**kwargs)
        return int(resp.input_tokens)


# --------------------------------------------------------------------------- #
# Ollama
# --------------------------------------------------------------------------- #
class OllamaProvider(LLMProvider):
    provider_name = "ollama"

    def __init__(self, config: LLMProviderConfig):
        super().__init__(config)
        self._base_url = (config.base_url or "http://localhost:11434").rstrip("/")

    async def generate(
        self, prompt, model, system_instruction=None, response_format=None, config=None
    ) -> LLMResponse:
        payload: dict[str, Any] = {"model": model, "prompt": prompt, "stream": False}
        if system_instruction:
            payload["system"] = system_instruction
        if config:
            payload.update(config)
        if response_format:
            payload["format"] = "json"

        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as http:
                resp = await http.post(f"{self._base_url}/api/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            return _error_response(e, started)
        latency = time.perf_counter() - started

        text = data.get("response", "") or ""
        prompt_tokens = int(data.get("prompt_eval_count", 0) or 0)
        completion_tokens = int(data.get("eval_count", 0) or 0)

        # Ollama can omit prompt_eval_count when the prompt was served from cache.
        estimated = False
        if prompt_tokens == 0:
            prompt_tokens = _estimate_tokens((system_instruction or "") + prompt)
            estimated = True
        if completion_tokens == 0 and text:
            completion_tokens = _estimate_tokens(text)
            estimated = True

        cost_usd = calculate_cost(
            prompt_tokens,
            completion_tokens,
            self.config.input_cost_per_1m,
            self.config.output_cost_per_1m,
        )
        return LLMResponse(
            text=text,
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            cost_usd=cost_usd,
            raw=data,
            latency_s=latency,
            usage_estimated=estimated,
        )

    def count_tokens(self, text: str) -> int:
        return _estimate_tokens(text)

    async def acount_tokens(self, prompt, model, system_instruction=None) -> int:
        return _estimate_tokens((system_instruction or "") + prompt)
