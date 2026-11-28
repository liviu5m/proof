import pytest
from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine

from src.models import PromptRegistry, PromptVersion, ProofUserRole, Runs, Users
from src.routes.runs import (
    RunCreateRequest,
    _prompt_version_summaries,
    resolve_system_prompt,
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


def _registry(session, owner_id=1, content="Version prompt"):
    registry = PromptRegistry(name="R", user_id=owner_id)
    session.add(registry)
    session.commit()
    session.refresh(registry)

    version = PromptVersion(
        registry_id=registry.id,
        content_hash="h",
        content=content,
        is_current=True,
        sequence=1,
    )
    session.add(version)
    session.commit()
    session.refresh(version)
    return registry, version


def test_raw_prompt_used_without_version(session):
    user = _user(session)
    payload = RunCreateRequest(dataset_id=1, system_prompt="  plain prompt  ")

    assert resolve_system_prompt(session, user, payload) == "plain prompt"


def test_version_content_overrides_raw_prompt(session):
    user = _user(session)
    _, version = _registry(session, content="From version")
    payload = RunCreateRequest(
        dataset_id=1, system_prompt="ignored", prompt_version_id=version.id
    )

    assert resolve_system_prompt(session, user, payload) == "From version"


def test_deleted_version_is_rejected(session):
    user = _user(session)
    _, version = _registry(session)
    version.deleted_at = version.created_at
    session.add(version)
    session.commit()

    payload = RunCreateRequest(dataset_id=1, prompt_version_id=version.id)
    with pytest.raises(HTTPException) as exc:
        resolve_system_prompt(session, user, payload)
    assert exc.value.status_code == 404


def test_other_users_version_is_forbidden(session):
    user = _user(session, user_id=1)
    _user(session, user_id=2)
    _, version = _registry(session, owner_id=2)

    payload = RunCreateRequest(dataset_id=1, prompt_version_id=version.id)
    with pytest.raises(HTTPException) as exc:
        resolve_system_prompt(session, user, payload)
    assert exc.value.status_code == 403


def test_admin_can_use_any_version(session):
    admin = _user(session, user_id=1, role=ProofUserRole.ADMIN)
    _user(session, user_id=2)
    _, version = _registry(session, owner_id=2, content="Admin sees this")

    payload = RunCreateRequest(dataset_id=1, prompt_version_id=version.id)
    assert resolve_system_prompt(session, admin, payload) == "Admin sees this"


def test_run_summary_includes_ordinal_and_hash(session):
    _user(session)
    registry, version = _registry(session, content="first")
    newer = PromptVersion(
        registry_id=registry.id,
        sequence=2,
        content_hash="abc123",
        content="second",
    )
    session.add(newer)
    session.commit()
    session.refresh(newer)

    run = Runs(
        dataset_id=1,
        model="m",
        system_prompt="second",
        judge_model="j",
        total=1,
        prompt_version_id=newer.id,
    )
    session.add(run)
    session.commit()

    summaries = _prompt_version_summaries(session, [run])
    assert summaries[newer.id] == {
        "id": newer.id,
        "registry_id": registry.id,
        "version_number": 2,
        "content_hash": "abc123",
        "deleted": False,
    }
    assert version.id not in summaries


def test_run_persists_prompt_version_id(session):
    run = Runs(
        dataset_id=1,
        model="m",
        system_prompt="p",
        judge_model="j",
        total=1,
        prompt_version_id=7,
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    stored = session.get(Runs, run.id)
    assert stored.prompt_version_id == 7
