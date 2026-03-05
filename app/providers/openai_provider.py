"""
OpenAI provider implementation.
"""

from openai import AsyncOpenAI

from app.models import ChatCompletionChoice, ChatMessage
from app.providers.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """Provider for OpenAI models."""

    AVAILABLE_MODELS = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
        "o1",
        "o1-mini",
        "o1-preview",
    ]

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.client = AsyncOpenAI(api_key=api_key)

    async def get_completion(
        self, messages: list[ChatMessage], model: str, temperature: float = 0.7, max_tokens: int | None = None, **kwargs
    ) -> ChatCompletionChoice:
        """Get completion from OpenAI."""

        # Convert our ChatMessage objects to OpenAI format
        openai_messages = [
            {
                "role": msg.role,
                "content": msg.content,
                **({"name": msg.name} if msg.name else {}),
                **({"tool_calls": msg.tool_calls} if msg.tool_calls else {}),
                **({"tool_call_id": msg.tool_call_id} if msg.tool_call_id else {}),
            }
            for msg in messages
        ]

        # Build request parameters
        request_params = {
            "model": model,
            "messages": openai_messages,
            "temperature": temperature,
        }

        if max_tokens:
            request_params["max_tokens"] = max_tokens

        # Add optional parameters
        for key in ["top_p", "frequency_penalty", "presence_penalty", "tools", "tool_choice"]:
            if key in kwargs and kwargs[key] is not None:
                request_params[key] = kwargs[key]

        # Special handling for reasoning models (o1, o1-mini, o1-preview)
        if model.startswith("o1"):
            # o1 models don't support temperature or system messages
            request_params.pop("temperature", None)
            # Add reasoning_effort if provided
            if "reasoning_effort" in kwargs and kwargs["reasoning_effort"]:
                request_params["reasoning_effort"] = kwargs["reasoning_effort"]

        try:
            response = await self.client.chat.completions.create(**request_params)

            # Convert OpenAI response to our format
            choice = response.choices[0]

            return ChatCompletionChoice(
                index=0,
                message=ChatMessage(
                    role=choice.message.role,
                    content=choice.message.content,
                    tool_calls=choice.message.tool_calls if hasattr(choice.message, "tool_calls") else None,
                ),
                finish_reason=choice.finish_reason or "stop",
            )

        except Exception as e:
            # Return error as a choice
            return ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content=f"Error calling OpenAI: {str(e)}"),
                finish_reason="error",
            )

    def get_available_models(self) -> list[str]:
        """Get list of available OpenAI models."""
        return self.AVAILABLE_MODELS
