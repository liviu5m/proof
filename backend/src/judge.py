from google.genai import Client
from dotenv import load_dotenv
import json
import os
load_dotenv()

client = Client()

SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer"},
        "reason": {"type": "string"},
    },
    "required": ["score", "reason"],
}

def judge_questions(data, model):
    scores = []
    for q in data:
        question = q["input"]
        response = q["response"]
        expected = q["expected"]
        JUDGE_PROMPT = f"""Grade the answer against the expected answer.

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

        First state the single biggest flaw, then score.

        Question: {question}
        Answer: {response}
        Expected: {expected}

        Flaw:"""
        interaction = client.interactions.create(
            model=model,
            system_instruction="You are a strict evaluator. Answer under 100 characters",
            input=JUDGE_PROMPT,
            response_format=SCHEMA,
            store=False,
        )

        result = json.loads(interaction.output_text)
        
        print(f"Score: {result['score']} — {result['reason']}\n")
        scores.append(result["score"])
    return scores

        


