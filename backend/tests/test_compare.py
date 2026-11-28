import asyncio

import pytest
from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine, select

from src.models import (
    Datasets,
    ProofUserRole,
    Results,
    Runs,
    TokenUsage,
    Users,
)
from src.routes.runs import compare_runs


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
            id=1, name="QA", source_path="1/a.csv", item_count=2, hash="h", user_id=1
        )
    )
    session.add(
        Runs(
            id=1,
            dataset_id=1,
            model="m",
            system_prompt="p",
            judge_model="j",
            total=2,
            avg_score=4.5,
        )
    )
    session.add(
        Runs(
            id=2,
            dataset_id=1,
            model="m",
            system_prompt="p",
            judge_model="j",
            total=2,
            avg_score=3.5,
        )
    )
    session.add_all(
        [
            Results(
                run_id=1,
                idx=0,
                question="q1",
                expected="a",
                response="apple",
                score=4.0,
            ),
            Results(
                run_id=2,
                idx=0,
                question="q1",
                expected="a",
                response="orange",
                score=3.0,
            ),
            Results(
                run_id=1, idx=1, question="q2", expected="b", response="same", score=5.0
            ),
            Results(
                run_id=2, idx=1, question="q2", expected="b", response="same", score=5.0
            ),
            TokenUsage(run_id=1, model="m", provider="google", cost_usd=0.2),
            TokenUsage(run_id=2, model="m", provider="google", cost_usd=0.3),
        ]
    )
    session.commit()
    return user


def test_compare_reports_scores_diffs_and_regression(session):
    user = _seed(session)

    result = asyncio.run(
        compare_runs(run_a=1, run_b=2, session=session, user=user, _=user)
    )

    assert result["metrics"]["score_delta"] == -1.0
    assert result["metrics"]["cost_delta"] == pytest.approx(0.1)
    assert result["regression"]["regressed"] is True
    assert result["regression"]["threshold"] == 0.5
    assert result["same_dataset"] is True

    first, second = result["rows"]
    assert first["status"] == "regressed"
    assert first["score_delta"] == -1.0
    assert "-apple" in first["response_diff"]
    assert "+orange" in first["response_diff"]
    assert second["status"] == "unchanged"
    assert second["response_diff"] == ""


def test_compare_within_threshold_and_one_sided_rows(session):
    user = _seed(session)

    run_b = session.get(Runs, 2)
    run_b.avg_score = 4.0  # delta -0.5 == threshold, not a regression
    session.add(run_b)

    usage_b = session.exec(select(TokenUsage).where(TokenUsage.run_id == 2)).first()
    usage_b.cost_usd = None
    session.add(usage_b)
    session.add(Results(run_id=2, idx=2, question="q3", response="only b", score=4.0))
    session.commit()

    result = asyncio.run(
        compare_runs(run_a=1, run_b=2, session=session, user=user, _=user)
    )

    assert result["regression"]["regressed"] is False
    assert result["metrics"]["cost_delta"] == pytest.approx(-0.2)
    assert result["run_b"]["unpriced"] is True
    assert result["rows"][2]["status"] == "only_b"
    assert result["rows"][2]["score_a"] is None


def test_compare_rejects_foreign_run(session):
    _seed(session)
    other = Users(id=2, name="o", email="o@example.com")

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            compare_runs(run_a=1, run_b=2, session=session, user=other, _=other)
        )
    assert exc.value.status_code == 403
