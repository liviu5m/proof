import asyncio

from dotenv import load_dotenv
from google.genai import errors
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

load_dotenv()

MAX_CONCURRENCY = 5
REQUEST_TIMEOUT = 60  
RETRYABLE_CODES = {429, 500, 502, 503, 504}


class EmptyResponse(Exception):
    """The API call succeeded but returned no text."""


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, EmptyResponse):
        return True
    if isinstance(exc, errors.APIError):
        return exc.code in RETRYABLE_CODES
    return isinstance(exc, (asyncio.TimeoutError, TimeoutError))


GEMINI_RETRY = retry(
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(5),
    retry=retry_if_exception(_is_retryable),
    reraise=True,
)


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


async def run_single(q, prompt, model, client, sem: asyncio.Semaphore | None = None):
    full_prompt = _build_prompt(prompt, q)
    print("RUNNING --------------------------------------")
    @GEMINI_RETRY
    async def _call():
        interaction = await asyncio.wait_for(
            client.aio.interactions.create(
                model=model,
                system_instruction=full_prompt,
                input=q["input"],
                generation_config={"thinking_level": "minimal"},
                store=False,
            ),
            timeout=REQUEST_TIMEOUT,
        )
        print(interaction.output_text)
        if not interaction.output_text:
            print(f"EMPTY RESPONSE for {q['input'][:60]!r}: {interaction}")
            raise EmptyResponse("no text in output")
        return interaction

    try:
        if sem is not None:
            async with sem:
                interaction = await _call()
        else:
            interaction = await _call()
    except Exception as e:
        print(e)
        return {
            "input": q.get("input", ""),
            "response": None,
            "error": f"{type(e).__name__}: {e}",
            "code": getattr(e, "code", None) or "gemini_api_error",
        }

    print(f"Q: {q['input']}")
    print(f"A: {interaction.output_text}\n")
    return {
        "input": q["input"],
        "response": interaction.output_text,
        "expected": q.get("expected"),
        "regex": q.get("regex"),
        "min_words": q.get("min_words"),
        "max_words": q.get("max_words"),
        "required_keywords": q.get("required_keywords"),
        "forbidden_keywords": q.get("forbidden_keywords"),
        "requires_json": q.get("requires_json"),
    }


async def run_tests(questions, prompt, model, client):
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    tasks = [run_single(q, prompt, model, client, sem) for q in questions]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    normalized = []
    for r in results:
        if isinstance(r, Exception):
            normalized.append(
                {"error": f"{type(r).__name__}: {r}", "response": None, "code": "task_exception"}
            )
        else:
            normalized.append(r)
    return normalized
