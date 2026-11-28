from unittest.mock import AsyncMock, MagicMock

import pytest

from src.judge import judge_questions


def _provider():
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
    provider.generate = AsyncMock(return_value=response)
    return provider


def _semantic(monkeypatch, score):
    async def fake(pairs):
        return [{"score": score} for _ in pairs]

    monkeypatch.setattr("src.judge.score_semantic_batch", fake)


def _broken_semantic(monkeypatch):
    async def boom(pairs):
        raise RuntimeError("embedding model unavailable")

    monkeypatch.setattr("src.judge.score_semantic_batch", boom)


DATA = [
    {"input": "q", "response": "x", "expected": "x"},
]


@pytest.mark.asyncio
async def test_blend_uses_all_three_scores(monkeypatch):
    _semantic(monkeypatch, 2.0)

    results = await judge_questions(
        DATA, "m", _provider(), {"rule": 0.3, "llm": 0.4, "semantic": 0.3}
    )

    # rule 5, llm 4, semantic 2 -> 1.5 + 1.6 + 0.6
    assert results[0]["score"] == pytest.approx(3.7)


@pytest.mark.asyncio
async def test_llm_only_weights_ignore_semantic(monkeypatch):
    _semantic(monkeypatch, 1.0)

    results = await judge_questions(
        DATA, "m", _provider(), {"rule": 0, "llm": 1, "semantic": 0}
    )

    assert results[0]["score"] == pytest.approx(4.0)


@pytest.mark.asyncio
async def test_embedding_failure_falls_back_to_rule_and_llm(monkeypatch):
    _broken_semantic(monkeypatch)

    results = await judge_questions(
        DATA, "m", _provider(), {"rule": 0.3, "llm": 0.4, "semantic": 0.3}
    )

    # semantic dropped, renormalized: (5*0.3 + 4*0.4) / 0.7
    assert results[0]["score"] == pytest.approx(4.428571, rel=1e-4)


@pytest.mark.asyncio
async def test_missing_expected_drops_semantic(monkeypatch):
    _semantic(monkeypatch, 1.0)

    results = await judge_questions(
        [{"input": "q", "response": "x", "expected": ""}],
        "m",
        _provider(),
        {"rule": 0.3, "llm": 0.4, "semantic": 0.3},
    )

    assert results[0]["score"] == pytest.approx(4.428571, rel=1e-4)


@pytest.mark.asyncio
async def test_semantic_only_weights_survive_embedding_failure(monkeypatch):
    _broken_semantic(monkeypatch)

    results = await judge_questions(
        DATA, "m", _provider(), {"rule": 0, "llm": 0, "semantic": 1}
    )

    # no zero-division: falls back to rule 0.3 / llm 0.4
    assert results[0]["score"] == pytest.approx(4.428571, rel=1e-4)


@pytest.mark.asyncio
async def test_mixed_expected_items_keep_per_item_weights(monkeypatch):
    _semantic(monkeypatch, 5.0)

    data = [
        {"input": "q1", "response": "x", "expected": "x"},
        {"input": "q2", "response": "x", "expected": ""},
    ]
    results = await judge_questions(
        data, "m", _provider(), {"rule": 0.3, "llm": 0.4, "semantic": 0.3}
    )

    # full blend for the first, rule+llm only for the second
    assert results[0]["score"] == pytest.approx(4.6)
    assert results[1]["score"] == pytest.approx(4.428571, rel=1e-4)
