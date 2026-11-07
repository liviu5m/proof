import os
import sys
from unittest.mock import AsyncMock, MagicMock

from src.deps import get_llm_client

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from src.db import get_session, engine as _engine, _get_engine
from src.main import app

TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})


def override_get_session():
    with Session(test_engine) as session:
        yield session


app.dependency_overrides[get_session] = override_get_session

def override_get_llm_client():
    mock_client = MagicMock()
    mock_interaction = MagicMock()
    mock_interaction.output_text = '{"answer": "test"}'
    mock_client.aio.interactions.create = AsyncMock(return_value=mock_interaction)
    return mock_client


app.dependency_overrides[get_llm_client] = override_get_llm_client

@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    SQLModel.metadata.create_all(test_engine)
    yield
    # Cleanup: remove the test database file
    import os as _os
    if _os.path.exists("test.db"):
        _os.remove("test.db")


@pytest.fixture
def client():
    return TestClient(app)
