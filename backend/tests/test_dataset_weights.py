import asyncio

import pytest
from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine

from src.models import Datasets, ProofUserRole, Users
from src.routes.datasets import ScorerWeightsIn, updateDatasetScorerWeights


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
        SQLModel.metadata.drop_all(engine)


def _seed(session):
    user = Users(id=1, name="u", email="u@example.com", role=ProofUserRole.MEMBER)
    session.add(user)
    session.add(
        Datasets(
            id=1, name="QA", source_path="1/a.csv", item_count=1, hash="h", user_id=1
        )
    )
    session.commit()
    return user


def test_save_then_overwrite_weights(session):
    user = _seed(session)

    first = asyncio.run(
        updateDatasetScorerWeights(
            1,
            ScorerWeightsIn(rule=0.5, llm=0.5, semantic=0),
            session,
            user,
            user,
            None,
        )
    )
    assert first["scorer_weights"] == {"rule": 0.5, "llm": 0.5, "semantic": 0.0}

    second = asyncio.run(
        updateDatasetScorerWeights(
            1,
            ScorerWeightsIn(rule=0, llm=0.2, semantic=0.8),
            session,
            user,
            user,
            None,
        )
    )
    assert second["scorer_weights"] == {"rule": 0.0, "llm": 0.2, "semantic": 0.8}


def test_all_zero_weights_rejected(session):
    user = _seed(session)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            updateDatasetScorerWeights(
                1,
                ScorerWeightsIn(rule=0, llm=0, semantic=0),
                session,
                user,
                user,
                None,
            )
        )
    assert exc.value.status_code == 400
    assert exc.value.detail["code"] == "invalid_scorer_weights"


def test_foreign_dataset_is_not_found(session):
    _seed(session)
    other = Users(id=2, name="o", email="o@example.com")

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            updateDatasetScorerWeights(
                1,
                ScorerWeightsIn(rule=1, llm=0, semantic=0),
                session,
                other,
                other,
                None,
            )
        )
    assert exc.value.status_code == 404
