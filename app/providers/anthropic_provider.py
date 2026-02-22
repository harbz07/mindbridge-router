"""
Anthropic provider implementation.
"""

from typing import List, Optional
from anthropic import AsyncAnthropic
from app.models import ChatMessage, ChatCompletionChoice
from app.providers.base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """Provider for Anthropic Claude models."""
    
    AVAILABLE_MODELS = [
        # Claude 4 models (latest)
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-sonnet-4-5",
        "claude-opus-4-5",
        # Claude 3.5 models
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-20240620",
        "claude-3-5-haiku-20241022",
        # Claude 3 models
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ]
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.client = AsyncAnthropic(api_key=api_key)
    
    async def get_completion(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatCompletionChoice:
        """Get completion from Anthropic."""
        
        # Anthropic requires separating system messages
        system_message = None
        conversation_messages = []
        
        for msg in messages:
            if msg.role == "system":
                # Combine multiple system messages if present
                if system_message:
                    system_message += f"\n\n{msg.content}"
                else:
                    system_message = msg.content
            else:
                conversation_messages.append({
                    "role": msg.role,
                    "content": msg.content or ""
                })
        
        # Build request parameters
        request_params = {
            "model": model,
            "messages": conversation_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 1024,  # Anthropic requires max_tokens
        }
        
        if system_message:
            request_params["system"] = system_message
        
        # Add optional parameters
        if "top_p" in kwargs and kwargs["top_p"] is not None:
            request_params["top_p"] = kwargs["top_p"]
        
        try:
            response = await self.client.messages.create(**request_params)
            
            # Extract text content from response
            content = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text
            
            return ChatCompletionChoice(
                index=0,
                message=ChatMessage(
                    role="assistant",
                    content=content
                ),
                finish_reason=response.stop_reason or "stop"
            )
        
        except Exception as e:
            return ChatCompletionChoice(
                index=0,
                message=ChatMessage(
                    role="assistant",
                    content=f"Error calling Anthropic: {str(e)}"
                ),
                finish_reason="error"
            )
    
    def get_available_models(self) -> List[str]:
        """Get list of available Anthropic models."""
        return self.AVAILABLE_MODELS
