from google import genai
from fastapi import Depends
from .config import settings 

def get_llm_client(settings):
    return genai.Client(api_key=settings.GEMINI_API_KEY)
