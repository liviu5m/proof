import asyncio
import json

import pytest
from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine

from src.models import Datasets, ProofUserRole, Results, Runs, Users
from src.routes.runs import export_run


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
            avg_score=4.0,
        )
    )
    session.add_all(
        [
            Results(
                run_id=1,
                idx=0,
                question="q1",
                expected=None,
                response="=cmd()",
                score=4.0,
                reason='ok, "quoted"',
            ),
            Results(
                run_id=1,
                idx=1,
                question="q2",
                expected="e",
                response="line1\nline2",
                score=None,
                reason=None,
            ),
        ]
    )
    session.commit()
    return user


def test_csv_export_has_header_injection_guard_and_newlines(session):
    user = _seed(session)

    response = asyncio.run(
        export_run(run_id=1, session=session, user=user, _=user, format="csv")
    )

    body = response.body.decode()
    assert body.splitlines()[0] == "idx,question,expected,response,score,reason"
    assert "'=cmd()" in body
    assert "line1\nline2" in body
    assert response.media_type == "text/csv; charset=utf-8"
    assert "run-1-results.csv" in response.headers["content-disposition"]


def test_json_export_shape(session):
    user = _seed(session)

    response = asyncio.run(
        export_run(run_id=1, session=session, user=user, _=user, format="json")
    )

    payload = json.loads(response.body)
    assert payload["run"]["id"] == 1
    assert payload["run"]["dataset_name"] == "QA"
    assert payload["run"]["avg_score"] == 4.0
    assert [row["idx"] for row in payload["results"]] == [0, 1]
    assert payload["results"][1]["score"] is None
    assert "run-1-results.json" in response.headers["content-disposition"]


def test_export_rejects_foreign_run(session):
    _seed(session)
    other = Users(id=2, name="o", email="o@example.com")

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            export_run(run_id=1, session=session, user=other, _=other, format="csv")
        )
    assert exc.value.status_code == 403
