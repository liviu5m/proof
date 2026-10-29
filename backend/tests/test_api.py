import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == "Hello World"

def test_auth_register_and_login():
    # Register with missing fields
    response = client.post("/api/auth/register", json={"email": "bad"})
    assert response.status_code in [400, 422]

    # Login with missing fields
    response = client.post("/api/auth/login", json={"email": "test@example.com", "password": "wrong"})
    assert response.status_code in [400, 401, 422]

    # Logout endpoint
    response = client.post("/api/auth/logout")
    assert response.status_code == 200

def test_user_jwt_unauthorized():
    response = client.get("/api/user/jwt")
    assert response.status_code in [401, 403]

def test_dataset_unauthorized():
    response = client.get("/api/dataset/")
    assert response.status_code in [401, 403]

def test_runs_unauthorized():
    response = client.get("/api/runs/")
    assert response.status_code in [401, 403]
