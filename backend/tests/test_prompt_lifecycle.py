import asyncio

import pytest
from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine

from src.models import PromptRegistry, ProofUserRole, Users
from src.routes.prompts import (
    PromptRegistryCreate,
    PromptVersionCreate,
    activate_prompt_version,
    compare_prompt_versions,
    create_prompt_registry,
    create_prompt_version,
    delete_prompt_registry,
    delete_prompt_version,
    get_prompt_registry,
)


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
        SQLModel.metadata.drop_all(engine)


def _user(session, user_id=1, role=ProofUserRole.MEMBER):
    user = Users(id=user_id, name="u", email=f"u{user_id}@example.com", role=role)
    session.add(user)
    session.commit()
    return user


def _create(session, user, content="one"):
    registry = asyncio.run(
        create_prompt_registry(
            PromptRegistryCreate(name="R", initial_content=content),
            session,
            user,
            user,
            None,
        )
    )
    return registry["id"]


def test_version_lifecycle_delete_and_no_sequence_reuse(session):
    user = _user(session)
    registry_id = _create(session, user)

    v2 = asyncio.run(
        create_prompt_version(
            registry_id, PromptVersionCreate(content="two"), session, user, user, None
        )
    )
    v3 = asyncio.run(
        create_prompt_version(
            registry_id, PromptVersionCreate(content="three"), session, user, user, None
        )
    )
    assert (v2.version_number, v3.version_number) == (2, 3)

    detail = asyncio.run(get_prompt_registry(registry_id, session, user, user))
    assert detail.current_version.version_number == 1

    asyncio.run(activate_prompt_version(registry_id, v3.id, session, user, user, None))
    detail = asyncio.run(get_prompt_registry(registry_id, session, user, user))
    assert detail.current_version.version_number == 3

    # delete the middle version, then create: number 4, never reused
    asyncio.run(delete_prompt_version(registry_id, v2.id, session, user, user, None))
    v4 = asyncio.run(
        create_prompt_version(
            registry_id, PromptVersionCreate(content="four"), session, user, user, None
        )
    )
    assert v4.version_number == 4

    detail = asyncio.run(get_prompt_registry(registry_id, session, user, user))
    assert detail.version_count == 3
    assert [v.version_number for v in detail.versions] == [4, 3, 1]

    # deleting the active version promotes the newest remaining one
    asyncio.run(delete_prompt_version(registry_id, v3.id, session, user, user, None))
    detail = asyncio.run(get_prompt_registry(registry_id, session, user, user))
    assert detail.current_version.version_number == 4


def test_compare_first_and_last_version(session):
    user = _user(session)
    registry_id = _create(session, user, "alpha\nbeta")
    v2 = asyncio.run(
        create_prompt_version(
            registry_id,
            PromptVersionCreate(content="alpha\ngamma"),
            session,
            user,
            user,
            None,
        )
    )

    detail = asyncio.run(get_prompt_registry(registry_id, session, user, user))
    first = detail.versions[-1]
    comparison = asyncio.run(
        compare_prompt_versions(registry_id, first.id, v2.id, session, user, user)
    )

    assert "-beta" in comparison.diff
    assert "+gamma" in comparison.diff


def test_foreign_member_cannot_version_registry(session):
    owner = _user(session, 1)
    other = _user(session, 2)
    registry_id = _create(session, owner)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            create_prompt_version(
                registry_id,
                PromptVersionCreate(content="x"),
                session,
                other,
                other,
                None,
            )
        )
    assert exc.value.status_code == 403


def test_deleted_registry_is_gone(session):
    user = _user(session)
    registry_id = _create(session, user)

    asyncio.run(delete_prompt_registry(registry_id, session, user, user, None))

    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_prompt_registry(registry_id, session, user, user))
    assert exc.value.status_code == 404

    # soft-deleted row still exists, but is not served
    assert session.get(PromptRegistry, registry_id).deleted_at is not None
