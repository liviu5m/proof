import asyncio
from typing import Any

from src.llm import LLMProvider

MAX_CONCURRENCY = 5
REQUEST_TIMEOUT = 60


def _build_prompt(prompt: str, q: dict) -> str:
    full_prompt = prompt
    if q.get("min_words") or q.get("max_words"):
        full_prompt += f"\nWords: {q.get('min_words', 0)}-{q.get('max_words', 10000)}"
    if q.get("required_keywords"):
        full_prompt += f"\nInclude: {q.get('required_keywords')}"
    if q.get("forbidden_keywords"):
        full_prompt += f"\nExclude: {q.get('forbidden_keywords')}"
    if q.get("regex"):
        full_prompt += f"\nMatch regex: {q.get('regex')}"
    return full_prompt


async def run_single(
    q, prompt, model, provider: LLMProvider, sem: asyncio.Semaphore | None = None
):
    full_prompt = _build_prompt(prompt, q)
    print("RUNNING --------------------------------------")

    async def _call():
        return await asyncio.wait_for(
            provider.generate(
                prompt=q["input"],
                model=model,
                system_instruction=full_prompt,
                config={"thinking_level": "minimal"},
            ),
            timeout=REQUEST_TIMEOUT,
        )

    try:
        if sem is not None:
            async with sem:
                response = await _call()
        else:
            response = await _call()
    except Exception as e:
        print(e)
        return {
            "input": q.get("input", ""),
            "response": None,
            "error": f"{type(e).__name__}: {e}",
            "code": "llm_provider_error",
        }

    text = response.text or ""
    if not text:
        error_msg = (
            response.raw.get("error", "no text in output")
            if isinstance(response.raw, dict)
            else "no text in output"
        )
        print(f"EMPTY RESPONSE for {q['input'][:60]!r}: {response}")
        return {
            "input": q.get("input", ""),
            "response": None,
            "error": error_msg,
            "code": "empty_response",
        }

    print(f"Q: {q['input']}")
    print(f"A: {text}\n")
    return {
        "input": q["input"],
        "response": text,
        "expected": q.get("expected"),
        "regex": q.get("regex"),
        "min_words": q.get("min_words"),
        "max_words": q.get("max_words"),
        "required_keywords": q.get("required_keywords"),
        "forbidden_keywords": q.get("forbidden_keywords"),
        "requires_json": q.get("requires_json"),
    }


async def run_tests(questions, prompt, model, provider: LLMProvider):
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    tasks = [run_single(q, prompt, model, provider, sem) for q in questions]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    normalized: list[dict[str, Any]] = []
    for r in results:
        if isinstance(r, Exception):
            normalized.append(
                {
                    "error": f"{type(r).__name__}: {r}",
                    "response": None,
                    "code": "task_exception",
                }
            )
        else:
            normalized.append(r)  # type: ignore[arg-type]
    return normalized
