"""
Base model loader interface
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseModelLoader(ABC):
    """Abstract base class for all model loaders"""

    def __init__(self):
        self.loaded_models: dict[str, Any] = {}
        self.model_configs: dict[str, dict] = {}

    @abstractmethod
    def load_model(self, model_id: str, **kwargs) -> 'BaseModel':
        """Load a model by ID or path"""
        pass

    @abstractmethod
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory"""
        pass

    @abstractmethod
    def list_available_models(self) -> list[dict[str, Any]]:
        """List all available models"""
        pass

    @abstractmethod
    def get_model_info(self, model_id: str) -> dict[str, Any]:
        """Get information about a specific model"""
        pass

    def is_model_loaded(self, model_id: str) -> bool:
        """Check if a model is currently loaded"""
        return model_id in self.loaded_models

    def get_loaded_model(self, model_id: str) -> "BaseModel | None":
        """Get a loaded model instance"""
        return self.loaded_models.get(model_id)


class BaseModel(ABC):
    """Abstract base class for all models"""

    def __init__(self, model_id: str, model_path: str | Path):
        self.model_id = model_id
        self.model_path = Path(model_path) if isinstance(model_path, str) else model_path
        self.config: dict[str, Any] = {}
        self.tokenizer = None
        self.model = None
        self.device = "cpu"  # Will be set to "gpu" for Apple Silicon
        self.loaded = False

    @abstractmethod
    def load(self, **kwargs) -> None:
        """Load the model into memory"""
        pass

    @abstractmethod
    def unload(self) -> None:
        """Unload the model from memory"""
        pass

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt"""
        pass

    @abstractmethod
    def generate_stream(self, prompt: str, **kwargs):
        """Generate text in streaming mode"""
        pass

    @abstractmethod
    def tokenize(self, text: str) -> list[int]:
        """Tokenize input text"""
        pass

    @abstractmethod
    def detokenize(self, tokens: list[int]) -> str:
        """Detokenize tokens to text"""
        pass

    def get_info(self) -> dict[str, Any]:
        """Get model information"""
        return {
            'model_id': self.model_id,
            'model_path': str(self.model_path),
            'loaded': self.loaded,
            'device': self.device,
            'config': self.config
        }

    def __repr__(self):
        return f"{self.__class__.__name__}(model_id='{self.model_id}', loaded={self.loaded})"


class BaseEmbeddingModel(ABC):
    """Abstract base class for embedding models"""

    def __init__(self, model_name: str, model_path: str | Path, dimensions: int, max_tokens: int, device: str):
        self.model_name = model_name
        self.model_path = Path(model_path) if isinstance(model_path, str) else model_path
        self.dimensions = dimensions
        self.max_tokens = max_tokens
        self.device = device
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @abstractmethod
    def load(self) -> None:
        """Load the embedding model into memory"""

    @abstractmethod
    def unload(self) -> None:
        """Unload the embedding model from memory"""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts"""

    def get_info(self) -> dict[str, Any]:
        """Get embedding model metadata"""
        return {
            'model_name': self.model_name,
            'model_path': str(self.model_path),
            'dimensions': self.dimensions,
            'max_tokens': self.max_tokens,
            'device': self.device,
            'loaded': self._loaded,
        }

    def __repr__(self):
        return f"{self.__class__.__name__}(model_name='{self.model_name}', device='{self.device}', loaded={self._loaded})"


class BaseEmbeddingModelLoader(ABC):
    """Abstract base class for embedding model loaders"""

    def __init__(self):
        self._loaded_models: dict[str, BaseEmbeddingModel] = {}

    @abstractmethod
    def load_model(self, name: str) -> BaseEmbeddingModel:
        """Load an embedding model by short name"""

    @abstractmethod
    def unload_model(self, name: str) -> None:
        """Unload an embedding model"""

    @abstractmethod
    def list_available_models(self) -> list[dict[str, Any]]:
        """List all available embedding models"""

    def get_loaded_model(self, name: str) -> BaseEmbeddingModel | None:
        """Get a loaded embedding model by name"""
        return self._loaded_models.get(name)

    def is_model_loaded(self, name: str) -> bool:
        """Check if an embedding model is loaded"""
        return name in self._loaded_models and self._loaded_models[name].is_loaded


class ModelLoadError(Exception):
    """Exception raised when model loading fails"""
    pass


class ModelNotFoundError(Exception):
    """Exception raised when model is not found"""
    pass


class InferenceError(Exception):
    """Exception raised during inference"""
    pass


class EmbeddingError(Exception):
    """Exception raised during embedding operations"""
    pass
