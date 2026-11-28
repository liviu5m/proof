import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlmodel import Session, SQLModel, create_engine

from src.models import Datasets, ProofUserRole, Runs, TokenUsage, Users
from src.routes.runs import get_usage


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
    dataset = Datasets(
        id=1, name="QA", source_path="1/a.csv", item_count=2, hash="h", user_id=1
    )
    session.add(dataset)
    run = Runs(
        id=1,
        dataset_id=1,
        model="m",
        system_prompt="p",
        judge_model="j",
        total=2,
    )
    session.add(run)
    session.add(
        TokenUsage(
            run_id=1,
            model="m",
            provider="google",
            prompt_tokens=100,
            completion_tokens=50,
            cost_usd=0.5,
        )
    )
    session.add(
        TokenUsage(
            run_id=1,
            model="m",
            provider="ollama",
            prompt_tokens=10,
            completion_tokens=5,
            cost_usd=None,
        )
    )
    session.commit()
    return user


def test_usage_totals_and_unpriced_count(session):
    user = _seed(session)

    result = asyncio.run(get_usage(session=session, user=user, _=user, days=30))

    assert result["totals"]["runs"] == 1
    assert result["totals"]["prompt_tokens"] == 110
    assert result["totals"]["completion_tokens"] == 55
    assert result["totals"]["cost_usd"] == 0.5
    assert result["totals"]["unpriced_runs"] == 1
    assert result["datasets"][0]["dataset_name"] == "QA"
    assert result["daily"][0]["tokens"] == 165


def test_usage_window_and_estimated_flag(session):
    user = _seed(session)
    session.add(
        TokenUsage(
            run_id=1,
            model="m",
            provider="google",
            prompt_tokens=7,
            completion_tokens=3,
            cost_usd=1.0,
            usage_estimated=True,
            created_at=datetime.now(UTC) - timedelta(days=90),
        )
    )
    session.commit()

    result = asyncio.run(get_usage(session=session, user=user, _=user, days=30))

    # the 90-day-old row is outside the window
    assert result["totals"]["prompt_tokens"] == 110
    assert result["totals"]["cost_usd"] == 0.5
    assert result["totals"]["estimated"] is False

    session.add(
        TokenUsage(
            run_id=1,
            model="m",
            provider="google",
            usage_estimated=True,
        )
    )
    session.commit()

    result = asyncio.run(get_usage(session=session, user=user, _=user, days=30))
    assert result["totals"]["estimated"] is True


def test_usage_is_owner_scoped(session):
    _seed(session)
    other = Users(id=2, name="o", email="o@example.com")

    result = asyncio.run(get_usage(session=session, user=other, _=other, days=30))

    assert result["totals"]["runs"] == 0
    assert result["datasets"] == []
