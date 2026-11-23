from datetime import UTC, datetime
from difflib import unified_diff

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc
from sqlmodel import select

from src.db import SessionDep
from src.models import PromptRegistry, PromptVersion, ProofUserRole, Users
from src.utils import (
    get_current_user,
    get_registry_or_404,
    hash_content,
    registry_out,
    require_member,
    require_viewer,
    verify_csrf,
    verifyUserTokenSession,
)

router = APIRouter(
    prefix="/api/prompts",
    dependencies=[Depends(verifyUserTokenSession)],
)




class PromptRegistryCreate(BaseModel):
    name: str
    description: str | None = None
    initial_content: str


class PromptRegistryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None
    user_id: int
    current_version_id: int | None
    version_count: int
    created_at: datetime
    updated_at: datetime


class PromptVersionOut(BaseModel):
    id: int
    registry_id: int
    content_hash: str
    content: str
    description: str | None
    is_current: bool
    created_at: datetime


class PromptRegistryDetailOut(BaseModel):
    id: int
    name: str
    description: str | None
    user_id: int
    current_version: PromptVersionOut | None
    versions: list[PromptVersionOut]
    created_at: datetime
    updated_at: datetime


class PromptVersionCreate(BaseModel):
    content: str
    description: str | None = None


class PromptCompareOut(BaseModel):
    v1: PromptVersionOut
    v2: PromptVersionOut
    diff: str


# ── Endpoints ───────────────────────────────────────────────────────────


@router.get("", response_model=list[PromptRegistryOut])
async def list_prompt_registries(
    session: SessionDep,
    user: Users = Depends(get_current_user),
    _: Users = Depends(require_viewer),
    search: str | None = None,
):
    stmt = select(PromptRegistry).where(
        PromptRegistry.user_id == user.id,
        PromptRegistry.deleted_at == None,  # noqa: E712
    )
    if search:
        stmt = stmt.where(PromptRegistry.name.ilike(f"%{search}%"))  # type: ignore[attr-defined]
    stmt = stmt.order_by(desc(PromptRegistry.created_at))
    registries = session.exec(stmt).all()
    return [registry_out(session, r) for r in registries]


@router.post(
    "", response_model=PromptRegistryOut, status_code=status.HTTP_201_CREATED
)
async def create_prompt_registry(
    payload: PromptRegistryCreate,
    session: SessionDep,
    user: Users = Depends(get_current_user),
    _: Users = Depends(require_member),
    __: Request = Depends(verify_csrf),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(
            status_code=400,
            detail={"error": "Registry name is required", "code": "invalid_name"},
        )

    registry = PromptRegistry(
        name=name,
        description=payload.description,
        user_id=user.id,
    )
    session.add(registry)
    session.commit()
    session.refresh(registry)

    content_hash = hash_content(payload.initial_content)
    version = PromptVersion(
        registry_id=registry.id,
        content_hash=content_hash,
        content=payload.initial_content,
        description="Initial version",
        is_current=True,
    )
    session.add(version)
    session.commit()
    session.refresh(version)

    return registry_out(session, registry)


@router.get("/{registry_id}", response_model=PromptRegistryDetailOut)
async def get_prompt_registry(
    registry_id: int,
    session: SessionDep,
    user: Users = Depends(get_current_user),
    _: Users = Depends(require_viewer),
):
    registry = get_registry_or_404(session, registry_id, user)

    versions_stmt = select(PromptVersion).where(
        PromptVersion.registry_id == registry_id,
        PromptVersion.deleted_at == None,  # noqa: E712
    ).order_by(desc(PromptVersion.created_at))
    versions = session.exec(versions_stmt).all()

    current = next((v for v in versions if v.is_current), None)

    return PromptRegistryDetailOut(
        id=registry.id,
        name=registry.name,
        description=registry.description,
        user_id=registry.user_id,
        current_version=(
            PromptVersionOut.model_validate(current, from_attributes=True) if current else None
        ),
        versions=[PromptVersionOut.model_validate(v,from_attributes=True) for v in versions],
        created_at=registry.created_at,
        updated_at=registry.updated_at,
    )


@router.post(
    "/{registry_id}/versions",
    response_model=PromptVersionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_prompt_version(
    registry_id: int,
    payload: PromptVersionCreate,
    session: SessionDep,
    user: Users = Depends(get_current_user),
    _: Users = Depends(require_member),
    __: Request = Depends(verify_csrf),
):
    registry = get_registry_or_404(session, registry_id, user)

    content_hash = hash_content(payload.content)
    version = PromptVersion(
        registry_id=registry_id,
        content_hash=content_hash,
        content=payload.content,
        description=payload.description,
        is_current=False,
    )
    session.add(version)
    session.commit()
    session.refresh(version)

    return PromptVersionOut.model_validate(version,from_attributes=True )


@router.post(
    "/{registry_id}/versions/{version_id}/activate",
    response_model=PromptRegistryOut,
)
async def activate_prompt_version(
    registry_id: int,
    version_id: int,
    session: SessionDep,
    user: Users = Depends(get_current_user),
    _: Users = Depends(require_member),
    __: Request = Depends(verify_csrf),
):
    registry = get_registry_or_404(session, registry_id, user)

    version_stmt = select(PromptVersion).where(
        PromptVersion.id == version_id,
        PromptVersion.registry_id == registry_id,
        PromptVersion.deleted_at == None,  # noqa: E712
    )
    version = session.exec(version_stmt).first()
    if not version:
        raise HTTPException(
            status_code=404,
            detail={"error": "Version not found", "code": "not_found"},
        )

    all_versions_stmt = select(PromptVersion).where(
        PromptVersion.registry_id == registry_id,
        PromptVersion.deleted_at == None,  # noqa: E712
    )
    all_versions = session.exec(all_versions_stmt).all()
    for v in all_versions:
        v.is_current = False
        session.add(v)

    version.is_current = True
    session.add(version)
    session.commit()

    return registry_out(session, registry)


@router.get("/{registry_id}/compare", response_model=PromptCompareOut)
async def compare_prompt_versions(
    registry_id: int,
    v1: int,
    v2: int,
    session: SessionDep,
    user: Users = Depends(get_current_user),
    _: Users = Depends(require_viewer),
):
    registry = get_registry_or_404(session, registry_id, user)

    v1_stmt = select(PromptVersion).where(
        PromptVersion.id == v1,
        PromptVersion.registry_id == registry_id,
        PromptVersion.deleted_at == None,  # noqa: E712
    )
    v2_stmt = select(PromptVersion).where(
        PromptVersion.id == v2,
        PromptVersion.registry_id == registry_id,
        PromptVersion.deleted_at == None,  # noqa: E712
    )
    version1 = session.exec(v1_stmt).first()
    version2 = session.exec(v2_stmt).first()

    if not version1 or not version2:
        raise HTTPException(
            status_code=404,
            detail={"error": "One or both versions not found", "code": "not_found"},
        )

    lines1 = version1.content.splitlines(keepends=True)
    lines2 = version2.content.splitlines(keepends=True)
    diff = "".join(
        unified_diff(
            lines1,
            lines2,
            fromfile=f"v{version1.id}",
            tofile=f"v{version2.id}",
        )
    )

    return PromptCompareOut(
        v1=PromptVersionOut.model_validate(version1,from_attributes=True ),
        v2=PromptVersionOut.model_validate(version2, from_attributes=True),
        diff=diff,
    )


@router.delete("/{registry_id}", status_code=status.HTTP_200_OK)
async def delete_prompt_registry(
    registry_id: int,
    session: SessionDep,
    user: Users = Depends(get_current_user),
    _: Users = Depends(require_member),
    __: Request = Depends(verify_csrf),
):
    registry = get_registry_or_404(session, registry_id, user)
    registry.deleted_at = datetime.now(UTC)
    session.add(registry)
    session.commit()
    return {"success": "Registry deleted"}
