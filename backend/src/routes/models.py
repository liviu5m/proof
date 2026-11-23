import logging

import httpx
from fastapi import APIRouter, Depends, status
from sqlmodel import select

from src.db import SessionDep
from src.models import ModelCatalog, ProviderCredential, Users
from src.security import decrypt_api_key
from src.utils import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", dependencies=[Depends(get_current_user)])

PROVIDER_ENDPOINTS = {
    "openai": "https://api.openai.com/v1/models",
    "anthropic": "https://api.anthropic.com/v1/models",
    "google": "https://generativelanguage.googleapis.com/v1beta/models",
    "ollama": "http://localhost:11434/api/tags",
}


@router.get("")
async def list_models(
    session: SessionDep,
    user: Users = Depends(get_current_user),
):
    """List all active models from the catalog."""
    stmt = select(ModelCatalog).where(ModelCatalog.is_active)
    models = session.exec(stmt).all()
    return [
        {
            "id": m.model_id,
            "name": m.name,
            "provider": m.provider,
            "supports_json_mode": m.supports_json_mode,
            "supports_system_prompt": m.supports_system_prompt,
            "max_tokens": m.max_tokens,
            "input_cost_per_1m": float(m.input_cost_per_1m) if m.input_cost_per_1m else None,
            "output_cost_per_1m": float(m.output_cost_per_1m) if m.output_cost_per_1m else None,
        }
        for m in models
    ]


@router.post("/sync", status_code=status.HTTP_200_OK)
async def sync_models(
    session: SessionDep,
    user: Users = Depends(get_current_user),
):
    """Fetch models from provider APIs and upsert into the catalog."""
    synced = []
    errors = []

    for provider, endpoint in PROVIDER_ENDPOINTS.items():
        # Get API key: user's stored credential first, then env fallback
        cred = session.exec(
            select(ProviderCredential).where(
                ProviderCredential.user_id == user.id,
                ProviderCredential.provider == provider,
                ProviderCredential.is_active,
            )
        ).first()
        api_key = decrypt_api_key(cred.encrypted_api_key) if cred else None

        # Skip providers without an API key (except Ollama which runs locally)
        if api_key is None and provider != "ollama":
            errors.append({provider: "No API key configured"})
            continue

        try:
            async with httpx.AsyncClient(timeout=30) as http:
                headers: dict[str, str] = {}

                # Provider-specific auth
                if provider == "google":
                    # Google uses ?key= query parameter, not Bearer token
                    if api_key:
                        endpoint_with_key = f"{endpoint}?key={api_key}"
                    else:
                        endpoint_with_key = endpoint
                    resp = await http.get(endpoint_with_key, headers=headers)
                elif provider == "anthropic":
                    if api_key:
                        headers["x-api-key"] = api_key
                        headers["anthropic-version"] = "2023-06-01"
                    resp = await http.get(endpoint, headers=headers)
                elif provider == "openai":
                    if api_key:
                        headers["Authorization"] = f"Bearer {api_key}"
                    resp = await http.get(endpoint, headers=headers)
                elif provider == "ollama":
                    resp = await http.get(endpoint, headers=headers)
                else:
                    resp = await http.get(endpoint, headers=headers)

                if resp.status_code != 200:
                    errors.append({provider: f"HTTP {resp.status_code}"})
                    continue
                data = resp.json()
            # Parse provider-specific response (get name from API, fallback to id)
            if provider == "openai":
                raw_models = data.get("data", [])
                provider_models = [
                    {"id": m.get("id", ""), "name": m.get("id", "")} for m in raw_models
                ]
            elif provider == "anthropic":
                raw_models = data.get("data", [])
                provider_models = [
                    {"id": m.get("id", ""), "name": m.get("name") or m.get("id", "")}
                    for m in raw_models
                ]
            elif provider == "google":
                raw_models = data.get("models", [])
                provider_models = [
                    {
                        "id": m.get("name", "").replace("models/", ""),
                        "name": m.get("display_name")
                        or m.get("name", "").replace("models/", ""),
                    }
                    for m in raw_models
                ]
            elif provider == "ollama":
                raw_models = data.get("models", [])
                provider_models = [
                    {"id": m.get("name", ""), "name": m.get("name", "")}
                    for m in raw_models
                ]
            else:
                provider_models = []

            # Upsert into catalog (no unique constraint needed)
            for model in provider_models:
                model_id = model["id"]
                name = model["name"] or model_id
                if not model_id:
                    continue

                existing = session.exec(
                    select(ModelCatalog).where(
                        ModelCatalog.provider == provider,
                        ModelCatalog.model_id == model_id,
                    )
                ).first()

                if existing:
                    existing.name = name
                    existing.is_active = True
                    session.add(existing)
                else:
                    new_model = ModelCatalog(
                        provider=provider,
                        model_id=model_id,
                        name=name,
                        supports_json_mode=False,
                        supports_system_prompt=True,
                        is_active=True,
                    )
                    session.add(new_model)

                synced.append(
                    {"provider": provider, "model_id": model_id, "name": name}
                )

        except Exception as e:
            logger.error(f"Failed to sync {provider}: {e}")
            errors.append({provider: str(e)})
            continue

    session.commit()
    return {"synced": synced, "count": len(synced), "errors": errors}
