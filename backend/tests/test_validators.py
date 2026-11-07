import pytest
from pydantic import ValidationError
from src.validators import (
    DatasetRow,
    validate_csv_headers,
    validate_csv_rows,
    REQUIRED_COLUMNS,
    OPTIONAL_COLUMNS,
    ALL_COLUMNS,
)


class TestDatasetRowModel:
    def test_valid_row(self):
        row = DatasetRow(input="What is 2+2?", expected="4")
        assert row.input == "What is 2+2?"
        assert row.expected == "4"

    def test_input_required(self):
        with pytest.raises(ValidationError):
            DatasetRow(input="")

    def test_input_whitespace_only(self):
        with pytest.raises(ValidationError):
            DatasetRow(input="   \t\n  ")

    def test_input_none(self):
        with pytest.raises(ValidationError):
            DatasetRow(input=None)

    def test_regex_valid(self):
        row = DatasetRow(input="Order 456", regex=r"\d+")
        assert row.regex == r"\d+"

    def test_regex_invalid(self):
        with pytest.raises(ValidationError):
            DatasetRow(input="test", regex="[invalid")

    def test_regex_none_allowed(self):
        row = DatasetRow(input="test", regex=None)
        assert row.regex is None

    def test_min_words_non_negative(self):
        with pytest.raises(ValidationError):
            DatasetRow(input="test", min_words=-1)

    def test_min_words_zero_allowed(self):
        row = DatasetRow(input="test", min_words=0)
        assert row.min_words == 0

    def test_min_words_greater_than_max(self):
        with pytest.raises(ValidationError):
            DatasetRow(input="test", min_words=10, max_words=5)

    def test_min_words_equals_max(self):
        row = DatasetRow(input="test", min_words=5, max_words=5)
        assert row.min_words == 5
        assert row.max_words == 5

    def test_requires_json_string_true(self):
        row = DatasetRow(input="test", requires_json="true")
        assert row.requires_json is True

    def test_requires_json_string_1(self):
        row = DatasetRow(input="test", requires_json="1")
        assert row.requires_json is True

    def test_requires_json_string_yes(self):
        row = DatasetRow(input="test", requires_json="yes")
        assert row.requires_json is True

    def test_requires_json_string_false(self):
        row = DatasetRow(input="test", requires_json="false")
        assert row.requires_json is False

    def test_requires_json_bool(self):
        row = DatasetRow(input="test", requires_json=True)
        assert row.requires_json is True

    def test_all_optional_fields(self):
        row = DatasetRow(
            input="Q",
            expected="A",
            regex=r"\d+",
            min_words=1,
            max_words=10,
            required_keywords="paris",
            forbidden_keywords="london",
            requires_json=True,
        )
        assert row.input == "Q"
        assert row.expected == "A"
        assert row.regex == r"\d+"
        assert row.min_words == 1
        assert row.max_words == 10
        assert row.required_keywords == "paris"
        assert row.forbidden_keywords == "london"
        assert row.requires_json is True


class TestValidateCsvHeaders:
    def test_valid_headers_only_input(self):
        errors = validate_csv_headers(["input"])
        assert errors == []

    def test_valid_headers_all_columns(self):
        headers = ["input", "expected", "regex", "min_words", "max_words",
                   "required_keywords", "forbidden_keywords", "requires_json"]
        errors = validate_csv_headers(headers)
        assert errors == []

    def test_missing_required_input(self):
        errors = validate_csv_headers(["expected", "regex"])
        assert any("Missing required columns" in e for e in errors)
        assert any("input" in e for e in errors)

    def test_unknown_columns(self):
        errors = validate_csv_headers(["input", "unknown_col", "another_bad"])
        assert any("Unknown columns" in e for e in errors)

    def test_headers_case_insensitive(self):
        errors = validate_csv_headers(["INPUT", "Expected"])
        assert errors == []

    def test_headers_with_whitespace(self):
        errors = validate_csv_headers(["  input  ", "  expected  "])
        assert errors == []

    def test_empty_headers(self):
        errors = validate_csv_headers([])
        assert any("Missing required columns" in e for e in errors)


class TestValidateCsvRows:
    def test_valid_rows(self):
        rows = [
            {"input": "What is 2+2?", "expected": "4"},
            {"input": "Capital of France?", "expected": "Paris", "min_words": "1", "max_words": "5"},
        ]
        valid, errors = validate_csv_rows(rows)
        assert len(valid) == 2
        assert len(errors) == 0
        assert valid[0].input == "What is 2+2?"
        assert valid[0].expected == "4"

    def test_row_with_missing_input_reports_line_number(self):
        rows = [
            {"input": "Q1", "expected": "A1"},
            {"expected": "A2"},
            {"input": "Q3", "expected": "A3"},
        ]
        valid, errors = validate_csv_rows(rows)
        assert len(valid) == 2
        assert len(errors) == 1
        assert errors[0]["line"] == 3
        assert ("input is required" in errors[0]["error"]
                or "Field required" in errors[0]["error"]
                or "type=missing" in errors[0]["error"])

    def test_row_with_invalid_regex_reports_line_number(self):
        rows = [
            {"input": "Q1", "regex": "[invalid"},
        ]
        valid, errors = validate_csv_rows(rows)
        assert len(valid) == 0
        assert len(errors) == 1
        assert errors[0]["line"] == 2
        assert "invalid regex" in errors[0]["error"]

    def test_row_with_min_words_gt_max_words(self):
        rows = [
            {"input": "Q1", "min_words": "10", "max_words": "5"},
        ]
        valid, errors = validate_csv_rows(rows)
        assert len(valid) == 0
        assert len(errors) == 1
        assert "min_words cannot be greater" in errors[0]["error"]

    def test_requires_json_parsing_from_csv_strings(self):
        rows = [
            {"input": "Q1", "requires_json": "true"},
            {"input": "Q2", "requires_json": "false"},
            {"input": "Q3", "requires_json": "yes"},
            {"input": "Q4", "requires_json": "no"},
        ]
        valid, errors = validate_csv_rows(rows)
        assert len(valid) == 4
        assert valid[0].requires_json is True
        assert valid[1].requires_json is False
        assert valid[2].requires_json is True
        assert valid[3].requires_json is False

    def test_empty_rows_list(self):
        valid, errors = validate_csv_rows([])
        assert valid == []
        assert errors == []

    def test_mixed_valid_and_invalid_rows(self):
        rows = [
            {"input": "Good row"},
            {},
            {"input": "Another good", "expected": "ok"},
            {"input": "", "expected": "bad"},
        ]
        valid, errors = validate_csv_rows(rows)
        assert len(valid) == 2
        assert len(errors) == 2
        error_lines = {e["line"] for e in errors}
        assert error_lines == {3, 5}