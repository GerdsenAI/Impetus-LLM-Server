"""
Base inference engine classes and utilities for IMPETUS
Provides common interfaces and configuration for all model formats
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union, Iterator
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)

class ModelFormat(Enum):
    """Supported model formats"""
    GGUF = "gguf"
    SAFETENSORS = "safetensors"
    MLX = "mlx"
    COREML = "coreml"
    PYTORCH = "pytorch"
    ONNX = "onnx"

@dataclass
class GenerationConfig:
    """Configuration for text generation"""
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.0
    stream: bool = False
    stop_sequences: Optional[List[str]] = None
    
    def __post_init__(self):
        # Ensure valid ranges
        self.temperature = max(0.0, min(2.0, self.temperature))
        self.top_p = max(0.0, min(1.0, self.top_p))
        self.top_k = max(1, self.top_k)
        self.max_tokens = max(1, self.max_tokens)
        self.repetition_penalty = max(0.1, min(2.0, self.repetition_penalty))

@dataclass
class GenerationResult:
    """Result from text generation"""
    text: str
    model_id: str
    format: str
    finish_reason: str = "stop"
    tokens_generated: int = 0
    generation_time: float = 0.0
    tokens_per_second: float = 0.0
    
    def to_openai_format(self, message_role: str = "assistant") -> Dict:
        """Convert to OpenAI chat completion format"""
        return {
            "choices": [{
                "index": 0,
                "message": {
                    "role": message_role,
                    "content": self.text
                },
                "finish_reason": self.finish_reason
            }],
            "usage": {
                "prompt_tokens": 0,  # Would need tokenizer to calculate
                "completion_tokens": self.tokens_generated,
                "total_tokens": self.tokens_generated
            },
            "model": self.model_id,
            "created": int(time.time())
        }

class BaseInferenceEngine(ABC):
    """Base class for model format-specific inference engines"""
    
    def __init__(self, format_name: str):
        self.format_name = format_name
        self.loaded_models = {}
        self.logger = logging.getLogger(f"{__name__}.{format_name}")
    
    @abstractmethod
    def can_load_model(self, model_path: str) -> bool:
        """Check if this engine can load the given model"""
        pass
    
    @abstractmethod
    def load_model_for_inference(self, model_id: str, model_path: str, model_info: Dict[str, Any]) -> bool:
        """Load a model for inference"""
        pass
    
    @abstractmethod
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory"""
        pass
    
    @abstractmethod
    def generate_text(self, model_id: str, prompt: str, config: GenerationConfig) -> Optional[GenerationResult]:
        """Generate text from a prompt"""
        pass
    
    @abstractmethod
    def generate_chat_completion(self, model_id: str, messages: List[Dict], config: GenerationConfig) -> Optional[Dict]:
        """Generate chat completion response"""
        pass
    
    def get_loaded_models(self) -> Dict[str, Any]:
        """Get list of loaded models"""
        return self.loaded_models.copy()
    
    def is_model_loaded(self, model_id: str) -> bool:
        """Check if a model is loaded"""
        return model_id in self.loaded_models
    
    def get_model_info(self, model_id: str) -> Optional[Dict]:
        """Get information about a loaded model"""
        return self.loaded_models.get(model_id)

class DummyInferenceEngine(BaseInferenceEngine):
    """Dummy inference engine for testing and development"""
    
    def __init__(self, format_name: str = "dummy"):
        super().__init__(format_name)
    
    def can_load_model(self, model_path: str) -> bool:
        """Dummy engine can 'load' any model"""
        return True
    
    def load_model_for_inference(self, model_id: str, model_path: str, model_info: Dict[str, Any]) -> bool:
        """Simulate loading a model"""
        self.logger.info(f"Loading dummy model {model_id} from {model_path}")
        
        self.loaded_models[model_id] = {
            "path": model_path,
            "info": model_info,
            "loaded_at": time.time(),
            "format": self.format_name
        }
        
        return True
    
    def unload_model(self, model_id: str) -> bool:
        """Simulate unloading a model"""
        if model_id in self.loaded_models:
            del self.loaded_models[model_id]
            self.logger.info(f"Unloaded dummy model {model_id}")
            return True
        return False
    
    def generate_text(self, model_id: str, prompt: str, config: GenerationConfig) -> Optional[GenerationResult]:
        """Generate dummy text response"""
        if model_id not in self.loaded_models:
            self.logger.error(f"Model {model_id} not loaded")
            return None
        
        # Simulate generation time
        start_time = time.time()
        
        # Generate dummy response
        dummy_responses = [
            "This is a dummy response generated by the IMPETUS system.",
            "Hello! I'm a local AI assistant running on your Apple Silicon Mac.",
            "I can help you with coding tasks when integrated with VS Code and Cline.",
            "The IMPETUS system supports multiple model formats including GGUF, SafeTensors, MLX, and more.",
            "Thank you for testing the IMPETUS MVP system!"
        ]
        
        # Simulate processing time based on max_tokens
        generation_time = min(1.0, config.max_tokens / 1000.0)
        time.sleep(generation_time)
        
        response_text = dummy_responses[hash(prompt) % len(dummy_responses)]
        
        # Truncate response to max_tokens (rough estimation)
        if config.max_tokens < 100:
            response_text = response_text[:config.max_tokens]
        
        end_time = time.time()
        actual_time = end_time - start_time
        
        return GenerationResult(
            text=response_text,
            model_id=model_id,
            format=self.format_name,
            finish_reason="stop",
            tokens_generated=len(response_text.split()),
            generation_time=actual_time,
            tokens_per_second=len(response_text.split()) / actual_time if actual_time > 0 else 0
        )
    
    def generate_chat_completion(self, model_id: str, messages: List[Dict], config: GenerationConfig) -> Optional[Dict]:
        """Generate dummy chat completion response"""
        if model_id not in self.loaded_models:
            self.logger.error(f"Model {model_id} not loaded")
            return None
        
        # Extract the last user message as the prompt
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if not user_messages:
            prompt = "Hello"
        else:
            prompt = user_messages[-1].get("content", "Hello")
        
        # Generate text response
        result = self.generate_text(model_id, prompt, config)
        if result is None:
            return None
        
        # Convert to OpenAI format
        return result.to_openai_format()

def create_inference_engine(format_type: ModelFormat) -> BaseInferenceEngine:
    """Factory function to create format-specific inference engines"""
    
    # For now, return dummy engines for all formats
    # In the future, this would return actual format-specific engines
    dummy_engine = DummyInferenceEngine(format_type.value)
    
    return dummy_engine

# Utility functions
def messages_to_prompt(messages: List[Dict]) -> str:
    """Convert OpenAI-style messages to a simple prompt"""
    prompt_parts = []
    
    for message in messages:
        role = message.get("role", "")
        content = message.get("content", "")
        
        if role == "system":
            prompt_parts.append(f"System: {content}")
        elif role == "user":
            prompt_parts.append(f"User: {content}")
        elif role == "assistant":
            prompt_parts.append(f"Assistant: {content}")
    
    prompt_parts.append("Assistant:")
    return "\n".join(prompt_parts)

def validate_generation_config(config: Dict) -> GenerationConfig:
    """Validate and create GenerationConfig from dictionary"""
    return GenerationConfig(
        max_tokens=config.get("max_tokens", 512),
        temperature=config.get("temperature", 0.7),
        top_p=config.get("top_p", 0.9),
        top_k=config.get("top_k", 50),
        repetition_penalty=config.get("repetition_penalty", 1.0),
        stream=config.get("stream", False),
        stop_sequences=config.get("stop", None)
    )