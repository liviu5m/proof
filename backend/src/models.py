from datetime import datetime, timezone
from sqlmodel import Field, SQLModel
from typing import Optional

class Users(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False, unique=True)
    email: str = Field(nullable=False, unique=True)
    password: Optional[str] = Field(default=None)
    provider: str = Field(default="credentials", nullable=False) 
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

class Runs(SQLModel, table=True):
    __tablename__ = "runs"
    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="datasets.id", nullable=False)
    model: str = Field(nullable=False)
    system_prompt: str = Field(nullable=False)
    judge_model: str = Field(nullable=False)
    avg_score: Optional[float] = Field(default=None)
    total: int = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    status: str = Field(default="Pending", nullable=False)

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
