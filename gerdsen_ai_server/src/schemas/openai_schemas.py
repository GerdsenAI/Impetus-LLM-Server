"""
Pydantic schemas for OpenAI-compatible API endpoints
"""

import time
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field, validator


class ChatMessage(BaseModel):
    """Chat message schema"""
    role: Literal["system", "user", "assistant"] = Field(..., description="The role of the message author")
    content: str = Field(..., min_length=1, max_length=100000, description="The content of the message")
    name: str | None = Field(None, min_length=1, max_length=64, description="An optional name for the participant")

    @validator('content')
    def validate_content(self, v):
        if not v.strip():
            raise ValueError("Message content cannot be empty or only whitespace")
        return v.strip()


class ChatCompletionRequest(BaseModel):
    """Chat completion request schema"""
    model: str = Field(..., min_length=1, max_length=255, description="ID of the model to use")
    messages: list[ChatMessage] = Field(..., min_items=1, max_items=100, description="List of messages")
    temperature: float | None = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int | None = Field(2048, ge=1, le=8192, description="Maximum number of tokens to generate")
    top_p: float | None = Field(1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    top_k: int | None = Field(50, ge=1, le=100, description="Top-k sampling parameter")
    stream: bool | None = Field(False, description="Whether to stream partial message deltas")
    stop: str | list[str] | None = Field(None, description="Sequences where the API will stop generating")
    presence_penalty: float | None = Field(0.0, ge=-2.0, le=2.0, description="Presence penalty")
    frequency_penalty: float | None = Field(0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    logit_bias: dict[str, float] | None = Field(None, description="Modify likelihood of specified tokens")
    user: str | None = Field(None, max_length=255, description="Unique identifier for the end-user")
    n: int | None = Field(1, ge=1, le=5, description="Number of completions to generate")

    # Impetus-specific extensions
    conversation_id: str | None = Field(None, description="Conversation ID for KV cache")
    use_cache: bool | None = Field(True, description="Whether to use KV cache")
    repetition_penalty: float | None = Field(1.0, ge=0.1, le=2.0, description="Repetition penalty")

    # RAG extensions
    use_rag: bool | None = Field(False, description="Enable automatic RAG context retrieval")
    rag_collection: str | None = Field(None, description="Collection to search for RAG context")
    rag_n_results: int | None = Field(5, ge=1, le=20, description="Number of RAG context documents")
    context_documents: list[str] | None = Field(None, description="Pre-retrieved context documents")

    @validator('model')
    def validate_model(self, v):
        if not v.strip():
            raise ValueError("Model ID cannot be empty")
        return v.strip()

    @validator('messages')
    def validate_messages(self, v):
        if not v:
            raise ValueError("Messages list cannot be empty")

        # Check for alternating user/assistant pattern (best practice)
        roles = [msg.role for msg in v]
        if roles[0] not in ['system', 'user']:
            raise ValueError("First message must be from 'system' or 'user'")

        return v

    @validator('stop')
    def validate_stop(self, v):
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
    prompt: str | list[str] = Field(..., description="The prompt(s) to generate completions for")
    max_tokens: int | None = Field(16, ge=1, le=8192, description="Maximum number of tokens to generate")
    temperature: float | None = Field(1.0, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float | None = Field(1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    n: int | None = Field(1, ge=1, le=5, description="Number of completions to generate")
    stream: bool | None = Field(False, description="Whether to stream partial completions")
    logprobs: int | None = Field(None, ge=0, le=5, description="Include log probabilities")
    echo: bool | None = Field(False, description="Echo back the prompt in addition to completion")
    stop: str | list[str] | None = Field(None, description="Sequences where the API will stop generating")
    presence_penalty: float | None = Field(0.0, ge=-2.0, le=2.0, description="Presence penalty")
    frequency_penalty: float | None = Field(0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    best_of: int | None = Field(1, ge=1, le=20, description="Number of completions to generate server-side")
    logit_bias: dict[str, float] | None = Field(None, description="Modify likelihood of specified tokens")
    user: str | None = Field(None, max_length=255, description="Unique identifier for the end-user")

    @validator('prompt')
    def validate_prompt(self, v):
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
    permission: list[dict[str, Any]] = Field(default_factory=list, description="Model permissions")
    root: str = Field(..., description="Root model identifier")
    parent: str | None = Field(None, description="Parent model identifier")


class ModelListResponse(BaseModel):
    """Model list response schema"""
    object: Literal["list"] = Field("list", description="Object type")
    data: list[ModelInfo] = Field(..., description="List of models")


class Usage(BaseModel):
    """Token usage schema"""
    prompt_tokens: int = Field(..., ge=0, description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., ge=0, description="Number of tokens in the completion")
    total_tokens: int = Field(..., ge=0, description="Total number of tokens")


class ChatCompletionChoice(BaseModel):
    """Chat completion choice schema"""
    index: int = Field(..., ge=0, description="Choice index")
    message: ChatMessage = Field(..., description="The generated message")
    finish_reason: Literal["stop", "length", "content_filter"] | None = Field(None, description="Reason for finishing")


class CompletionChoice(BaseModel):
    """Completion choice schema"""
    text: str = Field(..., description="The generated text")
    index: int = Field(..., ge=0, description="Choice index")
    logprobs: dict[str, Any] | None = Field(None, description="Log probabilities")
    finish_reason: Literal["stop", "length", "content_filter"] | None = Field(None, description="Reason for finishing")


class ChatCompletionResponse(BaseModel):
    """Chat completion response schema"""
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:8]}", description="Unique identifier")
    object: Literal["chat.completion"] = Field("chat.completion", description="Object type")
    created: int = Field(default_factory=lambda: int(time.time()), description="Unix timestamp")
    model: str = Field(..., description="Model used for completion")
    choices: list[ChatCompletionChoice] = Field(..., description="List of completion choices")
    usage: Usage | None = Field(None, description="Token usage statistics")

    # Impetus-specific extensions
    conversation_id: str | None = Field(None, description="Conversation ID used")
    performance_metrics: dict[str, Any] | None = Field(None, description="Performance metrics")


class CompletionResponse(BaseModel):
    """Completion response schema"""
    id: str = Field(default_factory=lambda: f"cmpl-{uuid.uuid4().hex[:8]}", description="Unique identifier")
    object: Literal["text_completion"] = Field("text_completion", description="Object type")
    created: int = Field(default_factory=lambda: int(time.time()), description="Unix timestamp")
    model: str = Field(..., description="Model used for completion")
    choices: list[CompletionChoice] = Field(..., description="List of completion choices")
    usage: Usage | None = Field(None, description="Token usage statistics")


class ChatCompletionStreamDelta(BaseModel):
    """Streaming chat completion delta schema"""
    role: str | None = Field(None, description="Message role")
    content: str | None = Field(None, description="Partial message content")


class ChatCompletionStreamChoice(BaseModel):
    """Streaming chat completion choice schema"""
    index: int = Field(..., ge=0, description="Choice index")
    delta: ChatCompletionStreamDelta = Field(..., description="Partial message delta")
    finish_reason: Literal["stop", "length", "content_filter"] | None = Field(None, description="Reason for finishing")


class ChatCompletionStreamResponse(BaseModel):
    """Streaming chat completion response schema"""
    id: str = Field(..., description="Unique identifier")
    object: Literal["chat.completion.chunk"] = Field("chat.completion.chunk", description="Object type")
    created: int = Field(..., description="Unix timestamp")
    model: str = Field(..., description="Model used for completion")
    choices: list[ChatCompletionStreamChoice] = Field(..., description="List of completion choices")


# ── Embedding schemas ──────────────────────────────────────────────


class EmbeddingRequest(BaseModel):
    """OpenAI-compatible embedding request"""
    input: str | list[str] = Field(..., description="Text(s) to embed")
    model: str = Field(default="all-MiniLM-L6-v2", description="Embedding model name")
    encoding_format: Literal["float", "base64"] = Field(default="float", description="Output encoding format")
    dimensions: int | None = Field(None, ge=1, description="Optional dimension truncation")


class EmbeddingData(BaseModel):
    """Single embedding object"""
    object: Literal["embedding"] = Field("embedding")
    embedding: list[float] = Field(..., description="The embedding vector")
    index: int = Field(..., ge=0, description="Index of the input text")


class EmbeddingUsage(BaseModel):
    """Token usage for embedding request"""
    prompt_tokens: int = Field(..., ge=0)
    total_tokens: int = Field(..., ge=0)


class EmbeddingResponse(BaseModel):
    """OpenAI-compatible embedding response"""
    object: Literal["list"] = Field("list")
    data: list[EmbeddingData] = Field(..., description="List of embeddings")
    model: str = Field(..., description="Model used")
    usage: EmbeddingUsage = Field(..., description="Token usage")


# ── Error schema ───────────────────────────────────────────────────


# ── Document / RAG schemas ─────────────────────────────────────────


class DocumentIngestRequest(BaseModel):
    """Request to ingest a text document into the vector store."""
    text: str = Field(..., min_length=1, max_length=500000, description="Text to ingest")
    source: str = Field(default="unknown", max_length=512, description="Source identifier (e.g. filename)")
    collection: str | None = Field(None, max_length=128, description="Target collection name")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata for all chunks")
    chunk_size: int | None = Field(None, ge=64, le=8192, description="Override default chunk size")
    chunk_overlap: int | None = Field(None, ge=0, le=1024, description="Override default chunk overlap")


class DocumentIngestResponse(BaseModel):
    """Response from document ingestion."""
    status: str = Field(..., description="Ingestion status")
    chunks_stored: int = Field(..., ge=0, description="Number of chunks stored")
    collection: str = Field(..., description="Collection name")
    source: str = Field(..., description="Source identifier")
    document_ids: list[str] = Field(default_factory=list, description="Stored chunk IDs")


class DocumentSearchRequest(BaseModel):
    """Request to search the vector store."""
    query: str = Field(..., min_length=1, max_length=10000, description="Search query")
    n_results: int = Field(5, ge=1, le=50, description="Number of results to return")
    collection: str | None = Field(None, max_length=128, description="Collection to search")
    where: dict[str, Any] | None = Field(None, description="Optional metadata filter")


class DocumentSearchResponse(BaseModel):
    """Response from document search."""
    documents: list[str] = Field(default_factory=list, description="Matched document texts")
    metadatas: list[dict[str, Any]] = Field(default_factory=list, description="Document metadata")
    distances: list[float] = Field(default_factory=list, description="Similarity distances")
    count: int = Field(..., ge=0, description="Number of results")
    query: str = Field(..., description="Original query")


class CollectionInfoResponse(BaseModel):
    """Information about a vector store collection."""
    name: str = Field(..., description="Collection name")
    count: int = Field(..., ge=0, description="Document count")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Collection metadata")


# ── Error schema ───────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: dict[str, Any] = Field(..., description="Error details")

    @classmethod
    def from_exception(cls, message: str, error_type: str = "invalid_request_error", code: str | None = None):
        """Create error response from exception"""
        error_data = {
            "message": message,
            "type": error_type,
            "param": None,
            "code": code
        }
        return cls(error=error_data)
