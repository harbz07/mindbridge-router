"""
Base provider interface for LLM providers.
"""

from abc import ABC, abstractmethod

from app.models import ChatCompletionChoice, ChatMessage


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Each provider implementation must handle the conversion between
    OpenAI-style messages and their native API format.
    """

    def __init__(self, api_key: str | None = None, **kwargs):
        """
        Initialize the provider.

        Args:
            api_key: API key for the provider
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    async def get_completion(
        self, messages: list[ChatMessage], model: str, temperature: float = 0.7, max_tokens: int | None = None, **kwargs
    ) -> ChatCompletionChoice:
        """
        Get a completion from the provider.

        Args:
            messages: List of conversation messages
            model: Model identifier (without provider prefix)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            ChatCompletionChoice with the model's response
        """
        pass

    @abstractmethod
    def get_available_models(self) -> list[str]:
        """
        Get a list of available models for this provider.

        Returns:
            List of model identifiers
        """
        pass

    def is_valid_model(self, model: str) -> bool:
        """
        Check if a model is valid for this provider.

        Args:
            model: Model identifier

        Returns:
            True if the model is valid, False otherwise
        """
        return model in self.get_available_models()
