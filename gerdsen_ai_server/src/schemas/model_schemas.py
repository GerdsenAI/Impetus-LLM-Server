"""
Pydantic schemas for model management endpoints
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime


class ModelDownloadRequest(BaseModel):
    """Model download request schema"""
    model_id: str = Field(..., min_length=1, max_length=255, description="HuggingFace model identifier")
    auto_load: Optional[bool] = Field(True, description="Automatically load model after download")
    force_download: Optional[bool] = Field(False, description="Force re-download if model exists")
    
    @validator('model_id')
    def validate_model_id(cls, v):
        if not v.strip():
            raise ValueError("Model ID cannot be empty")
        
        # Basic validation for HuggingFace model ID format
        parts = v.strip().split('/')
        if len(parts) != 2:
            raise ValueError("Model ID must be in format 'organization/model-name'")
        
        organization, model_name = parts
        if not organization or not model_name:
            raise ValueError("Both organization and model name must be non-empty")
        
        # Check for valid characters
        import re
        if not re.match(r'^[a-zA-Z0-9_.-]+$', organization) or not re.match(r'^[a-zA-Z0-9_.-]+$', model_name):
            raise ValueError("Model ID contains invalid characters")
        
        return v.strip()


class ModelLoadRequest(BaseModel):
    """Model load request schema"""
    model_id: str = Field(..., min_length=1, max_length=255, description="Model identifier to load")
    force_reload: Optional[bool] = Field(False, description="Force reload if already loaded")
    
    @validator('model_id')
    def validate_model_id(cls, v):
        if not v.strip():
            raise ValueError("Model ID cannot be empty")
        return v.strip()


class ModelUnloadRequest(BaseModel):
    """Model unload request schema"""
    model_id: str = Field(..., min_length=1, max_length=255, description="Model identifier to unload")
    force: Optional[bool] = Field(False, description="Force unload even if in use")
    
    @validator('model_id')
    def validate_model_id(cls, v):
        if not v.strip():
            raise ValueError("Model ID cannot be empty")
        return v.strip()


class BenchmarkRequest(BaseModel):
    """Benchmark request schema"""
    num_samples: Optional[int] = Field(10, ge=1, le=100, description="Number of benchmark samples")
    max_tokens: Optional[int] = Field(100, ge=10, le=1000, description="Maximum tokens per sample")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    include_memory_test: Optional[bool] = Field(True, description="Include memory usage test")
    include_warmup: Optional[bool] = Field(True, description="Include warmup phase")


class WarmupRequest(BaseModel):
    """Model warmup request schema"""
    sample_prompts: Optional[List[str]] = Field(
        None, 
        max_items=10, 
        description="Custom prompts for warmup (default prompts used if not provided)"
    )
    max_tokens: Optional[int] = Field(50, ge=10, le=500, description="Maximum tokens for warmup")
    
    @validator('sample_prompts')
    def validate_prompts(cls, v):
        if v is not None:
            for prompt in v:
                if not isinstance(prompt, str) or not prompt.strip():
                    raise ValueError("All prompts must be non-empty strings")
                if len(prompt) > 1000:
                    raise ValueError("Prompt too long (max 1000 characters)")
        return v


class CacheSettingsRequest(BaseModel):
    """KV cache settings request schema"""
    max_cache_size_mb: Optional[int] = Field(None, ge=100, le=8192, description="Maximum cache size in MB")
    cache_ttl_seconds: Optional[int] = Field(None, ge=60, le=86400, description="Cache TTL in seconds")
    max_conversations: Optional[int] = Field(None, ge=1, le=1000, description="Maximum conversations to cache")
    enable_cache: Optional[bool] = Field(None, description="Enable or disable caching")


class ModelInfo(BaseModel):
    """Model information schema"""
    model_id: str = Field(..., description="Model identifier")
    status: Literal["loading", "loaded", "unloaded", "error", "downloading"] = Field(..., description="Model status")
    size_mb: Optional[float] = Field(None, description="Model size in megabytes")
    memory_usage_mb: Optional[float] = Field(None, description="Current memory usage in MB")
    load_time_seconds: Optional[float] = Field(None, description="Time taken to load model")
    last_used: Optional[datetime] = Field(None, description="Last time model was used")
    format: Optional[str] = Field(None, description="Model format (MLX, GGUF, etc.)")
    architecture: Optional[str] = Field(None, description="Model architecture")
    parameters: Optional[str] = Field(None, description="Number of parameters")
    quantization: Optional[str] = Field(None, description="Quantization method")
    error_message: Optional[str] = Field(None, description="Error message if status is error")


class ModelListResponse(BaseModel):
    """Model list response schema"""
    models: List[ModelInfo] = Field(..., description="List of models")
    total_memory_usage_mb: float = Field(..., description="Total memory usage of all loaded models")
    available_memory_mb: float = Field(..., description="Available memory for new models")


class BenchmarkResult(BaseModel):
    """Benchmark result schema"""
    model_id: str = Field(..., description="Model identifier")
    timestamp: datetime = Field(..., description="Benchmark timestamp")
    tokens_per_second: float = Field(..., description="Average tokens per second")
    first_token_latency_ms: float = Field(..., description="First token latency in milliseconds")
    total_tokens: int = Field(..., description="Total tokens generated")
    total_time_seconds: float = Field(..., description="Total benchmark time")
    memory_usage_mb: float = Field(..., description="Memory usage during benchmark")
    gpu_utilization_percent: Optional[float] = Field(None, description="GPU utilization percentage")
    samples: List[Dict[str, Any]] = Field(..., description="Individual sample results")


class WarmupResult(BaseModel):
    """Warmup result schema"""
    model_id: str = Field(..., description="Model identifier")
    timestamp: datetime = Field(..., description="Warmup timestamp")
    warmup_time_seconds: float = Field(..., description="Time taken for warmup")
    first_token_latency_ms: float = Field(..., description="First token latency after warmup")
    success: bool = Field(..., description="Whether warmup was successful")
    error_message: Optional[str] = Field(None, description="Error message if unsuccessful")


class CacheStatus(BaseModel):
    """Cache status schema"""
    enabled: bool = Field(..., description="Whether cache is enabled")
    total_size_mb: float = Field(..., description="Total cache size in MB")
    used_size_mb: float = Field(..., description="Used cache size in MB")
    available_size_mb: float = Field(..., description="Available cache size in MB")
    total_conversations: int = Field(..., description="Total conversations in cache")
    hit_rate: float = Field(..., description="Cache hit rate percentage")
    total_hits: int = Field(..., description="Total cache hits")
    total_misses: int = Field(..., description="Total cache misses")
    oldest_entry: Optional[datetime] = Field(None, description="Timestamp of oldest cache entry")


class CacheSettings(BaseModel):
    """Cache settings schema"""
    max_cache_size_mb: int = Field(..., description="Maximum cache size in MB")
    cache_ttl_seconds: int = Field(..., description="Cache TTL in seconds")
    max_conversations: int = Field(..., description="Maximum conversations to cache")
    enable_cache: bool = Field(..., description="Whether cache is enabled")


class DiscoveredModel(BaseModel):
    """Discovered model schema"""
    model_id: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Human-readable model name")
    description: Optional[str] = Field(None, description="Model description")
    size_gb: float = Field(..., description="Model size in gigabytes")
    parameters: str = Field(..., description="Number of parameters")
    architecture: str = Field(..., description="Model architecture")
    quantization: Optional[str] = Field(None, description="Quantization method")
    license: Optional[str] = Field(None, description="Model license")
    performance_estimate: Optional[Dict[str, float]] = Field(None, description="Performance estimates")
    recommended_memory_gb: float = Field(..., description="Recommended system memory")
    tags: List[str] = Field(default_factory=list, description="Model tags")
    is_downloaded: bool = Field(False, description="Whether model is already downloaded")


class ModelDiscoveryResponse(BaseModel):
    """Model discovery response schema"""
    models: List[DiscoveredModel] = Field(..., description="List of discovered models")
    total_models: int = Field(..., description="Total number of models")
    categories: List[str] = Field(..., description="Available model categories")
    hardware_compatibility: Dict[str, bool] = Field(..., description="Hardware compatibility info")


class OperationResponse(BaseModel):
    """Generic operation response schema"""
    success: bool = Field(..., description="Whether operation was successful")
    message: str = Field(..., description="Operation result message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")
    error_code: Optional[str] = Field(None, description="Error code if unsuccessful")


class DownloadProgress(BaseModel):
    """Download progress schema"""
    model_id: str = Field(..., description="Model identifier")
    status: Literal["downloading", "completed", "error", "cancelled"] = Field(..., description="Download status")
    progress_percent: float = Field(..., ge=0.0, le=100.0, description="Download progress percentage")
    downloaded_mb: float = Field(..., description="Downloaded size in MB")
    total_mb: float = Field(..., description="Total size in MB")
    speed_mbps: Optional[float] = Field(None, description="Download speed in MB/s")
    eta_seconds: Optional[int] = Field(None, description="Estimated time to completion")
    error_message: Optional[str] = Field(None, description="Error message if status is error")