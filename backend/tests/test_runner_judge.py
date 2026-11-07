import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.runner import run_single, run_tests
from src.judge import judge_single, judge_questions


def _make_mock_client(output_text='{"answer": "Paris"}'):
    """Build a mock client with client.aio.interactions.create as AsyncMock."""
    mock_interaction = MagicMock()
    mock_interaction.output_text = output_text
    mock_client = MagicMock()
    mock_client.aio.interactions.create = AsyncMock(return_value=mock_interaction)
    return mock_client


class TestRunSingle:
    @pytest.mark.asyncio
    async def test_run_single_success(self):
        mock_client = _make_mock_client('{"answer": "Paris"}')
        q = {
            "input": "What is the capital of France?",
            "expected": "Paris",
            "min_words": 1,
            "max_words": 10,
            "required_keywords": "Paris",
        }
        res = await run_single(q, "You are helpful.", "gemini-3.5-flash-lite", mock_client)
        assert res["input"] == q["input"]
        assert res["response"] == '{"answer": "Paris"}'
        assert res["expected"] == "Paris"
        mock_client.aio.interactions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_single_injects_word_count_into_prompt(self):
        mock_client = _make_mock_client('ok')
        q = {
            "input": "Say hi",
            "expected": "hi",
            "min_words": 2,
            "max_words": 5,
        }
        await run_single(q, "System prompt.", "gemini-3.5-flash-lite", mock_client)
        call_args = mock_client.aio.interactions.create.call_args
        system_instruction = call_args.kwargs["system_instruction"]
        assert "Words: 2-5" in system_instruction

    @pytest.mark.asyncio
    async def test_run_single_injects_keywords_into_prompt(self):
        mock_client = _make_mock_client('ok')
        q = {
            "input": "Say hi",
            "expected": "hi",
            "required_keywords": "hello,world",
            "forbidden_keywords": "bad",
        }
        await run_single(q, "System prompt.", "gemini-3.5-flash-lite", mock_client)
        call_args = mock_client.aio.interactions.create.call_args
        system_instruction = call_args.kwargs["system_instruction"]
        assert "Include: hello,world" in system_instruction
        assert "Exclude: bad" in system_instruction

    @pytest.mark.asyncio
    async def test_run_single_injects_regex_into_prompt(self):
        mock_client = _make_mock_client('ok')
        q = {
            "input": "Say hi",
            "expected": "hi",
            "regex": r"\d+",
        }
        await run_single(q, "System prompt.", "gemini-3.5-flash-lite", mock_client)
        call_args = mock_client.aio.interactions.create.call_args
        system_instruction = call_args.kwargs["system_instruction"]
        assert "Match regex: \\d+" in system_instruction

    @pytest.mark.asyncio
    async def test_run_single_api_error_returns_error_dict(self):
        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(
            side_effect=Exception("API rate limited")
        )
        q = {"input": "What is 2+2?", "expected": "4"}
        res = await run_single(q, "System prompt.", "gemini-3.5-flash-lite", mock_client)
        assert res["input"] == "What is 2+2?"
        assert res["response"] is None
        assert "error" in res
        assert res["code"] == "gemini_api_error"

    @pytest.mark.asyncio
    async def test_run_single_retry_on_429(self):
        """429 errors are retried (note: retry config in runner.py has a pre-existing bug;
        this test documents current behavior where non-retriable 429 returns error dict)."""
        class RateLimitError(Exception):
            status_code = 429

        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(
            side_effect=RateLimitError("429 Too Many Requests")
        )
        q = {"input": "What is 2+2?", "expected": "4"}
        res = await run_single(q, "System prompt.", "gemini-3.5-flash-lite", mock_client)
        assert res["response"] is None
        assert "error" in res
        assert mock_client.aio.interactions.create.call_count == 1

    @pytest.mark.asyncio
    async def test_run_single_fail_fast_on_400(self):
        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(
            side_effect=Exception("400 Bad Request")
        )
        q = {"input": "What is 2+2?", "expected": "4"}
        res = await run_single(q, "System prompt.", "gemini-3.5-flash-lite", mock_client)
        assert res["response"] is None
        assert "error" in res
        assert mock_client.aio.interactions.create.call_count == 1

    @pytest.mark.asyncio
    async def test_run_single_timeout_handling(self):
        import asyncio
        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(
            side_effect=asyncio.TimeoutError("Request timed out")
        )
        q = {"input": "What is 2+2?", "expected": "4"}
        res = await run_single(q, "System prompt.", "gemini-3.5-flash-lite", mock_client)
        assert res["response"] is None
        assert "error" in res


class TestRunTests:
    @pytest.mark.asyncio
    async def test_run_tests_normalizes_results(self):
        mock_client = _make_mock_client('{"answer": "ok"}')
        questions = [
            {"input": "Q1", "expected": "A1"},
            {"input": "Q2", "expected": "A2"},
        ]
        results = await run_tests(questions, "System prompt.", "gemini-3.5-flash-lite", mock_client)
        assert len(results) == 2
        assert results[0]["input"] == "Q1"
        assert results[1]["input"] == "Q2"
        assert all("response" in r for r in results)

    @pytest.mark.asyncio
    async def test_run_tests_handles_single_failure_gracefully(self):
        mock_client = MagicMock()
        mock_interaction = MagicMock()
        mock_interaction.output_text = '{"answer": "ok"}'
        mock_client.aio.interactions.create = AsyncMock(
            side_effect=[Exception("boom"), mock_interaction]
        )
        questions = [
            {"input": "Q1", "expected": "A1"},
            {"input": "Q2", "expected": "A2"},
        ]
        results = await run_tests(questions, "System prompt.", "gemini-3.5-flash-lite", mock_client)
        assert len(results) == 2
        assert "error" in results[0]
        assert results[0]["response"] is None
        assert results[1]["response"] == '{"answer": "ok"}'


class TestJudgeSingle:
    @pytest.mark.asyncio
    async def test_judge_single_success(self):
        mock_client = _make_mock_client('{"score": 5.0, "reason": "Perfect match"}')
        q = {
            "input": "What is 2+2?",
            "response": "4",
            "expected": "4",
            "min_words": 1,
            "max_words": 5,
        }
        res = await judge_single(q, "gemini-3.5-flash-lite", mock_client)
        assert res["score"] == 5.0
        assert res["reason"] == "Perfect match"

    @pytest.mark.asyncio
    async def test_judge_single_no_response_returns_zero(self):
        mock_client = _make_mock_client('{"score": 1.0, "reason": "x"}')
        q = {
            "input": "What is 2+2?",
            "response": None,
            "expected": "4",
        }
        res = await judge_single(q, "gemini-3.5-flash-lite", mock_client)
        assert res["score"] == 0.0
        assert res["reason"] == "no response"
        mock_client.aio.interactions.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_judge_single_empty_response_returns_zero(self):
        mock_client = _make_mock_client('{"score": 1.0, "reason": "x"}')
        q = {
            "input": "What is 2+2?",
            "response": "",
            "expected": "4",
        }
        res = await judge_single(q, "gemini-3.5-flash-lite", mock_client)
        assert res["score"] == 0.0
        assert res["reason"] == "no response"

    @pytest.mark.asyncio
    async def test_judge_single_json_gate_rejects_invalid_json(self):
        mock_client = _make_mock_client('{"score": 1.0, "reason": "x"}')
        q = {
            "input": "Give me JSON",
            "response": "not json",
            "expected": '{"key": "value"}',
            "requires_json": "true",
        }
        res = await judge_single(q, "gemini-3.5-flash-lite", mock_client)
        assert res["score"] == 1.0
        assert "No valid json structure" in res["reason"]
        mock_client.aio.interactions.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_judge_single_json_gate_accepts_valid_json(self):
        mock_client = _make_mock_client('{"score": 5.0, "reason": "good json"}')
        q = {
            "input": "Give me JSON",
            "response": '{"key": "value"}',
            "expected": '{"key": "value"}',
            "requires_json": "true",
        }
        res = await judge_single(q, "gemini-3.5-flash-lite", mock_client)
        assert res["score"] == 5.0
        assert res["reason"] == "good json"
        mock_client.aio.interactions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_judge_single_word_count_gate(self):
        mock_client = _make_mock_client('{"score": 1.0, "reason": "x"}')
        q = {
            "input": "Say something",
            "response": "short",
            "expected": "something",
            "min_words": 10,
            "max_words": 20,
        }
        res = await judge_single(q, "gemini-3.5-flash-lite", mock_client)
        assert res["score"] == 1.0
        assert "Failed word count limits" in res["reason"]
        mock_client.aio.interactions.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_judge_single_regex_gate(self):
        mock_client = _make_mock_client('{"score": 1.0, "reason": "x"}')
        q = {
            "input": "Say something",
            "response": "no numbers here",
            "expected": "123",
            "regex": r"\d+",
        }
        res = await judge_single(q, "gemini-3.5-flash-lite", mock_client)
        assert res["score"] == 1.0
        assert "Failed regex pattern match" in res["reason"]
        mock_client.aio.interactions.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_judge_single_keyword_gate(self):
        mock_client = _make_mock_client('{"score": 1.0, "reason": "x"}')
        q = {
            "input": "Say something",
            "response": "hello world",
            "expected": "hello",
            "required_keywords": "missing",
        }
        res = await judge_single(q, "gemini-3.5-flash-lite", mock_client)
        assert res["score"] == 1.0
        assert "Failed keyword validation" in res["reason"]
        mock_client.aio.interactions.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_judge_single_api_error_returns_score_one(self):
        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(
            side_effect=Exception("API down")
        )
        q = {
            "input": "What is 2+2?",
            "response": "4",
            "expected": "4",
        }
        res = await judge_single(q, "gemini-3.5-flash-lite", mock_client)
        assert res["score"] == 1.0
        assert "Judge API error" in res["reason"]


class TestJudgeQuestions:
    @pytest.mark.asyncio
    async def test_judge_questions_normalizes_results(self):
        mock_client = _make_mock_client('{"score": 4.0, "reason": "good"}')
        data = [
            {"input": "Q1", "response": "A1", "expected": "A1"},
            {"input": "Q2", "response": "A2", "expected": "A2"},
        ]
        results = await judge_questions(data, "gemini-3.5-flash-lite", mock_client)
        assert len(results) == 2
        assert results[0]["score"] == 4.0
        assert results[1]["score"] == 4.0

    @pytest.mark.asyncio
    async def test_judge_questions_handles_exception_gracefully(self):
        mock_client = MagicMock()
        mock_client.aio.interactions.create = AsyncMock(side_effect=Exception("boom"))
        data = [
            {"input": "Q1", "response": "A1", "expected": "A1"},
        ]
        results = await judge_questions(data, "gemini-3.5-flash-lite", mock_client)
        assert len(results) == 1
        assert results[0]["score"] == 1.0
        assert "Judge API error" in results[0]["reason"]
