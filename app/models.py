"""
Pydantic models for OpenAI-compatible chat completion API.
"""

import time
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


class FunctionDefinition(BaseModel):
    """Definition of a function that can be called by the model."""

    name: str
    description: str | None = None
    parameters: dict[str, Any]


class Tool(BaseModel):
    """A tool that can be called by the model."""

    type: Literal["function"] = "function"
    function: FunctionDefinition


class ToolCall(BaseModel):
    """A tool call made by the model."""

    id: str
    type: Literal["function"] = "function"
    function: dict[str, str]  # {"name": "...", "arguments": "..."}


class ChatMessage(BaseModel):
    """A message in the chat conversation."""

    role: Literal["system", "user", "assistant", "tool"]
    content: str | None = None
    name: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None


class ChatCompletionRequest(BaseModel):
    """Request body for chat completion endpoint."""

    model: str = Field(
        ..., description="Model identifier in format 'mindbridge:provider/model', e.g., 'mindbridge:openai/gpt-4o'"
    )
    messages: list[ChatMessage]
    temperature: float | None = Field(0.7, ge=0, le=2)
    max_tokens: int | None = Field(None, ge=1)
    top_p: float | None = Field(None, ge=0, le=1)
    frequency_penalty: float | None = Field(None, ge=-2, le=2)
    presence_penalty: float | None = Field(None, ge=-2, le=2)
    tools: list[Tool] | None = None
    tool_choice: str | dict[str, Any] | None = None
    stream: bool | None = False
    reasoning_effort: Literal["low", "medium", "high"] | None = None

    def parse_model(self) -> tuple[str, str]:
        """
        Parse the model string to extract provider and model name.

        Expected format: mindbridge:provider/model
        Example: mindbridge:openai/gpt-4o

        Returns:
            tuple: (provider, model_name)
        """
        if not self.model.startswith("mindbridge:"):
            raise ValueError(f"Model must start with 'mindbridge:'. Got: {self.model}")

        # Remove 'mindbridge:' prefix
        rest = self.model[len("mindbridge:") :]

        if "/" not in rest:
            raise ValueError(f"Model must be in format 'mindbridge:provider/model'. Got: {self.model}")

        provider, model_name = rest.split("/", 1)
        return provider.lower(), model_name


class ChatCompletionChoice(BaseModel):
    """A choice in the chat completion response."""

    index: int
    message: ChatMessage
    finish_reason: Literal["stop", "length", "tool_calls", "content_filter", "error"]


class Usage(BaseModel):
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """Response body for chat completion endpoint."""

    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:24]}")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: list[ChatCompletionChoice]
    usage: Usage


class Model(BaseModel):
    """Information about an available model."""

    id: str
    object: Literal["model"] = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "mindbridge"


class ModelList(BaseModel):
    """List of available models."""

    object: Literal["list"] = "list"
    data: list[Model]


class ErrorDetail(BaseModel):
    """Error detail information."""

    type: str
    message: str
    param: str | None = None
    code: str | None = None


class ErrorResponse(BaseModel):
    """Error response body."""

    error: ErrorDetail
