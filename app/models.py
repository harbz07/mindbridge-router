"""
Pydantic models for OpenAI-compatible chat completion API.
"""

from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field
import time
import uuid


class FunctionDefinition(BaseModel):
    """Definition of a function that can be called by the model."""
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any]


class Tool(BaseModel):
    """A tool that can be called by the model."""
    type: Literal["function"] = "function"
    function: FunctionDefinition


class ToolCall(BaseModel):
    """A tool call made by the model."""
    id: str
    type: Literal["function"] = "function"
    function: Dict[str, str]  # {"name": "...", "arguments": "..."}


class ChatMessage(BaseModel):
    """A message in the chat conversation."""
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    """Request body for chat completion endpoint."""
    model: str = Field(
        ...,
        description="Model identifier in format 'mindbridge:provider/model', e.g., 'mindbridge:openai/gpt-4o'"
    )
    messages: List[ChatMessage]
    temperature: Optional[float] = Field(0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1)
    top_p: Optional[float] = Field(None, ge=0, le=1)
    frequency_penalty: Optional[float] = Field(None, ge=-2, le=2)
    presence_penalty: Optional[float] = Field(None, ge=-2, le=2)
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    stream: Optional[bool] = False
    reasoning_effort: Optional[Literal["low", "medium", "high"]] = None

    def parse_model(self) -> tuple[str, str]:
        """
        Parse the model string to extract provider and model name.
        
        Expected format: mindbridge:provider/model
        Example: mindbridge:openai/gpt-4o
        
        Returns:
            tuple: (provider, model_name)
        """
        if not self.model.startswith("mindbridge:"):
            raise ValueError(
                f"Model must start with 'mindbridge:'. Got: {self.model}"
            )
        
        # Remove 'mindbridge:' prefix
        rest = self.model[len("mindbridge:"):]
        
        if "/" not in rest:
            raise ValueError(
                f"Model must be in format 'mindbridge:provider/model'. Got: {self.model}"
            )
        
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
    choices: List[ChatCompletionChoice]
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
    data: List[Model]


class ErrorDetail(BaseModel):
    """Error detail information."""
    type: str
    message: str
    param: Optional[str] = None
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response body."""
    error: ErrorDetail
