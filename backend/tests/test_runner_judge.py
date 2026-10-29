import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.runner import run_single, run_tests
from src.judge import judge_single, judge_questions

@pytest.mark.asyncio
async def test_run_single():
    mock_interaction = MagicMock()
    mock_interaction.output_text = '{"answer": "Paris"}'

    with patch("src.runner.client") as mock_client:
        mock_client.aio.interactions.create = AsyncMock(return_value=mock_interaction)
        
        q = {
            "input": "What is the capital of France?",
            "expected": "Paris",
            "min_words": 1,
            "max_words": 10,
            "required_keywords": "Paris",
        }
        
        res = await run_single(q, "You are helpful.", "gemini-3.5-flash-lite")
        assert res["input"] == q["input"]
        assert res["response"] == '{"answer": "Paris"}'
        assert res["expected"] == "Paris"

@pytest.mark.asyncio
async def test_judge_single():
    mock_interaction = MagicMock()
    mock_interaction.output_text = '{"score": 5.0, "reason": "Perfect match"}'

    with patch("src.judge.client") as mock_client:
        mock_client.aio.interactions.create = AsyncMock(return_value=mock_interaction)
        
        q = {
            "input": "What is 2+2?",
            "response": "4",
            "expected": "4",
            "min_words": 1,
            "max_words": 5,
        }
        
        res = await judge_single(q, "gemini-3.5-flash-lite")
        assert res["score"] == 5.0
        assert res["reason"] == "Perfect match"
