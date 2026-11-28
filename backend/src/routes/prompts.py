from datetime import UTC, datetime
from difflib import unified_diff

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from src.db import SessionDep
from src.models import PromptRegistry, PromptVersion, Users
from src.utils import (
    get_current_user,
    get_current_version,
    get_registry_or_404,
    hash_content,
    next_version_sequence,
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
    current_version_position: int | None
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
    version_number: int
    created_at: datetime


class PromptRegistryDetailOut(BaseModel):
    id: int
    name: str
    description: str | None
    user_id: int
    current_version_id: int | None
    current_version: PromptVersionOut | None
    current_version_position: int | None
    version_count: int
    versions: list[PromptVersionOut]
    created_at: datetime
    updated_at: datetime


class PromptVersionCreate(BaseModel):
    content: str
    description: str | None = None


class PromptRegistryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class PromptCompareOut(BaseModel):
    v1: PromptVersionOut
    v2: PromptVersionOut
    diff: str


def version_out(version: PromptVersion) -> PromptVersionOut:
    assert version.id is not None
    return PromptVersionOut(
        id=version.id,
        registry_id=version.registry_id,
        content_hash=version.content_hash,
        content=version.content,
        description=version.description,
        is_current=version.is_current,
        version_number=version.sequence,
        created_at=version.created_at,
    )


def _touch_registry(registry: PromptRegistry) -> None:
    registry.updated_at = datetime.now(UTC)


def _versions_for(session: Session, registry_id: int) -> list[PromptVersion]:
    stmt = select(PromptVersion).where(
        PromptVersion.registry_id == registry_id,
        PromptVersion.deleted_at == None,
    )
    return list(session.exec(stmt).all())


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
        PromptRegistry.deleted_at == None,
    )
    if search:
        stmt = stmt.where(PromptRegistry.name.ilike(f"%{search}%"))  # type: ignore[attr-defined]
    stmt = stmt.order_by(desc(PromptRegistry.created_at))  # type: ignore[arg-type]
    registries = session.exec(stmt).all()
    return [registry_out(session, r) for r in registries]


@router.post("", response_model=PromptRegistryOut, status_code=status.HTTP_201_CREATED)
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

    assert user.id is not None
    registry = PromptRegistry(
        name=name,
        description=payload.description,
        user_id=user.id,
    )
    session.add(registry)
    session.commit()
    session.refresh(registry)

    assert registry.id is not None
    content_hash = hash_content(payload.initial_content)
    version = PromptVersion(
        registry_id=registry.id,
        content_hash=content_hash,
        content=payload.initial_content,
        description="Initial version",
        is_current=True,
        sequence=1,
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
    assert registry.id is not None

    versions_stmt = (
        select(PromptVersion)
        .where(
            PromptVersion.registry_id == registry_id,
            PromptVersion.deleted_at == None,
        )
        .order_by(desc(PromptVersion.created_at))  # type: ignore[arg-type]
    )
    versions = session.exec(versions_stmt).all()

    current = get_current_version(versions)

    return PromptRegistryDetailOut(
        id=registry.id,
        name=registry.name,
        description=registry.description,
        user_id=registry.user_id,
        current_version_id=current.id if current else None,
        current_version_position=current.sequence if current else None,
        version_count=len(versions),
        current_version=(version_out(current) if current else None),
        versions=[version_out(v) for v in versions],
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
    version = None
    for _attempt in range(3):
        candidate = PromptVersion(
            registry_id=registry_id,
            content_hash=content_hash,
            content=payload.content,
            description=payload.description,
            is_current=False,
            sequence=next_version_sequence(session, registry_id),
        )
        session.add(candidate)
        _touch_registry(registry)
        session.add(registry)
        try:
            session.commit()
        except IntegrityError:
            # another create took this sequence: retry with a fresh MAX+1
            session.rollback()
            session.refresh(registry)
            continue
        version = candidate
        break

    if version is None:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Could not allocate a version number, retry",
                "code": "sequence_conflict",
            },
        )

    session.refresh(version)
    return version_out(version)


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
        PromptVersion.deleted_at == None,
    )
    version = session.exec(version_stmt).first()
    if not version:
        raise HTTPException(
            status_code=404,
            detail={"error": "Version not found", "code": "not_found"},
        )

    all_versions_stmt = select(PromptVersion).where(
        PromptVersion.registry_id == registry_id,
        PromptVersion.deleted_at == None,
    )
    all_versions = session.exec(all_versions_stmt).all()
    for v in all_versions:
        v.is_current = False
        session.add(v)

    version.is_current = True
    session.add(version)
    _touch_registry(registry)
    session.add(registry)
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
    get_registry_or_404(session, registry_id, user)

    v1_stmt = select(PromptVersion).where(
        PromptVersion.id == v1,
        PromptVersion.registry_id == registry_id,
        PromptVersion.deleted_at == None,
    )
    v2_stmt = select(PromptVersion).where(
        PromptVersion.id == v2,
        PromptVersion.registry_id == registry_id,
        PromptVersion.deleted_at == None,
    )
    version1 = session.exec(v1_stmt).first()
    version2 = session.exec(v2_stmt).first()

    if not version1 or not version2:
        raise HTTPException(
            status_code=404,
            detail={"error": "One or both versions not found", "code": "not_found"},
        )

    version1.content.splitlines(keepends=True)
    version2.content.splitlines(keepends=True)

    diff = "".join(
        unified_diff(
            version1.content.splitlines(keepends=True),
            version2.content.splitlines(keepends=True),
            fromfile=f"v{version1.sequence}",
            tofile=f"v{version2.sequence}",
        )
    )

    return PromptCompareOut(
        v1=version_out(version1),
        v2=version_out(version2),
        diff=diff,
    )


@router.patch("/{registry_id}", response_model=PromptRegistryOut)
async def update_prompt_registry(
    registry_id: int,
    payload: PromptRegistryUpdate,
    session: SessionDep,
    user: Users = Depends(get_current_user),
    _: Users = Depends(require_member),
    __: Request = Depends(verify_csrf),
):
    registry = get_registry_or_404(session, registry_id, user)

    if payload.name is not None:
        name = payload.name.strip()
        if not name:
            raise HTTPException(
                status_code=400,
                detail={"error": "Registry name is required", "code": "invalid_name"},
            )
        if len(name) > 200:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Registry name must be 200 characters or fewer",
                    "code": "invalid_name",
                },
            )
        registry.name = name

    if payload.description is not None:
        description = payload.description.strip()
        if len(description) > 1000:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Description must be 1000 characters or fewer",
                    "code": "invalid_description",
                },
            )
        registry.description = description or None

    _touch_registry(registry)
    session.add(registry)
    session.commit()

    return registry_out(session, registry)


@router.delete("/{registry_id}/versions/{version_id}", status_code=status.HTTP_200_OK)
async def delete_prompt_version(
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
        PromptVersion.deleted_at == None,
    )
    version = session.exec(version_stmt).first()
    if not version:
        raise HTTPException(
            status_code=404,
            detail={"error": "Version not found", "code": "not_found"},
        )

    version.deleted_at = datetime.now(UTC)
    version.is_current = False
    session.add(version)
    session.commit()

    # Promote the newest remaining version if the active one was deleted
    remaining = _versions_for(session, registry_id)
    if remaining and not any(v.is_current for v in remaining):
        newest = max(remaining, key=lambda v: (v.created_at, v.id or 0))
        newest.is_current = True
        session.add(newest)

    _touch_registry(registry)
    session.add(registry)
    session.commit()

    return {"success": "Version deleted"}


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
