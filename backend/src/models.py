from enum import Enum
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel
from typing import Optional


class ProofUserRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class Users(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    email: str = Field(nullable=False, unique=True)
    password: Optional[str] = Field(default=None)
    provider: str = Field(default="credentials", nullable=False)
    role: ProofUserRole = Field(default=ProofUserRole.MEMBER, nullable=False)
    verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

class Datasets(SQLModel, table=True):
    __tablename__ = "datasets"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    source_path: str = Field(nullable=False)
    item_count: int = Field(nullable=False, default=0)
    hash: str = Field(nullable=False)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at: Optional[datetime] = Field(default=None)

class Runs(SQLModel, table=True):
    __tablename__ = "runs"
    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="datasets.id", nullable=False)
    model: str = Field(nullable=False)
    provider: str = Field(default="google", nullable=False)
    provider_judge: str = Field(default="google", nullable=False)
    system_prompt: str = Field(nullable=False)
    judge_model: str = Field(nullable=False)
    avg_score: Optional[float] = Field(default=None)
    total: int = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    status: str = Field(default="Pending", nullable=False)
    deleted_at: Optional[datetime] = Field(default=None)

class Results(SQLModel, table=True):
    __tablename__ = "results"
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="runs.id", nullable=False)
    idx: int = Field(nullable=False)
    question: str = Field(nullable=False)
    expected: Optional[str] = Field(default=None)
    response: Optional[str] = Field(default=None)
    score: Optional[float] = Field(default=None)
    reason: Optional[str] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)


class RefreshTokens(SQLModel, table=True):
    __tablename__ = "refresh_tokens"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    token_hash: str = Field(nullable=False, unique=True)
    expires_at: datetime = Field(nullable=False)
    revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EmailVerifications(SQLModel, table=True):
    __tablename__ = "email_verifications"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    token_hash: str = Field(nullable=False, unique=True)
    expires_at: datetime = Field(nullable=False)
    used: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PasswordResetTokens(SQLModel, table=True):
    __tablename__ = "password_reset_token"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    token_hash: str = Field(nullable=False, unique=True)
    expires_at: datetime = Field(nullable=False)
    used: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProviderCredential(SQLModel, table=True):
    __tablename__ = "provider_credentials"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    provider: str = Field(nullable=False)  # "google", "openai", "anthropic", "ollama"
    encrypted_api_key: str = Field(nullable=False)
    base_url: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

class ModelCatalog(SQLModel, table=True):
    __tablename__ = "model_catalog"
    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str = Field(nullable=False)  # "google", "openai", "anthropic", "ollama"
    model_id: str = Field(nullable=False)  # "gpt-4o", "claude-3-5-sonnet", etc.
    name: str = Field(nullable=False)      # Display name
    supports_json_mode: bool = Field(default=False)
    supports_system_prompt: bool = Field(default=True)
    max_tokens: Optional[int] = Field(default=None)
    cost_per_1k_tokens: Optional[float] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
