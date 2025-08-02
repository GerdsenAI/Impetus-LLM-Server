"""
Pydantic schemas for OpenAI-compatible API endpoints
"""

from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, validator
import uuid
import time


class ChatMessage(BaseModel):
    """Chat message schema"""
    role: Literal["system", "user", "assistant"] = Field(..., description="The role of the message author")
    content: str = Field(..., min_length=1, max_length=100000, description="The content of the message")
    name: Optional[str] = Field(None, min_length=1, max_length=64, description="An optional name for the participant")
    
    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError("Message content cannot be empty or only whitespace")
        return v.strip()


class ChatCompletionRequest(BaseModel):
    """Chat completion request schema"""
    model: str = Field(..., min_length=1, max_length=255, description="ID of the model to use")
    messages: List[ChatMessage] = Field(..., min_items=1, max_items=100, description="List of messages")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(2048, ge=1, le=8192, description="Maximum number of tokens to generate")
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    top_k: Optional[int] = Field(50, ge=1, le=100, description="Top-k sampling parameter")
    stream: Optional[bool] = Field(False, description="Whether to stream partial message deltas")
    stop: Optional[Union[str, List[str]]] = Field(None, description="Sequences where the API will stop generating")
    presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="Presence penalty")
    frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    logit_bias: Optional[Dict[str, float]] = Field(None, description="Modify likelihood of specified tokens")
    user: Optional[str] = Field(None, max_length=255, description="Unique identifier for the end-user")
    n: Optional[int] = Field(1, ge=1, le=5, description="Number of completions to generate")
    
    # Impetus-specific extensions
    conversation_id: Optional[str] = Field(None, description="Conversation ID for KV cache")
    use_cache: Optional[bool] = Field(True, description="Whether to use KV cache")
    repetition_penalty: Optional[float] = Field(1.0, ge=0.1, le=2.0, description="Repetition penalty")
    
    @validator('model')
    def validate_model(cls, v):
        if not v.strip():
            raise ValueError("Model ID cannot be empty")
        return v.strip()
    
    @validator('messages')
    def validate_messages(cls, v):
        if not v:
            raise ValueError("Messages list cannot be empty")
        
        # Check for alternating user/assistant pattern (best practice)
        roles = [msg.role for msg in v]
        if roles[0] not in ['system', 'user']:
            raise ValueError("First message must be from 'system' or 'user'")
        
        return v
    
    @validator('stop')
    def validate_stop(cls, v):
        if isinstance(v, str):
            return [v]
        elif isinstance(v, list):
            if len(v) > 4:
                raise ValueError("Stop sequences list cannot have more than 4 items")
            for item in v:
                if not isinstance(item, str) or len(item) > 100:
                    raise ValueError("Stop sequences must be strings with max length 100")
        return v


class CompletionRequest(BaseModel):
    """Text completion request schema"""
    model: str = Field(..., min_length=1, max_length=255, description="ID of the model to use")
    prompt: Union[str, List[str]] = Field(..., description="The prompt(s) to generate completions for")
    max_tokens: Optional[int] = Field(16, ge=1, le=8192, description="Maximum number of tokens to generate")
    temperature: Optional[float] = Field(1.0, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    n: Optional[int] = Field(1, ge=1, le=5, description="Number of completions to generate")
    stream: Optional[bool] = Field(False, description="Whether to stream partial completions")
    logprobs: Optional[int] = Field(None, ge=0, le=5, description="Include log probabilities")
    echo: Optional[bool] = Field(False, description="Echo back the prompt in addition to completion")
    stop: Optional[Union[str, List[str]]] = Field(None, description="Sequences where the API will stop generating")
    presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="Presence penalty")
    frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    best_of: Optional[int] = Field(1, ge=1, le=20, description="Number of completions to generate server-side")
    logit_bias: Optional[Dict[str, float]] = Field(None, description="Modify likelihood of specified tokens")
    user: Optional[str] = Field(None, max_length=255, description="Unique identifier for the end-user")
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if isinstance(v, str):
            if not v.strip():
                raise ValueError("Prompt cannot be empty")
            if len(v) > 50000:
                raise ValueError("Prompt too long (max 50,000 characters)")
            return v.strip()
        elif isinstance(v, list):
            if len(v) > 20:
                raise ValueError("Cannot process more than 20 prompts at once")
            validated_prompts = []
            for prompt in v:
                if not isinstance(prompt, str) or not prompt.strip():
                    raise ValueError("All prompts must be non-empty strings")
                if len(prompt) > 50000:
                    raise ValueError("Prompt too long (max 50,000 characters)")
                validated_prompts.append(prompt.strip())
            return validated_prompts
        else:
            raise ValueError("Prompt must be a string or list of strings")


class ModelInfo(BaseModel):
    """Model information schema"""
    id: str = Field(..., description="Model identifier")
    object: Literal["model"] = Field("model", description="Object type")
    created: int = Field(..., description="Unix timestamp")
    owned_by: str = Field(..., description="Organization that owns the model")
    permission: List[Dict[str, Any]] = Field(default_factory=list, description="Model permissions")
    root: str = Field(..., description="Root model identifier")
    parent: Optional[str] = Field(None, description="Parent model identifier")


class ModelListResponse(BaseModel):
    """Model list response schema"""
    object: Literal["list"] = Field("list", description="Object type")
    data: List[ModelInfo] = Field(..., description="List of models")


class Usage(BaseModel):
    """Token usage schema"""
    prompt_tokens: int = Field(..., ge=0, description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., ge=0, description="Number of tokens in the completion")
    total_tokens: int = Field(..., ge=0, description="Total number of tokens")


class ChatCompletionChoice(BaseModel):
    """Chat completion choice schema"""
    index: int = Field(..., ge=0, description="Choice index")
    message: ChatMessage = Field(..., description="The generated message")
    finish_reason: Optional[Literal["stop", "length", "content_filter"]] = Field(None, description="Reason for finishing")


class CompletionChoice(BaseModel):
    """Completion choice schema"""
    text: str = Field(..., description="The generated text")
    index: int = Field(..., ge=0, description="Choice index")
    logprobs: Optional[Dict[str, Any]] = Field(None, description="Log probabilities")
    finish_reason: Optional[Literal["stop", "length", "content_filter"]] = Field(None, description="Reason for finishing")


class ChatCompletionResponse(BaseModel):
    """Chat completion response schema"""
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:8]}", description="Unique identifier")
    object: Literal["chat.completion"] = Field("chat.completion", description="Object type")
    created: int = Field(default_factory=lambda: int(time.time()), description="Unix timestamp")
    model: str = Field(..., description="Model used for completion")
    choices: List[ChatCompletionChoice] = Field(..., description="List of completion choices")
    usage: Optional[Usage] = Field(None, description="Token usage statistics")
    
    # Impetus-specific extensions
    conversation_id: Optional[str] = Field(None, description="Conversation ID used")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")


class CompletionResponse(BaseModel):
    """Completion response schema"""
    id: str = Field(default_factory=lambda: f"cmpl-{uuid.uuid4().hex[:8]}", description="Unique identifier")
    object: Literal["text_completion"] = Field("text_completion", description="Object type")
    created: int = Field(default_factory=lambda: int(time.time()), description="Unix timestamp")
    model: str = Field(..., description="Model used for completion")
    choices: List[CompletionChoice] = Field(..., description="List of completion choices")
    usage: Optional[Usage] = Field(None, description="Token usage statistics")


class ChatCompletionStreamDelta(BaseModel):
    """Streaming chat completion delta schema"""
    role: Optional[str] = Field(None, description="Message role")
    content: Optional[str] = Field(None, description="Partial message content")


class ChatCompletionStreamChoice(BaseModel):
    """Streaming chat completion choice schema"""
    index: int = Field(..., ge=0, description="Choice index")
    delta: ChatCompletionStreamDelta = Field(..., description="Partial message delta")
    finish_reason: Optional[Literal["stop", "length", "content_filter"]] = Field(None, description="Reason for finishing")


class ChatCompletionStreamResponse(BaseModel):
    """Streaming chat completion response schema"""
    id: str = Field(..., description="Unique identifier")
    object: Literal["chat.completion.chunk"] = Field("chat.completion.chunk", description="Object type")
    created: int = Field(..., description="Unix timestamp")
    model: str = Field(..., description="Model used for completion")
    choices: List[ChatCompletionStreamChoice] = Field(..., description="List of completion choices")


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: Dict[str, Any] = Field(..., description="Error details")
    
    @classmethod
    def from_exception(cls, message: str, error_type: str = "invalid_request_error", code: Optional[str] = None):
        """Create error response from exception"""
        error_data = {
            "message": message,
            "type": error_type,
            "param": None,
            "code": code
        }
        return cls(error=error_data)