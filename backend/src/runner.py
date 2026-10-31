from google import genai
from dotenv import load_dotenv
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv()

GEMINI_RETRY = retry(
    wait=wait_exponential(multiplier=1, min=2, max=30),  
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(Exception),  
    reraise=True,
)

def _is_rate_limit(e: Exception) -> bool:
    """Check if exception is a rate limit (429) or timeout error."""
    msg = str(e).lower()
    return "429" in msg or "rate limit" in msg or "timeout" in msg or "timed out" in msg


async def run_single(q, prompt, model, client):
    full_prompt = prompt
    if q.get("min_words") or q.get("max_words"):
        full_prompt += f"\nWords: {q.get('min_words', 0)}-{q.get('max_words', 10000)}"
    if q.get("required_keywords"):
        full_prompt += f"\nInclude: {q.get('required_keywords')}"
    if q.get("forbidden_keywords"):
        full_prompt += f"\nExclude: {q.get('forbidden_keywords')}"
    if q.get("regex"):
        full_prompt += f"\nMatch regex: {q.get('regex')}"

    @GEMINI_RETRY
    async def _call():
        return await client.aio.interactions.create(
            model=model,
            system_instruction=full_prompt,
            input=q["input"],
            generation_config={"thinking_level": "minimal"},
            store=False,
        )

    try:
        interaction = await _call()
    except Exception as e:
        return {"error": str(e), "code": "gemini_api_error", "input": q.get("input", "")}

    print(f"Q: {q['input']}")
    print(f"A: {interaction.output_text}\n")
    return {
        "input": q["input"],
        "response": interaction.output_text,
        "expected": q["expected"],
        "regex": q.get("regex"),
        "min_words": q.get("min_words"),
        "max_words": q.get("max_words"),
        "required_keywords": q.get("required_keywords"),
        "forbidden_keywords": q.get("forbidden_keywords"),
        "required_json": q.get("requires_json"),
    }


async def run_tests(questions, prompt, model, client):
    tasks = [run_single(q, prompt, model, client) for q in questions]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    normalized = []
    for r in results:
        if isinstance(r, Exception):
            normalized.append({"error": str(r), "code": "task_exception"})
        else:
            normalized.append(r)
    return normalized
