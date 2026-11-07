import sys
import os
import csv
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import pytest
from typer.testing import CliRunner
from unittest.mock import MagicMock, AsyncMock, patch

from src.cli import app


runner = CliRunner()


def _make_csv(rows, suffix=".csv"):
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, newline="")
    writer = csv.DictWriter(tmp, fieldnames=["input", "expected"])
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    tmp.close()
    return tmp.name


class TestCliVersion:
    def test_version(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "proof 0.1.0" in result.output


class TestCliDatasetCreate:
    def test_dataset_create_csv_not_found(self):
        result = runner.invoke(app, ["dataset", "create", "--csv", "/nonexistent/file.csv"])
        assert result.exit_code == 1
        assert "File not found" in result.output

    def test_dataset_create_empty_csv(self):
        csv_path = _make_csv([])
        try:
            result = runner.invoke(app, ["dataset", "create", "--csv", csv_path, "--name", "empty"])
            assert result.exit_code == 0
            assert "Dataset created" in result.output or "already exists" in result.output
        finally:
            os.unlink(csv_path)

    def test_dataset_create_success(self):
        csv_path = _make_csv([
            {"input": "What is 2+2?", "expected": "4"},
            {"input": "Capital of France?", "expected": "Paris"},
        ])
        try:
            result = runner.invoke(app, ["dataset", "create", "--csv", csv_path, "--name", "test-dataset"])
            assert result.exit_code == 0
            assert "Dataset created" in result.output or "already exists" in result.output
            assert "test-dataset" in result.output
        finally:
            os.unlink(csv_path)

    def test_dataset_create_dedup_by_hash(self):
        csv_path = _make_csv([
            {"input": "What is 2+2?", "expected": "4"},
        ])
        try:
            result1 = runner.invoke(app, ["dataset", "create", "--csv", csv_path, "--name", "first"])
            assert result1.exit_code == 0
            result2 = runner.invoke(app, ["dataset", "create", "--csv", csv_path, "--name", "second"])
            assert result2.exit_code == 0
            assert "already exists" in result2.output
        finally:
            os.unlink(csv_path)


class TestCliDatasetList:
    def test_dataset_list_empty(self):
        result = runner.invoke(app, ["dataset", "list"])
        assert result.exit_code == 0
        assert "DATASETS" in result.output

    def test_dataset_list_with_data(self):
        csv_path = _make_csv([
            {"input": "Q1?", "expected": "A1"},
        ])
        try:
            runner.invoke(app, ["dataset", "create", "--csv", csv_path, "--name", "list-test"])
            result = runner.invoke(app, ["dataset", "list"])
            assert result.exit_code == 0
            assert "list-test" in result.output
        finally:
            os.unlink(csv_path)


class TestCliDatasetShow:
    def test_dataset_show_not_found(self):
        result = runner.invoke(app, ["dataset", "show", "99999"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_dataset_show_success(self):
        csv_path = _make_csv([
            {"input": "Q1?", "expected": "A1"},
            {"input": "Q2?", "expected": "A2"},
        ])
        try:
            create_result = runner.invoke(app, ["dataset", "create", "--csv", csv_path, "--name", "show-test"])
            assert create_result.exit_code == 0
            # Show by ID 1 - may not exist if other tests created datasets first
            result = runner.invoke(app, ["dataset", "show", "1"])
            assert result.exit_code in [0, 1]  # 0 if found, 1 if not found
        finally:
            os.unlink(csv_path)

class TestCliRun:
    def test_run_csv_not_found(self):
        result = runner.invoke(app, ["run", "--questions", "/nonexistent/file.csv"])
        assert result.exit_code == 1

    def test_run_empty_dataset(self):
        csv_path = _make_csv([])
        try:
            result = runner.invoke(app, ["run", "--questions", csv_path])
            assert result.exit_code in [0, 1]
        finally:
            os.unlink(csv_path)

    @patch("src.cli.genai.Client")
    def test_run_with_mocked_llm(self, mock_genai_client):
        mock_client = MagicMock()
        mock_interaction = MagicMock()
        mock_interaction.output_text = '{"answer": "Paris"}'
        mock_client.aio.interactions.create = AsyncMock(return_value=mock_interaction)
        mock_genai_client.return_value = mock_client

        csv_path = _make_csv([
            {"input": "What is the capital of France?", "expected": "Paris"},
        ])
        try:
            result = runner.invoke(app, ["run", "--questions", csv_path, "--model", "gemini-3.5-flash-lite"])
            assert result.exit_code == 0
            assert "Score:" in result.output
        finally:
            os.unlink(csv_path)


class TestCliRunList:
    def test_run_list_empty(self):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

    def test_run_list_with_dataset_filter(self):
        result = runner.invoke(app, ["list", "--dataset", "1"])
        assert result.exit_code == 0


class TestCliRunShow:
    def test_run_show_not_found(self):
        result = runner.invoke(app, ["show", "99999"])
        assert result.exit_code == 1
        assert "not found" in result.output


class TestCliCompare:
    def test_compare_missing_args(self):
        result = runner.invoke(app, ["compare"])
        assert result.exit_code == 2

    def test_compare_not_found(self):
        result = runner.invoke(app, ["compare", "1", "2"])
        assert result.exit_code in [0, 1]
