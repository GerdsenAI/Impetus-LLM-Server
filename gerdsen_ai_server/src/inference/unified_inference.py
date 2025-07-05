"""
Unified Inference Interface for IMPETUS (Intelligent Model Platform Enabling Taskbar Unified Server)
Provides a single interface for inference across all supported model formats
"""

import os
import time
import json
import logging
from typing import Dict, List, Optional, Any, Iterator, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Import existing components
from .gguf_inference import GGUFInferenceEngine, GenerationConfig, InferenceResult

logger = logging.getLogger(__name__)


class BaseInferenceEngine(ABC):
    """Base class for all inference engines"""
    
    @abstractmethod
    def load_model_for_inference(self, model_id: str, model_path: str, model_info: Dict[str, Any]) -> bool:
        """Load a model for inference"""
        pass
    
    @abstractmethod
    def generate(self, model_id: str, prompt: str, config: Optional[GenerationConfig] = None) -> InferenceResult:
        """Generate text using a loaded model"""
        pass
    
    @abstractmethod
    def generate_stream(self, model_id: str, prompt: str, config: Optional[GenerationConfig] = None) -> Iterator[str]:
        """Generate text in streaming mode"""
        pass
    
    @abstractmethod
    def create_chat_completion(self, model_id: str, messages: List[Dict[str, str]], 
                             config: Optional[GenerationConfig] = None, stream: bool = False) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """Create a chat completion (OpenAI-compatible format)"""
        pass
    
    @abstractmethod
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory"""
        pass
    
    @abstractmethod
    def get_loaded_models(self) -> List[str]:
        """Get list of loaded model IDs"""
        pass
    
    @abstractmethod
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded model"""
        pass


class UnifiedInferenceEngine:
    """Unified inference engine that routes to format-specific engines"""
    
    def __init__(self):
        self.logger = logger
        self.engines: Dict[str, BaseInferenceEngine] = {}
        self.model_registry: Dict[str, str] = {}  # model_id -> format
        
        # Initialize format-specific engines
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize all format-specific inference engines"""
        
        # GGUF engine (already implemented)
        self.engines['gguf'] = GGUFInferenceEngine()
        
        # Placeholder engines for other formats
        self.engines['safetensors'] = SafeTensorsInferenceEngine()
        self.engines['mlx'] = MLXInferenceEngine()
        self.engines['coreml'] = CoreMLInferenceEngine()
        self.engines['pytorch'] = PyTorchInferenceEngine()
        self.engines['onnx'] = ONNXInferenceEngine()
        
        self.logger.info("Initialized all inference engines")
    
    def load_model_for_inference(self, model_id: str, model_path: str, model_info: Dict[str, Any], 
                                 model_format: str) -> bool:
        """
        Load a model for inference using the appropriate engine
        
        Args:
            model_id: Unique identifier for the model
            model_path: Path to model file/directory
            model_info: Model metadata from loader
            model_format: Format type (gguf, safetensors, mlx, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if model_format not in self.engines:
                self.logger.error(f"Unsupported model format: {model_format}")
                return False
            
            # Load using format-specific engine
            engine = self.engines[model_format]
            success = engine.load_model_for_inference(model_id, model_path, model_info)
            
            if success:
                self.model_registry[model_id] = model_format
                self.logger.info(f"Loaded model {model_id} ({model_format}) for inference")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to load model {model_id}: {e}")
            return False
    
    def generate(self, model_id: str, prompt: str, config: Optional[GenerationConfig] = None) -> InferenceResult:
        """Generate text using the appropriate engine for the model"""
        if model_id not in self.model_registry:
            raise ValueError(f"Model {model_id} not loaded")
        
        model_format = self.model_registry[model_id]
        engine = self.engines[model_format]
        
        return engine.generate(model_id, prompt, config)
    
    def generate_stream(self, model_id: str, prompt: str, config: Optional[GenerationConfig] = None) -> Iterator[str]:
        """Generate text in streaming mode using the appropriate engine"""
        if model_id not in self.model_registry:
            raise ValueError(f"Model {model_id} not loaded")
        
        model_format = self.model_registry[model_id]
        engine = self.engines[model_format]
        
        yield from engine.generate_stream(model_id, prompt, config)
    
    def create_chat_completion(self, model_id: str, messages: List[Dict[str, str]], 
                             config: Optional[GenerationConfig] = None, stream: bool = False) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """Create a chat completion using the appropriate engine"""
        if model_id not in self.model_registry:
            raise ValueError(f"Model {model_id} not loaded")
        
        model_format = self.model_registry[model_id]
        engine = self.engines[model_format]
        
        return engine.create_chat_completion(model_id, messages, config, stream)
    
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from the appropriate engine"""
        if model_id not in self.model_registry:
            return False
        
        model_format = self.model_registry[model_id]
        engine = self.engines[model_format]
        
        success = engine.unload_model(model_id)
        if success:
            del self.model_registry[model_id]
            self.logger.info(f"Unloaded model {model_id}")
        
        return success
    
    def get_loaded_models(self) -> Dict[str, str]:
        """Get dict of loaded model IDs and their formats"""
        return self.model_registry.copy()
    
    def get_all_loaded_models(self) -> List[str]:
        """Get list of all loaded model IDs"""
        return list(self.model_registry.keys())
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded model"""
        if model_id not in self.model_registry:
            return None
        
        model_format = self.model_registry[model_id]
        engine = self.engines[model_format]
        
        return engine.get_model_info(model_id)
    
    def get_model_format(self, model_id: str) -> Optional[str]:
        """Get the format of a loaded model"""
        return self.model_registry.get(model_id)
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported model formats"""
        return list(self.engines.keys())
    
    def get_format_statistics(self) -> Dict[str, int]:
        """Get statistics on loaded models by format"""
        stats = {}
        for format_name in self.engines.keys():
            stats[format_name] = 0
        
        for model_format in self.model_registry.values():
            stats[model_format] += 1
        
        return stats


# Placeholder inference engines for other formats
# These will be implemented as dummy engines initially, then replaced with real implementations


class SafeTensorsInferenceEngine(BaseInferenceEngine):
    """Inference engine for SafeTensors models"""
    
    def __init__(self):
        self.logger = logger
        self.loaded_models: Dict[str, Any] = {}
    
    def load_model_for_inference(self, model_id: str, model_path: str, model_info: Dict[str, Any]) -> bool:
        """Load a SafeTensors model for inference"""
        try:
            self.logger.info(f"Loading SafeTensors model {model_id} for inference")
            
            # Store model info (actual loading would use transformers/torch)
            self.loaded_models[model_id] = {
                'type': 'safetensors',
                'info': model_info,
                'path': model_path
            }
            
            self.logger.info(f"SafeTensors model {model_id} loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load SafeTensors model {model_id}: {e}")
            return False
    
    def generate(self, model_id: str, prompt: str, config: Optional[GenerationConfig] = None) -> InferenceResult:
        """Generate text using SafeTensors model"""
        if model_id not in self.loaded_models:
            raise ValueError(f"SafeTensors model {model_id} not loaded")
        
        if config is None:
            config = GenerationConfig()
        
        start_time = time.time()
        
        # Dummy implementation - would use actual SafeTensors/transformers
        generated_text = f"[SafeTensors response to: {prompt[:50]}...] This is a SafeTensors model providing helpful assistance."
        tokens_generated = len(generated_text.split())
        
        time_taken = time.time() - start_time
        tokens_per_second = tokens_generated / time_taken if time_taken > 0 else 0
        
        return InferenceResult(
            text=generated_text,
            tokens_generated=tokens_generated,
            time_taken=time_taken,
            tokens_per_second=tokens_per_second,
            finish_reason="stop"
        )
    
    def generate_stream(self, model_id: str, prompt: str, config: Optional[GenerationConfig] = None) -> Iterator[str]:
        """Generate text in streaming mode"""
        if model_id not in self.loaded_models:
            raise ValueError(f"SafeTensors model {model_id} not loaded")
        
        # Dummy streaming
        response = f"This is a streaming SafeTensors response to your prompt: {prompt}"
        for word in response.split():
            yield word + " "
            time.sleep(0.03)
    
    def create_chat_completion(self, model_id: str, messages: List[Dict[str, str]], 
                             config: Optional[GenerationConfig] = None, stream: bool = False) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """Create a chat completion"""
        prompt = self._messages_to_prompt(messages)
        
        if stream:
            return self._stream_chat_completion(model_id, prompt, config)
        else:
            result = self.generate(model_id, prompt, config)
            
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model_id,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result.text
                    },
                    "finish_reason": result.finish_reason
                }],
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": result.tokens_generated,
                    "total_tokens": len(prompt.split()) + result.tokens_generated
                }
            }
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to a single prompt"""
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            prompt_parts.append(f"{role.title()}: {content}")
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)
    
    def _stream_chat_completion(self, model_id: str, prompt: str, config: Optional[GenerationConfig] = None) -> Iterator[Dict[str, Any]]:
        """Stream chat completion in OpenAI format"""
        chunk_id = f"chatcmpl-{int(time.time())}"
        
        # First chunk
        yield {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model_id,
            "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]
        }
        
        # Stream content
        for token in self.generate_stream(model_id, prompt, config):
            yield {
                "id": chunk_id,
                "object": "chat.completion.chunk", 
                "created": int(time.time()),
                "model": model_id,
                "choices": [{"index": 0, "delta": {"content": token}, "finish_reason": None}]
            }
        
        # Final chunk
        yield {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model_id,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
        }
    
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory"""
        if model_id in self.loaded_models:
            del self.loaded_models[model_id]
            self.logger.info(f"Unloaded SafeTensors model {model_id}")
            return True
        return False
    
    def get_loaded_models(self) -> List[str]:
        """Get list of loaded model IDs"""
        return list(self.loaded_models.keys())
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded model"""
        if model_id in self.loaded_models:
            return self.loaded_models[model_id]['info']
        return None


class MLXInferenceEngine(BaseInferenceEngine):
    """Inference engine for MLX models"""
    
    def __init__(self):
        self.logger = logger
        self.loaded_models: Dict[str, Any] = {}
    
    def load_model_for_inference(self, model_id: str, model_path: str, model_info: Dict[str, Any]) -> bool:
        """Load an MLX model for inference"""
        try:
            self.logger.info(f"Loading MLX model {model_id} for inference")
            
            self.loaded_models[model_id] = {
                'type': 'mlx',
                'info': model_info,
                'path': model_path
            }
            
            self.logger.info(f"MLX model {model_id} loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load MLX model {model_id}: {e}")
            return False
    
    def generate(self, model_id: str, prompt: str, config: Optional[GenerationConfig] = None) -> InferenceResult:
        """Generate text using MLX model"""
        if model_id not in self.loaded_models:
            raise ValueError(f"MLX model {model_id} not loaded")
        
        if config is None:
            config = GenerationConfig()
        
        start_time = time.time()
        
        # Dummy implementation - would use actual MLX
        generated_text = f"[MLX optimized response]: This is an Apple Silicon optimized MLX model responding to: {prompt[:50]}..."
        tokens_generated = len(generated_text.split())
        
        time_taken = time.time() - start_time
        tokens_per_second = tokens_generated / time_taken if time_taken > 0 else 0
        
        return InferenceResult(
            text=generated_text,
            tokens_generated=tokens_generated,
            time_taken=time_taken,
            tokens_per_second=tokens_per_second,
            finish_reason="stop"
        )
    
    def generate_stream(self, model_id: str, prompt: str, config: Optional[GenerationConfig] = None) -> Iterator[str]:
        """Generate text in streaming mode"""
        if model_id not in self.loaded_models:
            raise ValueError(f"MLX model {model_id} not loaded")
        
        response = f"MLX streaming response optimized for Apple Silicon: {prompt}"
        for word in response.split():
            yield word + " "
            time.sleep(0.02)  # Fast Apple Silicon performance
    
    def create_chat_completion(self, model_id: str, messages: List[Dict[str, str]], 
                             config: Optional[GenerationConfig] = None, stream: bool = False) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """Create a chat completion"""
        prompt = self._messages_to_prompt(messages)
        
        if stream:
            return self._stream_chat_completion(model_id, prompt, config)
        else:
            result = self.generate(model_id, prompt, config)
            
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model_id,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant", 
                        "content": result.text
                    },
                    "finish_reason": result.finish_reason
                }],
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": result.tokens_generated,
                    "total_tokens": len(prompt.split()) + result.tokens_generated
                }
            }
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to a single prompt"""
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            prompt_parts.append(f"{role.title()}: {content}")
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)
    
    def _stream_chat_completion(self, model_id: str, prompt: str, config: Optional[GenerationConfig] = None) -> Iterator[Dict[str, Any]]:
        """Stream chat completion in OpenAI format"""
        chunk_id = f"chatcmpl-{int(time.time())}"
        
        yield {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model_id,
            "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]
        }
        
        for token in self.generate_stream(model_id, prompt, config):
            yield {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model_id,
                "choices": [{"index": 0, "delta": {"content": token}, "finish_reason": None}]
            }
        
        yield {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model_id,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
        }
    
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory"""
        if model_id in self.loaded_models:
            del self.loaded_models[model_id]
            self.logger.info(f"Unloaded MLX model {model_id}")
            return True
        return False
    
    def get_loaded_models(self) -> List[str]:
        """Get list of loaded model IDs"""
        return list(self.loaded_models.keys())
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded model"""
        if model_id in self.loaded_models:
            return self.loaded_models[model_id]['info']
        return None


class CoreMLInferenceEngine(BaseInferenceEngine):
    """Inference engine for CoreML models"""
    
    def __init__(self):
        self.logger = logger
        self.loaded_models: Dict[str, Any] = {}
    
    def load_model_for_inference(self, model_id: str, model_path: str, model_info: Dict[str, Any]) -> bool:
        """Load a CoreML model for inference"""
        try:
            self.logger.info(f"Loading CoreML model {model_id} for inference")
            
            self.loaded_models[model_id] = {
                'type': 'coreml',
                'info': model_info,
                'path': model_path
            }
            
            self.logger.info(f"CoreML model {model_id} loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load CoreML model {model_id}: {e}")
            return False
    
    def generate(self, model_id: str, prompt: str, config: Optional[GenerationConfig] = None) -> InferenceResult:
        """Generate text using CoreML model"""
        if model_id not in self.loaded_models:
            raise ValueError(f"CoreML model {model_id} not loaded")
        
        if config is None:
            config = GenerationConfig()
        
        start_time = time.time()
        
        generated_text = f"[CoreML Neural Engine]: Native iOS/macOS model response to: {prompt[:50]}..."
        tokens_generated = len(generated_text.split())
        
        time_taken = time.time() - start_time
        tokens_per_second = tokens_generated / time_taken if time_taken > 0 else 0
        
        return InferenceResult(
            text=generated_text,
            tokens_generated=tokens_generated,
            time_taken=time_taken,
            tokens_per_second=tokens_per_second,
            finish_reason="stop"
        )
    
    def generate_stream(self, model_id: str, prompt: str, config: Optional[GenerationConfig] = None) -> Iterator[str]:
        """Generate text in streaming mode"""
        if model_id not in self.loaded_models:
            raise ValueError(f"CoreML model {model_id} not loaded")
        
        response = f"CoreML Neural Engine optimized response: {prompt}"
        for word in response.split():
            yield word + " "
            time.sleep(0.025)
    
    def create_chat_completion(self, model_id: str, messages: List[Dict[str, str]], 
                             config: Optional[GenerationConfig] = None, stream: bool = False) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """Create a chat completion"""
        prompt = self._messages_to_prompt(messages)
        
        if stream:
            return self._stream_chat_completion(model_id, prompt, config)
        else:
            result = self.generate(model_id, prompt, config)
            
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model_id,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result.text
                    },
                    "finish_reason": result.finish_reason
                }],
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": result.tokens_generated,
                    "total_tokens": len(prompt.split()) + result.tokens_generated
                }
            }
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to a single prompt"""
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            prompt_parts.append(f"{role.title()}: {content}")
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)
    
    def _stream_chat_completion(self, model_id: str, prompt: str, config: Optional[GenerationConfig] = None) -> Iterator[Dict[str, Any]]:
        """Stream chat completion in OpenAI format"""
        chunk_id = f"chatcmpl-{int(time.time())}"
        
        yield {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model_id,
            "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]
        }
        
        for token in self.generate_stream(model_id, prompt, config):
            yield {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model_id,
                "choices": [{"index": 0, "delta": {"content": token}, "finish_reason": None}]
            }
        
        yield {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model_id,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
        }
    
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory"""
        if model_id in self.loaded_models:
            del self.loaded_models[model_id]
            self.logger.info(f"Unloaded CoreML model {model_id}")
            return True
        return False
    
    def get_loaded_models(self) -> List[str]:
        """Get list of loaded model IDs"""
        return list(self.loaded_models.keys())
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded model"""
        if model_id in self.loaded_models:
            return self.loaded_models[model_id]['info']
        return None


class PyTorchInferenceEngine(BaseInferenceEngine):
    """Inference engine for PyTorch models"""
    
    def __init__(self):
        self.logger = logger
        self.loaded_models: Dict[str, Any] = {}
    
    def load_model_for_inference(self, model_id: str, model_path: str, model_info: Dict[str, Any]) -> bool:
        """Load a PyTorch model for inference"""
        try:
            self.logger.info(f"Loading PyTorch model {model_id} for inference")
            
            self.loaded_models[model_id] = {
                'type': 'pytorch',
                'info': model_info,
                'path': model_path
            }
            
            self.logger.info(f"PyTorch model {model_id} loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load PyTorch model {model_id}: {e}")
            return False
    
    def generate(self, model_id: str, prompt: str, config: Optional[GenerationConfig] = None) -> InferenceResult:
        """Generate text using PyTorch model"""
        if model_id not in self.loaded_models:
            raise ValueError(f"PyTorch model {model_id} not loaded")
        
        if config is None:
            config = GenerationConfig()
        
        start_time = time.time()
        
        generated_text = f"[PyTorch MPS]: Deep learning model response to: {prompt[:50]}..."
        tokens_generated = len(generated_text.split())
        
        time_taken = time.time() - start_time
        tokens_per_second = tokens_generated / time_taken if time_taken > 0 else 0
        
        return InferenceResult(
            text=generated_text,
            tokens_generated=tokens_generated,
            time_taken=time_taken,
            tokens_per_second=tokens_per_second,
            finish_reason="stop"
        )
    
    def generate_stream(self, model_id: str, prompt: str, config: Optional[GenerationConfig] = None) -> Iterator[str]:
        """Generate text in streaming mode"""
        if model_id not in self.loaded_models:
            raise ValueError(f"PyTorch model {model_id} not loaded")
        
        response = f"PyTorch Metal Performance Shaders optimized response: {prompt}"
        for word in response.split():
            yield word + " "
            time.sleep(0.04)
    
    def create_chat_completion(self, model_id: str, messages: List[Dict[str, str]], 
                             config: Optional[GenerationConfig] = None, stream: bool = False) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """Create a chat completion"""
        prompt = self._messages_to_prompt(messages)
        
        if stream:
            return self._stream_chat_completion(model_id, prompt, config)
        else:
            result = self.generate(model_id, prompt, config)
            
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model_id,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result.text
                    },
                    "finish_reason": result.finish_reason
                }],
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": result.tokens_generated,
                    "total_tokens": len(prompt.split()) + result.tokens_generated
                }
            }
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to a single prompt"""
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            prompt_parts.append(f"{role.title()}: {content}")
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)
    
    def _stream_chat_completion(self, model_id: str, prompt: str, config: Optional[GenerationConfig] = None) -> Iterator[Dict[str, Any]]:
        """Stream chat completion in OpenAI format"""
        chunk_id = f"chatcmpl-{int(time.time())}"
        
        yield {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model_id,
            "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]
        }
        
        for token in self.generate_stream(model_id, prompt, config):
            yield {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model_id,
                "choices": [{"index": 0, "delta": {"content": token}, "finish_reason": None}]
            }
        
        yield {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model_id,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
        }
    
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory"""
        if model_id in self.loaded_models:
            del self.loaded_models[model_id]
            self.logger.info(f"Unloaded PyTorch model {model_id}")
            return True
        return False
    
    def get_loaded_models(self) -> List[str]:
        """Get list of loaded model IDs"""
        return list(self.loaded_models.keys())
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded model"""
        if model_id in self.loaded_models:
            return self.loaded_models[model_id]['info']
        return None


class ONNXInferenceEngine(BaseInferenceEngine):
    """Inference engine for ONNX models"""
    
    def __init__(self):
        self.logger = logger
        self.loaded_models: Dict[str, Any] = {}
    
    def load_model_for_inference(self, model_id: str, model_path: str, model_info: Dict[str, Any]) -> bool:
        """Load an ONNX model for inference"""
        try:
            self.logger.info(f"Loading ONNX model {model_id} for inference")
            
            self.loaded_models[model_id] = {
                'type': 'onnx',
                'info': model_info,
                'path': model_path
            }
            
            self.logger.info(f"ONNX model {model_id} loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load ONNX model {model_id}: {e}")
            return False
    
    def generate(self, model_id: str, prompt: str, config: Optional[GenerationConfig] = None) -> InferenceResult:
        """Generate text using ONNX model"""
        if model_id not in self.loaded_models:
            raise ValueError(f"ONNX model {model_id} not loaded")
        
        if config is None:
            config = GenerationConfig()
        
        start_time = time.time()
        
        generated_text = f"[ONNX Runtime]: Cross-platform optimized response to: {prompt[:50]}..."
        tokens_generated = len(generated_text.split())
        
        time_taken = time.time() - start_time
        tokens_per_second = tokens_generated / time_taken if time_taken > 0 else 0
        
        return InferenceResult(
            text=generated_text,
            tokens_generated=tokens_generated,
            time_taken=time_taken,
            tokens_per_second=tokens_per_second,
            finish_reason="stop"
        )
    
    def generate_stream(self, model_id: str, prompt: str, config: Optional[GenerationConfig] = None) -> Iterator[str]:
        """Generate text in streaming mode"""
        if model_id not in self.loaded_models:
            raise ValueError(f"ONNX model {model_id} not loaded")
        
        response = f"ONNX Runtime optimized streaming response: {prompt}"
        for word in response.split():
            yield word + " "
            time.sleep(0.035)
    
    def create_chat_completion(self, model_id: str, messages: List[Dict[str, str]], 
                             config: Optional[GenerationConfig] = None, stream: bool = False) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """Create a chat completion"""
        prompt = self._messages_to_prompt(messages)
        
        if stream:
            return self._stream_chat_completion(model_id, prompt, config)
        else:
            result = self.generate(model_id, prompt, config)
            
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model_id,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result.text
                    },
                    "finish_reason": result.finish_reason
                }],
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": result.tokens_generated,
                    "total_tokens": len(prompt.split()) + result.tokens_generated
                }
            }
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to a single prompt"""
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            prompt_parts.append(f"{role.title()}: {content}")
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)
    
    def _stream_chat_completion(self, model_id: str, prompt: str, config: Optional[GenerationConfig] = None) -> Iterator[Dict[str, Any]]:
        """Stream chat completion in OpenAI format"""
        chunk_id = f"chatcmpl-{int(time.time())}"
        
        yield {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model_id,
            "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]
        }
        
        for token in self.generate_stream(model_id, prompt, config):
            yield {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model_id,
                "choices": [{"index": 0, "delta": {"content": token}, "finish_reason": None}]
            }
        
        yield {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model_id,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
        }
    
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory"""
        if model_id in self.loaded_models:
            del self.loaded_models[model_id]
            self.logger.info(f"Unloaded ONNX model {model_id}")
            return True
        return False
    
    def get_loaded_models(self) -> List[str]:
        """Get list of loaded model IDs"""
        return list(self.loaded_models.keys())
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded model"""
        if model_id in self.loaded_models:
            return self.loaded_models[model_id]['info']
        return None


# Singleton instance
_unified_inference_engine = None

def get_unified_inference_engine() -> UnifiedInferenceEngine:
    """Get or create the global unified inference engine instance"""
    global _unified_inference_engine
    if _unified_inference_engine is None:
        _unified_inference_engine = UnifiedInferenceEngine()
    return _unified_inference_engine


def main():
    """Test the unified inference engine"""
    logging.basicConfig(level=logging.INFO)
    
    engine = get_unified_inference_engine()
    
    print("=== IMPETUS Unified Inference Engine Test ===")
    print(f"Supported formats: {engine.get_supported_formats()}")
    
    # Test with different model formats
    test_models = [
        ("test-gguf", "/path/to/test.gguf", {"name": "test-gguf"}, "gguf"),
        ("test-safetensors", "/path/to/test.safetensors", {"name": "test-safetensors"}, "safetensors"),
        ("test-mlx", "/path/to/test.mlx", {"name": "test-mlx"}, "mlx"),
    ]
    
    for model_id, path, info, format_type in test_models:
        print(f"\nTesting {format_type.upper()} model:")
        
        # Load model
        success = engine.load_model_for_inference(model_id, path, info, format_type)
        if success:
            print(f"✓ Loaded {model_id}")
            
            # Test generation
            result = engine.generate(model_id, "Hello, how are you?")
            print(f"Generated: {result.text[:100]}...")
            
            # Test chat completion
            messages = [{"role": "user", "content": "What is AI?"}]
            response = engine.create_chat_completion(model_id, messages)
            print(f"Chat response: {response['choices'][0]['message']['content'][:100]}...")
        else:
            print(f"✗ Failed to load {model_id}")
    
    print(f"\nLoaded models: {engine.get_loaded_models()}")
    print(f"Format statistics: {engine.get_format_statistics()}")


if __name__ == "__main__":
    main()