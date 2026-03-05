"""
Provider factory for creating and managing LLM providers.
"""

from typing import Dict, Optional
import os
from app.providers.base import BaseLLMProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.google_provider import GoogleProvider


class ProviderFactory:
    """
    Factory for creating and managing LLM provider instances.
    """
    
    def __init__(self):
        """Initialize the provider factory."""
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """Initialize all configured providers based on environment variables."""
        
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self._providers["openai"] = OpenAIProvider(api_key=openai_key)
        
        # Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self._providers["anthropic"] = AnthropicProvider(api_key=anthropic_key)
        
        # Google
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key:
            self._providers["google"] = GoogleProvider(api_key=google_key)
        
        # TODO: Add more providers as needed
        # - DeepSeek
        # - OpenRouter
        # - Ollama
        # - OpenAI-compatible
    
    def get_provider(self, provider_name: str) -> Optional[BaseLLMProvider]:
        """
        Get a provider by name.
        
        Args:
            provider_name: Name of the provider (e.g., "openai", "anthropic")
            
        Returns:
            Provider instance or None if not found
        """
        return self._providers.get(provider_name.lower())
    
    def has_provider(self, provider_name: str) -> bool:
        """
        Check if a provider is configured.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            True if the provider is configured, False otherwise
        """
        return provider_name.lower() in self._providers
    
    def get_available_providers(self) -> list[str]:
        """
        Get a list of all configured provider names.
        
        Returns:
            List of provider names
        """
        return list(self._providers.keys())
    
    def get_all_models(self) -> Dict[str, list[str]]:
        """
        Get all available models grouped by provider.
        
        Returns:
            Dictionary mapping provider names to lists of model identifiers
        """
        return {
            provider_name: provider.get_available_models()
            for provider_name, provider in self._providers.items()
        }


# Global instance
provider_factory = ProviderFactory()
