import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine

from src.models import PromptRegistry, PromptVersion, Users
from src.utils import next_version_sequence


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
        SQLModel.metadata.drop_all(engine)


def _registry(session):
    session.add(Users(id=1, name="u", email="u@example.com"))
    registry = PromptRegistry(name="R", user_id=1)
    session.add(registry)
    session.commit()
    session.refresh(registry)
    return registry


def test_sequence_not_reused_after_soft_delete(session):
    registry = _registry(session)
    first = PromptVersion(
        registry_id=registry.id, sequence=1, content_hash="a", content="a"
    )
    second = PromptVersion(
        registry_id=registry.id, sequence=2, content_hash="b", content="b"
    )
    session.add(first)
    session.add(second)
    session.commit()

    second.deleted_at = second.created_at
    session.add(second)
    session.commit()

    # the deleted row still holds 2, so later numbers keep their value and the next is 3
    assert next_version_sequence(session, registry.id) == 3


def test_duplicate_sequence_is_rejected(session):
    registry = _registry(session)
    session.add(
        PromptVersion(
            registry_id=registry.id, sequence=1, content_hash="a", content="a"
        )
    )
    session.commit()

    session.add(
        PromptVersion(
            registry_id=registry.id, sequence=1, content_hash="b", content="b"
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
