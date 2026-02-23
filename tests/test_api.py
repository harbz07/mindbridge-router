import os

from fastapi.testclient import TestClient

from app.main import app
from app.models import ChatCompletionRequest, ChatMessage


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "mindbridge-router"


def test_models_endpoint_requires_valid_api_key() -> None:
    os.environ["MINDBRIDGE_API_KEY"] = "expected-key"

    no_auth = client.get("/v1/models")
    assert no_auth.status_code == 403

    invalid_auth = client.get(
        "/v1/models",
        headers={"Authorization": "Bearer wrong-key"},
    )
    assert invalid_auth.status_code == 401

    valid_auth = client.get(
        "/v1/models",
        headers={"Authorization": "Bearer expected-key"},
    )
    assert valid_auth.status_code == 200
    assert "data" in valid_auth.json()


def test_parse_model() -> None:
    request = ChatCompletionRequest(
        model="mindbridge:openai/gpt-4o-mini",
        messages=[ChatMessage(role="user", content="hello")],
    )
    provider, model = request.parse_model()
    assert provider == "openai"
    assert model == "gpt-4o-mini"
