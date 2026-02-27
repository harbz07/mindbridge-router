import pytest
from app.models import ChatCompletionRequest, ChatMessage


def test_parse_model_valid():
    request = ChatCompletionRequest(
        model="mindbridge:openai/gpt-4o",
        messages=[ChatMessage(role="user", content="hello")],
    )
    provider, model = request.parse_model()
    assert provider == "openai"
    assert model == "gpt-4o"


def test_parse_model_nested_path():
    request = ChatCompletionRequest(
        model="mindbridge:google/gemini-1.5-pro",
        messages=[ChatMessage(role="user", content="hello")],
    )
    provider, model = request.parse_model()
    assert provider == "google"
    assert model == "gemini-1.5-pro"


def test_parse_model_missing_prefix():
    request = ChatCompletionRequest(
        model="openai/gpt-4o",
        messages=[ChatMessage(role="user", content="hello")],
    )
    with pytest.raises(ValueError, match="must start with 'mindbridge:'"):
        request.parse_model()


def test_parse_model_missing_slash():
    request = ChatCompletionRequest(
        model="mindbridge:openai",
        messages=[ChatMessage(role="user", content="hello")],
    )
    with pytest.raises(ValueError, match="must be in format"):
        request.parse_model()


def test_chat_completion_request_defaults():
    request = ChatCompletionRequest(
        model="mindbridge:openai/gpt-4o",
        messages=[ChatMessage(role="user", content="test")],
    )
    assert request.temperature == 0.7
    assert request.max_tokens is None
    assert request.stream is False
