from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client()

def run_tests(questions, prompt, model):
    data = []
    for q in questions:
        interaction = client.interactions.create(
            model=model,
            system_instruction=prompt,
            input=q["input"],
            generation_config={"thinking_level": "minimal"},
            store=False,
        )    
        print(f"Q: {q}")
        print(f"A: {interaction.output_text}\n")
        data.append({
            "input": q["input"],
            "response": interaction.output_text,
            "expected": q["expected"]
        })

    return data

