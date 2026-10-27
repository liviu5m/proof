from google import genai
from dotenv import load_dotenv
import asyncio

load_dotenv()

client = genai.Client()

async def run_single(q, prompt, model):

    full_prompt = prompt
    if q.get("min_words") or q.get("max_words"):
        full_prompt += f"\nWords: {q.get('min_words', 0)}-{q.get('max_words', 10000)}"
    if q.get("required_keywords"):
        full_prompt += f"\nInclude: {q.get('required_keywords')}"
    if q.get("forbidden_keywords"):
        full_prompt += f"\nExclude: {q.get('forbidden_keywords')}"
    if q.get("regex"):
        full_prompt += f"\nMatch regex: {q.get('regex')}"
    interaction = await client.aio.interactions.create(
        model=model,
        system_instruction=full_prompt,
        input=q["input"],
        generation_config={"thinking_level": "minimal"},
        store=False,
    )
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
        "required_json": q.get("required_json"),
    }


async def run_tests(questions, prompt, model):
    tasks = [run_single(q, prompt, model) for q in questions]
    return await asyncio.gather(*tasks)
