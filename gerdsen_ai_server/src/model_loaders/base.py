"""
Base model loader interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from loguru import logger


class BaseModelLoader(ABC):
    """Abstract base class for all model loaders"""
    
    def __init__(self):
        self.loaded_models: Dict[str, Any] = {}
        self.model_configs: Dict[str, Dict] = {}
    
    @abstractmethod
    def load_model(self, model_id: str, **kwargs) -> 'BaseModel':
        """Load a model by ID or path"""
        pass
    
    @abstractmethod
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory"""
        pass
    
    @abstractmethod
    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available models"""
        pass
    
    @abstractmethod
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get information about a specific model"""
        pass
    
    def is_model_loaded(self, model_id: str) -> bool:
        """Check if a model is currently loaded"""
        return model_id in self.loaded_models
    
    def get_loaded_model(self, model_id: str) -> Optional['BaseModel']:
        """Get a loaded model instance"""
        return self.loaded_models.get(model_id)


class BaseModel(ABC):
    """Abstract base class for all models"""
    
    def __init__(self, model_id: str, model_path: Union[str, Path]):
        self.model_id = model_id
        self.model_path = Path(model_path) if isinstance(model_path, str) else model_path
        self.config: Dict[str, Any] = {}
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
    def tokenize(self, text: str) -> List[int]:
        """Tokenize input text"""
        pass
    
    @abstractmethod
    def detokenize(self, tokens: List[int]) -> str:
        """Detokenize tokens to text"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
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


class ModelLoadError(Exception):
    """Exception raised when model loading fails"""
    pass


class ModelNotFoundError(Exception):
    """Exception raised when model is not found"""
    pass


class InferenceError(Exception):
    """Exception raised during inference"""
    pass