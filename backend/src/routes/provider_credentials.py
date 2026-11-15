from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select
from src.db import SessionDep
from src.models import ProviderCredential, Users, ProofUserRole
from src.security import encrypt_api_key
from src.utils import get_current_user
from src.llm import PROVIDERS

router = APIRouter(prefix="/api/provider-credentials", dependencies=[Depends(get_current_user)])


class ProviderCredentialCreate(BaseModel):
    provider: str
    api_key: str
    base_url: str | None = None


class ProviderCredentialResponse(BaseModel):
    id: int
    provider: str
    base_url: str | None = None
    is_active: bool
    created_at: str


@router.get("", response_model=list[ProviderCredentialResponse])
def list_credentials(
    session: SessionDep,
    user: Users = Depends(get_current_user),
):
    """List the current user's stored provider credentials (keys are masked)."""
    stmt = select(ProviderCredential).where(
        ProviderCredential.user_id == user.id,
        ProviderCredential.is_active == True,
    )
    creds = session.exec(stmt).all()
    return [
        ProviderCredentialResponse(
            id=c.id,
            provider=c.provider,
            base_url=c.base_url,
            is_active=c.is_active,
            created_at=c.created_at.isoformat(),
        )
        for c in creds
    ]


@router.post("", response_model=ProviderCredentialResponse, status_code=status.HTTP_201_CREATED)
def upsert_credential(
    data: ProviderCredentialCreate,
    session: SessionDep,
    user: Users = Depends(get_current_user),
):
    """Add or update a provider API key for the current user."""
    provider = data.provider.lower()
    if provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    stmt = select(ProviderCredential).where(
        ProviderCredential.user_id == user.id,
        ProviderCredential.provider == provider,
        ProviderCredential.is_active == True,
    )
    existing = session.exec(stmt).first()

    encrypted_key = encrypt_api_key(data.api_key)

    if existing:
        existing.encrypted_api_key = encrypted_key
        existing.base_url = data.base_url
        session.add(existing)
        session.commit()
        session.refresh(existing)
        cred = existing
    else:
        cred = ProviderCredential(
            user_id=user.id,
            provider=provider,
            encrypted_api_key=encrypted_key,
            base_url=data.base_url,
        )
        session.add(cred)
        session.commit()
        session.refresh(cred)

    return ProviderCredentialResponse(
        id=cred.id,
        provider=cred.provider,
        base_url=cred.base_url,
        is_active=cred.is_active,
        created_at=cred.created_at.isoformat(),
    )


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_credential(
    credential_id: int,
    session: SessionDep,
    user: Users = Depends(get_current_user),
):
    """Deactivate (soft-delete) a stored provider credential."""
    stmt = select(ProviderCredential).where(
        ProviderCredential.id == credential_id,
        ProviderCredential.user_id == user.id,
    )
    cred = session.exec(stmt).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")

    cred.is_active = False
    session.add(cred)
    session.commit()
    return None
