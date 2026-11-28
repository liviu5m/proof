import pytest
from fastapi import HTTPException

from src.utils import validate_scorer_weights


def test_none_means_system_defaults():
    assert validate_scorer_weights(None) is None


def test_valid_weights_are_coerced_to_floats():
    assert validate_scorer_weights({"rule": "0.5", "llm": 0.25, "semantic": 0.25}) == {
        "rule": 0.5,
        "llm": 0.25,
        "semantic": 0.25,
    }


@pytest.mark.parametrize(
    "weights",
    [
        {"rule": 0, "llm": 0, "semantic": 0},
        {"rule": 1.5, "llm": 0, "semantic": 0},
        {"rule": -0.1, "llm": 0.6, "semantic": 0.5},
        {"rule": 0.5, "llm": 0.5},
        {"rule": "x", "llm": 0.5, "semantic": 0.5},
    ],
)
def test_invalid_weights_are_rejected(weights):
    with pytest.raises(HTTPException) as exc:
        validate_scorer_weights(weights)
    assert exc.value.status_code == 400
