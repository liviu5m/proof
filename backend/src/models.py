from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from sqlmodel import NUMERIC, Column, Field, SQLModel, Text


class ProofUserRole(StrEnum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Users(SQLModel, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    email: str = Field(nullable=False, unique=True)
    password: str | None = Field(default=None)
    provider: str = Field(default="credentials", nullable=False)
    role: ProofUserRole = Field(default=ProofUserRole.MEMBER, nullable=False)
    verified: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), nullable=False
    )


class Datasets(SQLModel, table=True):
    __tablename__ = "datasets"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    source_path: str = Field(nullable=False)
    item_count: int = Field(nullable=False, default=0)
    hash: str = Field(nullable=False)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(UTC), nullable=False
    )
    deleted_at: datetime | None = Field(default=None)


class Runs(SQLModel, table=True):
    __tablename__ = "runs"
    id: int | None = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="datasets.id", nullable=False)
    model: str = Field(nullable=False)
    provider: str = Field(default="google", nullable=False)
    provider_judge: str = Field(default="google", nullable=False)
    system_prompt: str = Field(nullable=False)
    judge_model: str = Field(nullable=False)
    avg_score: float | None = Field(default=None)
    total: int = Field(nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), nullable=False
    )
    status: str = Field(default="Pending", nullable=False)
    deleted_at: datetime | None = Field(default=None)


class Results(SQLModel, table=True):
    __tablename__ = "results"
    id: int | None = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="runs.id", nullable=False)
    idx: int = Field(nullable=False)
    question: str = Field(nullable=False)
    expected: str | None = Field(default=None)
    response: str | None = Field(default=None)
    score: float | None = Field(default=None)
    reason: str | None = Field(default=None)
    deleted_at: datetime | None = Field(default=None)


class RefreshTokens(SQLModel, table=True):
    __tablename__ = "refresh_tokens"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    token_hash: str = Field(nullable=False, unique=True)
    expires_at: datetime = Field(nullable=False)
    revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EmailVerifications(SQLModel, table=True):
    __tablename__ = "email_verifications"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    token_hash: str = Field(nullable=False, unique=True)
    expires_at: datetime = Field(nullable=False)
    used: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PasswordResetTokens(SQLModel, table=True):
    __tablename__ = "password_reset_token"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    token_hash: str = Field(nullable=False, unique=True)
    expires_at: datetime = Field(nullable=False)
    used: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProviderCredential(SQLModel, table=True):
    __tablename__ = "provider_credentials"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    provider: str = Field(nullable=False)  # "google", "openai", "anthropic", "ollama"
    encrypted_api_key: str = Field(nullable=False)
    base_url: str | None = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), nullable=False
    )


class ModelCatalog(SQLModel, table=True):
    __tablename__ = "model_catalog"
    id: int | None = Field(default=None, primary_key=True)
    provider: str = Field(nullable=False)  # "google", "openai", "anthropic", "ollama"
    model_id: str = Field(nullable=False)  # "gpt-4o", "claude-3-5-sonnet", etc.
    name: str = Field(nullable=False)  # Display name
    supports_json_mode: bool = Field(default=False)
    supports_system_prompt: bool = Field(default=True)
    input_cost_per_1m: Decimal | None = Field(
            default=None, sa_column=Column(NUMERIC(12, 6), nullable=True)
        )
    output_cost_per_1m: Decimal | None = Field(
        default=None, sa_column=Column(NUMERIC(12, 6), nullable=True)
    )
    max_tokens: int | None = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), nullable=False
    )

class TokenUsage(SQLModel, table=True):
    __tablename__ = "token_usage"
    id: int | None = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="runs.id", nullable=False)
    model: str = Field(nullable=False)
    provider: str = Field(nullable=False)
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    cost_usd: Decimal | None = Field(
        default=None, sa_column=Column(NUMERIC(12, 6), nullable=True)
    )
    input_cost_per_1m: Decimal | None = Field(
        default=None, sa_column=Column(NUMERIC(12, 6), nullable=True)
    )
    output_cost_per_1m: Decimal | None = Field(
        default=None, sa_column=Column(NUMERIC(12, 6), nullable=True)
    )
    cached_tokens: int = Field(default=0)
    reasoning_tokens: int = Field(default=0)
    total_latency_s: float = Field(default=0.0)
    total_attempts: int = Field(default=0)
    usage_estimated: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), nullable=False
    )


class PromptRegistry(SQLModel, table=True):
    __tablename__ = "prompt_registries"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(nullable=False, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), nullable=False
    )
    deleted_at: datetime | None = Field(default=None)


class PromptVersion(SQLModel, table=True):
    __tablename__ = "prompt_versions"

    id: int | None = Field(default=None, primary_key=True)
    registry_id: int = Field(foreign_key="prompt_registries.id", nullable=False)
    content_hash: str = Field(nullable=False, max_length=64)  # sha256 hex of content
    content: str = Field(sa_column=Column(Text))
    description: str | None = Field(default=None, max_length=500)
    is_current: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), nullable=False
    )
    deleted_at: datetime | None = Field(default=None)
