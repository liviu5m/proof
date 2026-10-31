import asyncio
from google.genai import Client
from dotenv import load_dotenv
import json
import os
from tenacity import retry, stop_after_attempt, wait_exponential

from src.scorers import check_json, check_keywords, check_regex, check_word_count

load_dotenv()

SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "number"},
        "reason": {"type": "string"},
    },
    "required": ["score", "reason"],
}

GEMINI_RETRY = retry(
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(5),
    reraise=True,
)


async def judge_single(q, model, client):
    question = q["input"]
    response = q["response"]
    expected = q["expected"]
    JUDGE_PROMPT = f"""Grade the answer against the expected answer. You can give precise decimal scores (e.g., 3.5, 3.8, 4.2, 4.7) rather than just whole numbers.

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
        req_kw = [k.strip() for k in q["required_keywords"].split(",")] if q.get("required_keywords") else []
        forb_kw = [k.strip() for k in q["forbidden_keywords"].split(",")] if q.get("forbidden_keywords") else []
        if not check_keywords(response, req_kw, forb_kw):
            return {"score": 1.0, "reason": "Failed keyword validation"}

    @GEMINI_RETRY
    async def _call():
        return await client.aio.interactions.create(
            model=model,
            system_instruction="You are a strict evaluator. Answer under 100 characters in plain text only with no markdown or special formatting.",
            input=JUDGE_PROMPT,
            response_format=SCHEMA,
            store=False,
        )

    try:
        interaction = await _call()
    except Exception as e:
        return {"score": 1.0, "reason": f"Judge API error: {e}"}

    return json.loads(interaction.output_text)


async def judge_questions(data, model, client):
    tasks = [judge_single(q, model, client) for q in data]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # Normalize exceptions to error dicts
    normalized = []
    for r in results:
        if isinstance(r, Exception):
            normalized.append({"score": 1.0, "reason": f"Judge task failed: {r}"})
        else:
            normalized.append(r)
    return normalized
