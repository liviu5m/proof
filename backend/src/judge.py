import asyncio
import json

from dotenv import load_dotenv
from google.genai import errors
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from src.scorers import check_json, check_keywords, check_regex, check_word_count

load_dotenv()

MAX_CONCURRENCY = 5
REQUEST_TIMEOUT = 60  # seconds per attempt
RETRYABLE_CODES = {429, 500, 502, 503, 504}

# reason comes first so the model states the flaw before committing to a score
SCHEMA = {
    "type": "object",
    "properties": {
        "reason": {"type": "string"},
        "score": {"type": "number"},
    },
    "required": ["reason", "score"],
}


class BadJudgeOutput(Exception):
    """The API call succeeded but the output was empty or not usable JSON."""


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, BadJudgeOutput):
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


def _parse_judgement(text: str | None) -> dict:
    if not text:
        raise BadJudgeOutput("empty output")
    try:
        data = json.loads(text)
        score = float(data["score"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
        raise BadJudgeOutput(f"unparseable output: {text[:200]!r}") from e
    return {
        "score": max(1.0, min(5.0, score)),  # clamp to the 1-5 rubric
        "reason": str(data.get("reason", "")),
    }


def _build_judge_prompt(question, response, expected) -> str:
    return f"""Grade the answer against the expected answer. You can give precise decimal scores (e.g., 3.5, 3.8, 4.2, 4.7) rather than just whole numbers.

RUBRIC:
5 = matches the expected answer, correct units/format, no errors
4 = correct value, but wrong units, rounding, or extra unrequested content
3 = right direction, wrong value, or correct but incomplete
2 = relevant attempt, fundamentally wrong
1 = no relevant content, refuses, or hallucinated

RULES:
- Compare against the expected answer, not against your own opinion.
- Any factual or arithmetic error caps the score at 4.
- Missing the expected value entirely caps the score at 3.
- Padding or filler lowers an otherwise-correct score by 1 (max 4).
- If you cannot verify the reasoning, lower the score.
- You may assign granular decimal scores (e.g. 3.5, 4.2).
- Output plain text only without markdown, bolding, or special characters.

First state the single biggest flaw, then score.

Question: {question}
Answer: {response}
Expected: {expected}

Flaw:"""


def _split_keywords(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(k).strip() for k in value]
    return [k.strip() for k in str(value).split(",") if k.strip()]


def _rule_check(q: dict, response: str) -> dict | None:
    """Cheap local checks. Returns a failing result, or None if all pass."""
    requires_json_val = q.get("requires_json")
    if requires_json_val and str(requires_json_val).lower() in ("true", "1", "yes"):
        if not check_json(response):
            return {"score": 1.0, "reason": "No valid json structure"}

    if q.get("min_words") or q.get("max_words"):
        min_w = int(q["min_words"]) if q.get("min_words") else 0
        max_w = int(q["max_words"]) if q.get("max_words") else 10000
        if not check_word_count(response, min_w, max_w):
            return {"score": 1.0, "reason": f"Failed word count limits ({min_w}-{max_w})"}

    if q.get("regex"):
        if not check_regex(response, q["regex"]):
            return {"score": 1.0, "reason": f"Failed regex pattern match: {q['regex']}"}

    if q.get("required_keywords") or q.get("forbidden_keywords"):
        req_kw = _split_keywords(q.get("required_keywords"))
        forb_kw = _split_keywords(q.get("forbidden_keywords"))
        if not check_keywords(response, req_kw, forb_kw):
            return {"score": 1.0, "reason": "Failed keyword validation"}

    return None


async def judge_single(q, model, client, sem: asyncio.Semaphore | None = None):
    if not q.get("response"):
        return {"score": 0.0, "reason": q.get("error") or "no response"}

    response = q["response"]

    failed = _rule_check(q, response)
    if failed:
        return failed

    judge_prompt = _build_judge_prompt(q["input"], response, q.get("expected"))

    @GEMINI_RETRY
    async def _call():
        interaction = await asyncio.wait_for(
            client.aio.interactions.create(
                model=model,
                system_instruction=(
                    "You are a strict evaluator. Answer under 100 characters in plain "
                    "text only with no markdown or special formatting."
                ),
                input=judge_prompt,
                response_format=SCHEMA,
                store=False,
            ),
            timeout=REQUEST_TIMEOUT,
        )
        try:
            return _parse_judgement(interaction.output_text)
        except BadJudgeOutput:
            print(f"BAD JUDGE OUTPUT for {q['input'][:60]!r}: {interaction}")
            raise

    try:
        if sem is not None:
            async with sem:
                return await _call()
        return await _call()
    except Exception as e:
        return {
            "score": 1.0,
            "reason": f"Judge error ({type(e).__name__}): {e}",
            "judge_failed": True,
        }


async def judge_questions(data, model, client):
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    tasks = [judge_single(q, model, client, sem) for q in data]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    normalized = []
    for r in results:
        if isinstance(r, Exception):
            normalized.append(
                {
                    "score": 1.0,
                    "reason": f"Judge task failed ({type(r).__name__}): {r}",
                    "judge_failed": True,
                }
            )
        else:
            normalized.append(r)
    return normalized
