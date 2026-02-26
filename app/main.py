"""
MindBridge Router - FastAPI application for OpenAI-compatible LLM routing.
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid

from app.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    Usage,
    ModelList,
    Model,
    ErrorResponse,
    ErrorDetail,
)
from app.auth import verify_api_key
from app.providers import provider_factory
from app.memory import conversation_memory

# Initialize FastAPI app
app = FastAPI(
    title="MindBridge Router",
    description="OpenAI-compatible API for routing requests to multiple LLM providers",
    version="1.0.0",
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def verify_soulos_key(x_soulos_key: Optional[str] = Header(None)) -> str:
    """Verify the SoulOS key header for actions gateway endpoints."""
    if not x_soulos_key:
        raise HTTPException(status_code=401, detail="Missing X-SoulOS-Key header")
    return x_soulos_key


class HandshakeRequest(BaseModel):
    user_id: str
    agent_id: str
    app_id: str
    persona: str
    capabilities: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MemorySearchRequest(BaseModel):
    user_id: str
    app_id: str
    query: str
    limit: int = 5


class MemoryAddRequest(BaseModel):
    user_id: str
    app_id: str
    agent_id: str
    persona: str
    content: str
    promote: bool = False
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom exception handler for HTTPException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "invalid_request_error",
                "message": exc.detail,
            }
        }
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "MindBridge Router",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "mindbridge-router",
        "version": "1.0.0",
        "providers": provider_factory.get_available_providers(),
    }


@app.get("/v1/models", response_model=ModelList)
async def list_models(api_key: str = Depends(verify_api_key)):
    """
    List all available models across all configured providers.
    
    Returns models in OpenAI-compatible format with the naming convention:
    mindbridge:provider/model
    """
    models = []
    all_provider_models = provider_factory.get_all_models()
    
    for provider_name, model_list in all_provider_models.items():
        for model_name in model_list:
            models.append(
                Model(
                    id=f"mindbridge:{provider_name}/{model_name}",
                    owned_by=provider_name,
                )
            )
    
    return ModelList(data=models)


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    Create a chat completion using the specified model.
    
    This endpoint is OpenAI-compatible and accepts the same request format
    as the OpenAI Chat Completions API.
    """
    
    # Parse the model string to extract provider and model name
    try:
        provider_name, model_name = request.parse_model()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Get the provider
    provider = provider_factory.get_provider(provider_name)
    if not provider:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider_name}' is not configured. Available providers: {provider_factory.get_available_providers()}"
        )
    
    # Validate the model
    if not provider.is_valid_model(model_name):
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model_name}' is not available for provider '{provider_name}'. Available models: {provider.get_available_models()}"
        )
    
    # Get completion from provider
    try:
        choice = await provider.get_completion(
            messages=request.messages,
            model=model_name,
            temperature=request.temperature or 0.7,
            max_tokens=request.max_tokens,
            tools=request.tools,
            tool_choice=request.tool_choice,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            reasoning_effort=request.reasoning_effort,
        )
        
        # Store conversation in memory (optional, for future context)
        # We could generate a conversation_id from request metadata
        # For now, we'll skip this to keep it simple
        
        # Estimate token usage (rough approximation)
        # In production, you'd want to use tiktoken or similar
        prompt_text = " ".join([msg.content or "" for msg in request.messages])
        completion_text = choice.message.content or ""
        
        prompt_tokens = len(prompt_text.split()) * 1.3  # Rough estimate
        completion_tokens = len(completion_text.split()) * 1.3
        
        usage = Usage(
            prompt_tokens=int(prompt_tokens),
            completion_tokens=int(completion_tokens),
            total_tokens=int(prompt_tokens + completion_tokens),
        )
        
        # Build response
        response = ChatCompletionResponse(
            model=request.model,
            choices=[choice],
            usage=usage,
        )
        
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating completion: {str(e)}"
        )


@app.get("/providers")
async def list_providers(api_key: str = Depends(verify_api_key)):
    """
    List all configured providers and their available models.
    
    This is a debug/admin endpoint.
    """
    return {
        "providers": provider_factory.get_all_models()
    }


@app.post("/agents/handshake", status_code=201)
async def agents_handshake(
    request: HandshakeRequest,
    key: str = Depends(verify_soulos_key),
):
    """Negotiate session profile + confirm governance rules."""
    handshake_id = f"hsk_{uuid.uuid4().hex[:12]}"
    return {
        "handshake_id": handshake_id,
        "session_ttl_seconds": 3600,
        "governance": {
            "read_layers": ["client-redid", "multi-agent-shared"],
            "write_layers": [request.app_id],
            "shared_write_forbidden": True,
        },
    }


@app.post("/memory/search")
async def memory_search(
    request: MemorySearchRequest,
    key: str = Depends(verify_soulos_key),
):
    """Search memories in a lane (private or shared)."""
    return {"results": []}


@app.post("/memory/add", status_code=201)
async def memory_add(
    request: MemoryAddRequest,
    key: str = Depends(verify_soulos_key),
):
    """Add memory to a lane (write allowed only to private lane)."""
    if request.app_id == "multi-agent-shared":
        raise HTTPException(
            status_code=403,
            detail="Gateway rejects direct shared writes.",
        )

    memory_id = f"mem_{uuid.uuid4().hex[:12]}"
    return {"memory_id": memory_id}


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
