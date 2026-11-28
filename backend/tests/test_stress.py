import asyncio
import csv
import io
import json
from unittest.mock import MagicMock

import pytest
from sqlmodel import Session, SQLModel, create_engine

from src.judge import MAX_CONCURRENCY, judge_questions
from src.models import (
    Datasets,
    ProofUserRole,
    Results,
    Runs,
    TokenUsage,
    Users,
)
from src.routes.prompts import (
    PromptRegistryCreate,
    PromptVersionCreate,
    compare_prompt_versions,
    create_prompt_registry,
    create_prompt_version,
    delete_prompt_version,
    get_prompt_registry,
)
from src.routes.runs import compare_runs, export_run, get_usage


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
        SQLModel.metadata.drop_all(engine)


def _user(session, user_id=1):
    user = Users(
        id=user_id, name="u", email=f"u{user_id}@example.com", role=ProofUserRole.MEMBER
    )
    session.add(user)
    session.commit()
    return user


def _provider(counter=None, delay=0.001):
    response = MagicMock()
    response.text = '{"score": 4, "reason": "ok"}'
    response.input_tokens = 1
    response.output_tokens = 1
    response.cost_usd = None
    response.cached_tokens = 0
    response.reasoning_tokens = 0
    response.latency_s = 0.0
    response.attempts = 1
    response.usage_estimated = False
    response.error = None

    provider = MagicMock()

    async def generate(**kwargs):
        if counter is not None:
            counter["current"] += 1
            counter["max"] = max(counter["max"], counter["current"])
            await asyncio.sleep(delay)
            counter["current"] -= 1
        return response

    provider.generate = generate
    return provider


@pytest.mark.asyncio
async def test_judge_200_rows_respects_concurrency_cap(monkeypatch):
    async def fake_semantic(pairs):
        return [{"score": 5.0} for _ in pairs]

    monkeypatch.setattr("src.judge.score_semantic_batch", fake_semantic)

    counter = {"current": 0, "max": 0}
    data = [
        {"input": f"q{idx}", "response": f"a{idx}", "expected": f"a{idx}"}
        for idx in range(200)
    ]

    results = await judge_questions(
        data, "m", _provider(counter), {"rule": 0.3, "llm": 0.4, "semantic": 0.3}
    )

    assert len(results) == 200
    assert all(res["score"] == pytest.approx(4.6) for res in results)
    assert counter["max"] <= MAX_CONCURRENCY
    assert counter["max"] > 1


def test_prompt_registry_40_versions_stay_ordered(session):
    user = _user(session)
    registry = asyncio.run(
        create_prompt_registry(
            PromptRegistryCreate(name="stress", initial_content="v1"),
            session,
            user,
            user,
            None,
        )
    )
    registry_id = registry["id"]

    versions = []
    for idx in range(2, 41):
        versions.append(
            asyncio.run(
                create_prompt_version(
                    registry_id,
                    PromptVersionCreate(content=f"v{idx}"),
                    session,
                    user,
                    user,
                    None,
                )
            )
        )

    detail = asyncio.run(get_prompt_registry(registry_id, session, user, user))
    assert detail.version_count == 40
    assert sorted(v.version_number for v in detail.versions) == list(range(1, 41))

    # delete every other version, numbering must stay unique and dense from source
    for version in versions[::2]:
        asyncio.run(
            delete_prompt_version(registry_id, version.id, session, user, user, None)
        )

    detail = asyncio.run(get_prompt_registry(registry_id, session, user, user))
    assert detail.version_count == 20
    assert all(v.version_number >= 1 for v in detail.versions)

    comparison = asyncio.run(
        compare_prompt_versions(
            registry_id,
            detail.versions[-1].id,
            detail.versions[0].id,
            session,
            user,
            user,
        )
    )
    assert "v1" in comparison.diff or "v40" in comparison.diff


def _seed_run(session, run_id, dataset_id, user_id):
    session.add(
        Runs(
            id=run_id,
            dataset_id=dataset_id,
            model="m",
            system_prompt="p",
            judge_model="j",
            total=1000,
            avg_score=4.0,
        )
    )
    session.add(
        TokenUsage(
            run_id=run_id,
            model="m",
            provider="google",
            prompt_tokens=10,
            completion_tokens=5,
            cost_usd=0.01,
        )
    )


def test_export_1000_rows_roundtrip(session):
    user = _user(session)
    session.add(
        Datasets(
            id=1, name="QA", source_path="1/a.csv", item_count=1000, hash="h", user_id=1
        )
    )
    _seed_run(session, 1, 1, 1)
    session.add_all(
        [
            Results(
                run_id=1,
                idx=idx,
                question=f"question {idx}, with comma",
                expected=f"expected {idx}",
                response=f'answer {idx} "quoted"\nsecond line',
                score=float(idx % 5 + 1),
                reason="reason",
            )
            for idx in range(1000)
        ]
    )
    session.commit()

    csv_response = asyncio.run(
        export_run(run_id=1, session=session, user=user, _=user, format="csv")
    )
    rows = list(csv.reader(io.StringIO(csv_response.body.decode())))
    assert len(rows) == 1001
    assert rows[0][0] == "idx"
    assert rows[1000][2] == "expected 999"

    json_response = asyncio.run(
        export_run(run_id=1, session=session, user=user, _=user, format="json")
    )
    payload = json.loads(json_response.body)
    assert len(payload["results"]) == 1000
    assert payload["results"][999]["idx"] == 999


def test_usage_aggregates_many_runs_across_datasets(session):
    user = _user(session)
    for dataset_id in range(1, 4):
        session.add(
            Datasets(
                id=dataset_id,
                name=f"dataset {dataset_id}",
                source_path=f"{dataset_id}/a.csv",
                item_count=10,
                hash="h",
                user_id=1,
            )
        )
    run_id = 1
    for dataset_id in range(1, 4):
        for _ in range(10):
            _seed_run(session, run_id, dataset_id, 1)
            run_id += 1
    session.commit()

    usage = asyncio.run(get_usage(session=session, user=user, _=user, days=30))

    assert usage["totals"]["runs"] == 30
    assert usage["totals"]["prompt_tokens"] == 300
    assert usage["totals"]["completion_tokens"] == 150
    assert usage["totals"]["cost_usd"] == pytest.approx(0.3)
    assert len(usage["datasets"]) == 3
    assert all(entry["runs"] == 10 for entry in usage["datasets"])


def test_compare_union_of_450_rows(session):
    user = _user(session)
    session.add(
        Datasets(
            id=1, name="QA", source_path="1/a.csv", item_count=450, hash="h", user_id=1
        )
    )
    _seed_run(session, 1, 1, 1)
    _seed_run(session, 2, 1, 1)
    session.add_all(
        [
            Results(
                run_id=1,
                idx=idx,
                question=f"q{idx}",
                expected="e",
                response=f"a{idx}",
                score=4.0,
            )
            for idx in range(300)
        ]
    )
    session.add_all(
        [
            Results(
                run_id=2,
                idx=idx,
                question=f"q{idx}",
                expected="e",
                response=f"b{idx}",
                score=3.0 if idx < 300 else 4.0,
            )
            for idx in range(150, 450)
        ]
    )
    run_b = session.get(Runs, 2)
    run_b.avg_score = 3.0
    session.add(run_b)
    session.commit()

    result = asyncio.run(
        compare_runs(run_a=1, run_b=2, session=session, user=user, _=user)
    )

    assert len(result["rows"]) == 450
    statuses = [row["status"] for row in result["rows"]]
    assert statuses.count("only_a") == 150
    assert statuses.count("only_b") == 150
    assert statuses.count("regressed") == 150
    assert result["regression"]["regressed"] is True
