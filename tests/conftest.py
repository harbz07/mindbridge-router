import os
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("MINDBRIDGE_API_KEY", "test-key-for-ci")


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {os.environ['MINDBRIDGE_API_KEY']}"}
