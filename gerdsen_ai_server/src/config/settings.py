from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerSettings(BaseSettings):
    """Server configuration settings"""
    host: str = Field(default="127.0.0.1", env="IMPETUS_HOST")  # Secure local-only binding
    port: int = Field(default=8080, env="IMPETUS_PORT")
    debug: bool = Field(default=False, env="IMPETUS_DEBUG")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="IMPETUS_CORS_ORIGINS"
    )
    api_key: str | None = Field(default=None, env="IMPETUS_API_KEY")

    # WebSocket settings
    websocket_ping_interval: int = Field(default=25, env="IMPETUS_WS_PING_INTERVAL")
    websocket_ping_timeout: int = Field(default=60, env="IMPETUS_WS_PING_TIMEOUT")

    model_config = SettingsConfigDict(env_prefix="IMPETUS_")


class ModelSettings(BaseSettings):
    """Model configuration settings"""
    models_dir: Path = Field(
        default=Path.home() / ".impetus" / "models",
        env="IMPETUS_MODELS_DIR"
    )
    cache_dir: Path = Field(
        default=Path.home() / ".impetus" / "cache",
        env="IMPETUS_CACHE_DIR"
    )
    max_loaded_models: int = Field(default=3, env="IMPETUS_MAX_LOADED_MODELS")
    default_model: str = Field(default="mlx-community/Mistral-7B-Instruct-v0.3-4bit", env="IMPETUS_DEFAULT_MODEL")

    # Model loading settings
    load_in_4bit: bool = Field(default=True, env="IMPETUS_LOAD_IN_4BIT")
    max_memory_gb: float | None = Field(default=None, env="IMPETUS_MAX_MEMORY_GB")

    @field_validator("models_dir", "cache_dir", mode="before")
    @classmethod
    def create_directories(cls, v):
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path

    model_config = SettingsConfigDict(env_prefix="IMPETUS_")


class InferenceSettings(BaseSettings):
    """Inference configuration settings"""
    max_tokens: int = Field(default=2048, env="IMPETUS_MAX_TOKENS")
    temperature: float = Field(default=0.7, env="IMPETUS_TEMPERATURE")
    top_p: float = Field(default=0.95, env="IMPETUS_TOP_P")
    repetition_penalty: float = Field(default=1.0, env="IMPETUS_REPETITION_PENALTY")

    # Batch settings
    max_batch_size: int = Field(default=1, env="IMPETUS_MAX_BATCH_SIZE")

    # Performance settings
    use_cache: bool = Field(default=True, env="IMPETUS_USE_CACHE")
    stream_by_default: bool = Field(default=True, env="IMPETUS_STREAM_BY_DEFAULT")

    model_config = SettingsConfigDict(env_prefix="IMPETUS_")


class HardwareSettings(BaseSettings):
    """Hardware optimization settings"""
    performance_mode: Literal["efficiency", "balanced", "performance"] = Field(
        default="balanced",
        env="IMPETUS_PERFORMANCE_MODE"
    )
    enable_thermal_management: bool = Field(default=True, env="IMPETUS_ENABLE_THERMAL_MANAGEMENT")
    enable_neural_engine: bool = Field(default=True, env="IMPETUS_ENABLE_NEURAL_ENGINE")
    enable_metal: bool = Field(default=True, env="IMPETUS_ENABLE_METAL")

    # Resource limits
    max_cpu_percent: float = Field(default=80.0, env="IMPETUS_MAX_CPU_PERCENT")
    max_memory_percent: float = Field(default=75.0, env="IMPETUS_MAX_MEMORY_PERCENT")

    model_config = SettingsConfigDict(env_prefix="IMPETUS_")


class ComputeSettings(BaseSettings):
    """Compute routing configuration for hybrid ANE/GPU inference"""
    enable_ane: bool = Field(default=True, env="IMPETUS_ENABLE_ANE")
    enable_metal: bool = Field(default=True, env="IMPETUS_ENABLE_METAL")
    preferred_embedding_device: Literal["auto", "ane", "gpu", "cpu"] = Field(
        default="auto", env="IMPETUS_PREFERRED_EMBEDDING_DEVICE"
    )
    default_embedding_model: str = Field(
        default="all-MiniLM-L6-v2", env="IMPETUS_DEFAULT_EMBEDDING_MODEL"
    )
    ane_max_model_size_mb: int = Field(default=500, env="IMPETUS_ANE_MAX_MODEL_SIZE_MB")
    ane_quantization: Literal["float16", "int8", "palettized"] = Field(
        default="float16", env="IMPETUS_ANE_QUANTIZATION"
    )
    embedding_cache_dir: Path = Field(
        default=Path.home() / ".impetus" / "models" / "embeddings",
        env="IMPETUS_EMBEDDING_CACHE_DIR"
    )
    max_batch_size_embedding: int = Field(default=32, env="IMPETUS_MAX_BATCH_SIZE_EMBEDDING")

    @field_validator("embedding_cache_dir", mode="before")
    @classmethod
    def create_embedding_cache_dir(cls, v):
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path

    model_config = SettingsConfigDict(env_prefix="IMPETUS_")


class VectorStoreSettings(BaseSettings):
    """Vector store configuration for RAG pipeline"""
    enabled: bool = Field(default=True, env="IMPETUS_VECTORSTORE_ENABLED")
    persist_directory: Path = Field(
        default=Path.home() / ".impetus" / "vectorstore",
        env="IMPETUS_VECTORSTORE_DIR"
    )
    default_collection: str = Field(default="documents", env="IMPETUS_VECTORSTORE_DEFAULT_COLLECTION")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="IMPETUS_VECTORSTORE_EMBEDDING_MODEL")
    chunk_size: int = Field(default=512, env="IMPETUS_CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, env="IMPETUS_CHUNK_OVERLAP")
    max_results: int = Field(default=5, env="IMPETUS_VECTORSTORE_MAX_RESULTS")

    @field_validator("persist_directory", mode="before")
    @classmethod
    def create_persist_directory(cls, v):
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path

    model_config = SettingsConfigDict(env_prefix="IMPETUS_")


class Settings(BaseSettings):
    """Main application settings"""
    app_name: str = "Impetus LLM Server"
    version: str = "0.1.0"

    # Sub-settings
    server: ServerSettings = Field(default_factory=ServerSettings)
    model: ModelSettings = Field(default_factory=ModelSettings)
    inference: InferenceSettings = Field(default_factory=InferenceSettings)
    hardware: HardwareSettings = Field(default_factory=HardwareSettings)
    compute: ComputeSettings = Field(default_factory=ComputeSettings)
    vectorstore: VectorStoreSettings = Field(default_factory=VectorStoreSettings)

    # Logging
    log_level: str = Field(default="INFO", env="IMPETUS_LOG_LEVEL")
    log_file: Path | None = Field(default=None, env="IMPETUS_LOG_FILE")

    # Environment
    environment: Literal["development", "production", "testing"] = Field(
        default="development",
        env="IMPETUS_ENV"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Singleton settings instance
settings = Settings()
