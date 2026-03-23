"""
DeepSeek provider implementation.

DeepSeek's API is OpenAI-compatible, so we use the openai client
pointed at api.deepseek.com. The deepseek-reasoner model returns
an additional `reasoning_content` field alongside `content`.
"""

from typing import List, Optional
from openai import AsyncOpenAI
from app.models import ChatMessage, ChatCompletionChoice
from app.providers.base import BaseLLMProvider


class DeepSeekProvider(BaseLLMProvider):
    """Provider for DeepSeek models."""

    AVAILABLE_MODELS = [
        "deepseek-chat",
        "deepseek-reasoner",
    ]

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )

    async def get_completion(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatCompletionChoice:
        """Get completion from DeepSeek."""

        openai_messages = [
            {
                "role": msg.role,
                "content": msg.content,
                **({"name": msg.name} if msg.name else {}),
            }
            for msg in messages
        ]

        request_params = {
            "model": model,
            "messages": openai_messages,
        }

        # deepseek-reasoner does not support temperature
        if model != "deepseek-reasoner":
            request_params["temperature"] = temperature

        if max_tokens:
            request_params["max_tokens"] = max_tokens

        for key in ["top_p", "frequency_penalty", "presence_penalty"]:
            if key in kwargs and kwargs[key] is not None:
                request_params[key] = kwargs[key]

        try:
            response = await self.client.chat.completions.create(**request_params)
            choice = response.choices[0]

            content = choice.message.content or ""

            # deepseek-reasoner returns reasoning_content in the message
            # We capture it and prepend it as a reasoning trace
            reasoning_content = getattr(choice.message, "reasoning_content", None)
            if reasoning_content:
                # Attach reasoning as metadata in the content for downstream consumers
                content = (
                    f"<reasoning>\n{reasoning_content}\n</reasoning>\n\n"
                    f"{content}"
                )

            return ChatCompletionChoice(
                index=0,
                message=ChatMessage(
                    role=choice.message.role,
                    content=content,
                ),
                finish_reason=choice.finish_reason or "stop",
            )

        except Exception as e:
            return ChatCompletionChoice(
                index=0,
                message=ChatMessage(
                    role="assistant",
                    content=f"Error calling DeepSeek: {str(e)}",
                ),
                finish_reason="error",
            )

    def get_available_models(self) -> List[str]:
        """Get list of available DeepSeek models."""
        return self.AVAILABLE_MODELS
