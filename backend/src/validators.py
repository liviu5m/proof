import re
from typing import Optional
from pydantic import BaseModel, field_validator, model_validator


class DatasetRow(BaseModel):
    input: str
    expected: Optional[str] = None
    regex: Optional[str] = None
    min_words: Optional[int] = None
    max_words: Optional[int] = None
    required_keywords: Optional[str] = None
    forbidden_keywords: Optional[str] = None
    requires_json: Optional[bool] = None

    @field_validator("input")
    @classmethod
    def input_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("input is required and cannot be empty")
        return v

    @field_validator("regex")
    @classmethod
    def validate_regex(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                re.compile(v)
            except re.error as e:
                raise ValueError(f"invalid regex pattern: {e}")
        return v

    @field_validator("min_words")
    @classmethod
    def min_words_non_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("min_words must be >= 0")
        return v

    @field_validator("max_words")
    @classmethod
    def max_words_gte_min(cls, v: Optional[int]) -> Optional[int]:
        return v

    @model_validator(mode="after")
    def check_min_max_words(self) -> "DatasetRow":
        if self.min_words is not None and self.max_words is not None:
            if self.min_words > self.max_words:
                raise ValueError("min_words cannot be greater than max_words")
        return self

    @field_validator("requires_json", mode="before")
    @classmethod
    def parse_requires_json(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v


REQUIRED_COLUMNS = {"input"}
OPTIONAL_COLUMNS = {
    "expected", "regex", "min_words", "max_words",
    "required_keywords", "forbidden_keywords", "requires_json"
}
ALL_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS


def validate_csv_headers(headers: list[str]) -> list[str]:
    """Return list of header errors (empty if valid)."""
    headers_set = set(h.strip().lower() for h in headers)
    missing = REQUIRED_COLUMNS - headers_set
    extra = headers_set - ALL_COLUMNS
    errors = []
    if missing:
        errors.append(f"Missing required columns: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"Unknown columns: {', '.join(sorted(extra))}")
    return errors


def validate_csv_rows(rows: list[dict]) -> tuple[list[DatasetRow], list[dict]]:
    """
    Validate CSV rows (list of dicts from csv.DictReader).
    Returns (valid_rows, errors) where errors contain line numbers.
    """
    valid = []
    errors = []
    for i, row in enumerate(rows, start=2):  # line 1 = header
        # Normalize keys: strip whitespace, lowercase
        normalized = {k.strip().lower(): v for k, v in row.items()}
        try:
            valid.append(DatasetRow(**normalized))
        except Exception as e:
            errors.append({"line": i, "error": str(e)})
    return valid, errors