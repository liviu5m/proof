from google import genai
from .config import settings


def get_llm_client():
    return genai.Client(api_key=settings.GEMINI_API_KEY)
