import asyncio
import json

from src.llm import LLMProvider
from src.scorers import check_json, check_keywords, check_regex, check_word_count

MAX_CONCURRENCY = 5
REQUEST_TIMEOUT = 60  # seconds per attempt

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


def _parse_judgement(text: str | None) -> dict:
    if not text:
        raise BadJudgeOutput("empty output")
    # Try direct JSON parse first
    try:
        data = json.loads(text)
        score = float(data["score"])
        return {
            "score": max(1.0, min(5.0, score)),
            "reason": str(data.get("reason", "")),
        }
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        pass
    # Fallback: try to extract JSON block from within text
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        data = json.loads(text[start:end])
        score = float(data["score"])
        return {
            "score": max(1.0, min(5.0, score)),
            "reason": str(data.get("reason", "")),
        }
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        pass
    # Fallback: extract just a score number
    import re

    match = re.search(r'"score"\s*:\s*([0-9]+(?:\.[0-9]+)?)', text)
    if match:
        score = float(match.group(1))
        return {
            "score": max(1.0, min(5.0, score)),
            "reason": "Extracted from non-JSON judge output",
        }
    match = re.search(r"score[:=]\s*([0-9]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
    if match:
        score = float(match.group(1))
        return {
            "score": max(1.0, min(5.0, score)),
            "reason": "Extracted from non-JSON judge output",
        }
    raise BadJudgeOutput(f"unparseable output: {text[:200]!r}")


def _build_judge_prompt(question, response, expected) -> str:
    return (
        "Grade the answer against the expected answer. You can give precise "
        "decimal scores (e.g., 3.5, 3.8, 4.2, 4.7) rather than just whole numbers.\n\n"
        "RUBRIC:\n"
        "5 = matches the expected answer, correct units/format, no errors\n"
        "4 = correct value, but wrong units, rounding, or extra unrequested content\n"
        "3 = right direction, wrong value, or correct but incomplete\n"
        "2 = relevant attempt, fundamentally wrong\n"
        "1 = no relevant content, refuses, or hallucinated\n\n"
        "RULES:\n"
        "- Compare against the expected answer, not against your own opinion.\n"
        "- Any factual or arithmetic error caps the score at 4.\n"
        "- Missing the expected value entirely caps the score at 3.\n"
        "- Padding or filler lowers an otherwise-correct score by 1 (max 4).\n"
        "- If you cannot verify the reasoning, lower the score.\n"
        "- You may assign granular decimal scores (e.g. 3.5, 4.2).\n"
        "- Output plain text only without markdown, bolding, or special characters.\n\n"
        "First state the single biggest flaw, then score.\n\n"
        "Question: {question}\nAnswer: {response}\nExpected: {expected}\n\nFlaw:"
    )


def _split_keywords(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(k).strip() for k in value]
    return [k.strip() for k in str(value).split(",") if k.strip()]


def _rule_check(q: dict, response: str) -> dict | None:
    """Cheap local checks. Returns a failing result, or None if all pass."""
    requires_json_val = q.get("requires_json")
    if (
        requires_json_val
        and str(requires_json_val).lower() in ("true", "1", "yes")
        and not check_json(response)
    ):
        return {"score": 1.0, "reason": "No valid json structure"}

    if q.get("min_words") or q.get("max_words"):
        min_w = int(q["min_words"]) if q.get("min_words") else 0
        max_w = int(q["max_words"]) if q.get("max_words") else 10000
        if not check_word_count(response, min_w, max_w):
            return {
                "score": 1.0,
                "reason": f"Failed word count limits ({min_w}-{max_w})",
            }

    if q.get("regex") and not check_regex(response, q["regex"]):
        return {"score": 1.0, "reason": f"Failed regex pattern match: {q['regex']}"}

    if q.get("required_keywords") or q.get("forbidden_keywords"):
        req_kw = _split_keywords(q.get("required_keywords"))
        forb_kw = _split_keywords(q.get("forbidden_keywords"))
        if not check_keywords(response, req_kw, forb_kw):
            return {"score": 1.0, "reason": "Failed keyword validation"}

    return None


async def judge_single(
    q, model, provider: LLMProvider, sem: asyncio.Semaphore | None = None
):
    if not q.get("response"):
        return {"score": 0.0, "reason": q.get("error") or "no response"}

    response = q["response"]

    failed = _rule_check(q, response)
    if failed:
        return failed

    judge_prompt = _build_judge_prompt(q["input"], response, q.get("expected"))

    async def _call():
        return await asyncio.wait_for(
            provider.generate(
                prompt=judge_prompt,
                model=model,
                system_instruction=(
                    "You are a strict evaluator. Return ONLY valid JSON matching "
                    'the schema {"reason": "string", "score": number}. '
                    "No markdown, no extra text, no explanation."
                ),
                response_format=SCHEMA,
            ),
            timeout=REQUEST_TIMEOUT,
        )

    try:
        if sem is not None:
            async with sem:
                result = await _call()
        else:
            result = await _call()
    except Exception as e:
        return {
            "score": 1.0,
            "reason": f"Judge error ({type(e).__name__}): {e}",
            "judge_failed": True,
        }
    print("JUDGE ----------------------------------------------")
    print(result)
    if result.text is None or result.text == "":
        return {
            "score": 1.0,
            "reason": "Judge returned empty output",
            "judge_failed": True,
        }

    try:
        return _parse_judgement(result.text)
    except BadJudgeOutput:
        print(f"BAD JUDGE OUTPUT for {q['input'][:60]!r}: {result.text}")
        return {
            "score": 1.0,
            "reason": f"Judge output unparseable: {result.text[:200]}",
            "judge_failed": True,
        }


async def judge_questions(data, model, provider: LLMProvider):
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    tasks = [judge_single(q, model, provider, sem) for q in data]
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
