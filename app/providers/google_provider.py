"""
Google Gemini provider implementation.
"""

from typing import List, Optional
import google.generativeai as genai
from app.models import ChatMessage, ChatCompletionChoice
from app.providers.base import BaseLLMProvider


class GoogleProvider(BaseLLMProvider):
    """Provider for Google Gemini models."""
    
    AVAILABLE_MODELS = [
        # Gemini 3.x models (preview)
        "gemini-3-flash-preview",
        "gemini-3.1-pro-preview",
        "gemini-3.1-flash-lite-preview",
        # Gemini 2.5 models (stable, recommended)
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.5-pro",
        # Gemini 2.0 models (retiring June 2026)
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
    ]
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        genai.configure(api_key=api_key)
    
    async def get_completion(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatCompletionChoice:
        """Get completion from Google Gemini."""
        
        system_instruction = None
        conversation_history = []
        
        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            elif msg.role == "user":
                conversation_history.append({
                    "role": "user",
                    "parts": [msg.content or ""]
                })
            elif msg.role == "assistant":
                conversation_history.append({
                    "role": "model",
                    "parts": [msg.content or ""]
                })
        
        try:
            generation_config = {
                "temperature": temperature,
            }
            
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens
            
            if "top_p" in kwargs and kwargs["top_p"] is not None:
                generation_config["top_p"] = kwargs["top_p"]
            
            if "top_k" in kwargs and kwargs["top_k"] is not None:
                generation_config["top_k"] = kwargs["top_k"]
            
            model_instance = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
                system_instruction=system_instruction
            )
            
            chat = model_instance.start_chat(history=conversation_history[:-1] if len(conversation_history) > 1 else [])
            
            last_message = conversation_history[-1]["parts"][0] if conversation_history else ""
            response = await chat.send_message_async(last_message)
            
            return ChatCompletionChoice(
                index=0,
                message=ChatMessage(
                    role="assistant",
                    content=response.text
                ),
                finish_reason="stop"
            )
        
        except Exception as e:
            return ChatCompletionChoice(
                index=0,
                message=ChatMessage(
                    role="assistant",
                    content=f"Error calling Google Gemini: {str(e)}"
                ),
                finish_reason="error"
            )
    
    def get_available_models(self) -> List[str]:
        """Get list of available Google models."""
        return self.AVAILABLE_MODELS
