from sqlmodel import select

from src.models import ProviderCredential

from .config import settings
from .llm import PROVIDERS, LLMProviderConfig
from .security import decrypt_api_key


def get_llm_provider(
    provider: str,
    user_id: int | None = None,
    session=None,
    ollama_base_url: str | None = None,
):
    """Returns an LLMProvider instance for the given provider name.

    Priority:
      1. User's stored ProviderCredential (if user_id + session provided)
      2. Server env var fallback
    """
    provider_class = PROVIDERS.get(provider.lower())
    if provider_class is None:
        raise ValueError(f"Unknown provider: {provider}")

    api_key = None
    base_url = None

    if user_id is not None and session is not None:
        cred = session.exec(
            select(ProviderCredential).where(
                ProviderCredential.user_id == user_id,
                ProviderCredential.provider == provider.lower(),
                ProviderCredential.is_active,
            )
        ).first()
        if cred:
            api_key = decrypt_api_key(cred.encrypted_api_key)
            base_url = cred.base_url

    if api_key is None:
        api_key_map = {
            "google": settings.GEMINI_API_KEY,
            "openai": getattr(settings, "OPENAI_API_KEY", None),
            "anthropic": getattr(settings, "ANTHROPIC_API_KEY", None),
            "ollama": None,
        }
        api_key = api_key_map.get(provider.lower())

    if provider.lower() == "ollama" and ollama_base_url:
        base_url = ollama_base_url
    elif base_url is None:
        base_url = getattr(settings, "OLLAMA_BASE_URL", None)

    config = LLMProviderConfig(api_key=api_key, base_url=base_url)
    return provider_class(config)
