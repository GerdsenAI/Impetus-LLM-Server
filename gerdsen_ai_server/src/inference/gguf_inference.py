"""
GGUF Inference Engine for Impetus-LLM-Server
Handles text generation using GGUF models with MLX backend
"""

import os
import time
import json
import logging
from typing import Dict, List, Optional, Any, Iterator, Union
from dataclasses import dataclass
import numpy as np

# Try multiple GGUF inference backends
INFERENCE_BACKEND = None

logger = logging.getLogger(__name__)

# Try llama-cpp-python first (most reliable for GGUF)
try:
    from llama_cpp import Llama
    INFERENCE_BACKEND = "llama_cpp"
    logger.info("✅ Using llama-cpp-python for GGUF inference")
except ImportError:
    pass

# Try MLX as fallback
if INFERENCE_BACKEND is None:
    try:
        import mlx.core as mx
        import mlx.nn as nn
        from mlx_lm import load, generate
        INFERENCE_BACKEND = "mlx"
        logger.info("✅ Using MLX for GGUF inference")
    except ImportError:
        pass

# Try transformers as last resort
if INFERENCE_BACKEND is None:
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        INFERENCE_BACKEND = "transformers"
        logger.info("⚠️ Using transformers for GGUF inference (may have limited GGUF support)")
    except ImportError:
        pass

if INFERENCE_BACKEND is None:
    logger.warning("❌ No GGUF inference backend available - using dummy responses")
    INFERENCE_BACKEND = "dummy"


@dataclass
class GenerationConfig:
    """Configuration for text generation"""
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repetition_penalty: float = 1.1
    seed: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    stream: bool = False


@dataclass
class InferenceResult:
    """Result from inference"""
    text: str
    tokens_generated: int
    time_taken: float
    tokens_per_second: float
    finish_reason: str  # "stop", "length", "stop_sequence"


class GGUFInferenceEngine:
    """Inference engine for GGUF models using MLX backend"""
    
    def __init__(self):
        self.logger = logger
        self.loaded_models: Dict[str, Any] = {}
        self.tokenizers: Dict[str, Any] = {}
        
    def load_model_for_inference(self, model_id: str, model_path: str, model_info: Dict[str, Any]) -> bool:
        """
        Load a GGUF model for inference
        
        Args:
            model_id: Unique identifier for the model
            model_path: Path to GGUF file
            model_info: Model metadata from GGUF loader
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Loading GGUF model {model_id} for inference using {INFERENCE_BACKEND}")
            
            if INFERENCE_BACKEND == "llama_cpp":
                # Load with llama-cpp-python
                if not os.path.exists(model_path):
                    raise FileNotFoundError(f"Model file not found: {model_path}")
                
                # Initialize Llama model with Metal GPU support
                model = Llama(
                    model_path=model_path,
                    n_ctx=model_info.get('context_length', 2048),
                    n_threads=os.cpu_count() // 2,  # Use half the CPU cores
                    n_gpu_layers=-1,  # Use all layers on GPU (Metal)
                    use_mlock=True,   # Lock model in memory
                    verbose=False
                )
                
                self.loaded_models[model_id] = {
                    'type': 'llama_cpp',
                    'info': model_info,
                    'path': model_path,
                    'model': model,
                    'tokenizer': None
                }
                
                self.logger.info(f"✅ GGUF model {model_id} loaded successfully with llama-cpp-python")
                return True
                
            elif INFERENCE_BACKEND == "mlx":
                # Load with MLX
                self.loaded_models[model_id] = {
                    'type': 'mlx',
                    'info': model_info,
                    'path': model_path,
                    'model': None,  # Would be actual MLX model
                    'tokenizer': None  # Would be actual tokenizer
                }
                
                self.logger.info(f"✅ Model {model_id} prepared for MLX inference")
                return True
                
            else:
                # Fallback to dummy
                self.logger.warning(f"No inference backend available, using dummy inference for {model_id}")
                self.loaded_models[model_id] = {
                    'type': 'dummy',
                    'info': model_info,
                    'path': model_path
                }
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to load model {model_id}: {e}")
            return False
    
    def generate(self, 
                 model_id: str,
                 prompt: str,
                 config: Optional[GenerationConfig] = None) -> InferenceResult:
        """
        Generate text using a loaded model
        
        Args:
            model_id: ID of the model to use
            prompt: Input text prompt
            config: Generation configuration
            
        Returns:
            InferenceResult with generated text
        """
        if model_id not in self.loaded_models:
            raise ValueError(f"Model {model_id} not loaded")
        
        if config is None:
            config = GenerationConfig()
        
        start_time = time.time()
        model_data = self.loaded_models[model_id]
        
        if model_data['type'] == 'llama_cpp':
            # Real llama-cpp-python inference
            model = model_data['model']
            
            # Prepare generation parameters
            stop_sequences = config.stop_sequences or []
            
            # Generate text
            response = model(
                prompt,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                top_k=config.top_k,
                repeat_penalty=config.repetition_penalty,
                stop=stop_sequences,
                echo=False
            )
            
            generated_text = response['choices'][0]['text']
            tokens_generated = response['usage']['completion_tokens']
            finish_reason = response['choices'][0]['finish_reason']
            
        elif model_data['type'] == 'mlx':
            # Real MLX generation would go here
            generated_text = f"[MLX inference not yet implemented for: {prompt[:50]}...]"
            tokens_generated = 20
            finish_reason = "stop"
            
        else:
            # Dummy implementation for testing
            generated_text = self._dummy_generate(prompt, config)
            tokens_generated = len(generated_text.split())
            finish_reason = "stop"
        
        time_taken = time.time() - start_time
        tokens_per_second = tokens_generated / time_taken if time_taken > 0 else 0
        
        return InferenceResult(
            text=generated_text,
            tokens_generated=tokens_generated,
            time_taken=time_taken,
            tokens_per_second=tokens_per_second,
            finish_reason=finish_reason
        )
    
    def generate_stream(self,
                       model_id: str,
                       prompt: str,
                       config: Optional[GenerationConfig] = None) -> Iterator[str]:
        """
        Generate text in streaming mode
        
        Args:
            model_id: ID of the model to use
            prompt: Input text prompt
            config: Generation configuration
            
        Yields:
            Generated text tokens
        """
        if model_id not in self.loaded_models:
            raise ValueError(f"Model {model_id} not loaded")
        
        if config is None:
            config = GenerationConfig()
        
        model_data = self.loaded_models[model_id]
        
        if model_data['type'] == 'dummy':
            # Dummy streaming implementation
            yield from self._dummy_stream(prompt, config)
        else:
            # Real streaming implementation would go here
            test_response = f"This is a streaming response to: {prompt}"
            for word in test_response.split():
                yield word + " "
                time.sleep(0.05)  # Simulate generation time
    
    def _dummy_generate(self, prompt: str, config: GenerationConfig) -> str:
        """Dummy generation for testing"""
        # Simple response based on prompt
        if "hello" in prompt.lower():
            return "Hello! I'm a GGUF model running locally. How can I help you today?"
        elif "code" in prompt.lower():
            return """Here's a simple Python function:

```python
def greet(name):
    return f"Hello, {name}!"

# Example usage
print(greet("World"))
```

This function takes a name parameter and returns a greeting string."""
        elif "explain" in prompt.lower():
            return "I'd be happy to explain! This is a locally running GGUF model that provides AI assistance without requiring cloud services. The model runs entirely on your machine, ensuring privacy and low latency."
        else:
            return f"I received your prompt: '{prompt[:100]}...' and I'm responding with this test message. In a real implementation, I would generate a meaningful response based on the model's training."
    
    def _dummy_stream(self, prompt: str, config: GenerationConfig) -> Iterator[str]:
        """Dummy streaming for testing"""
        response = self._dummy_generate(prompt, config)
        
        # Simulate word-by-word streaming
        words = response.split()
        for word in words:
            yield word + " "
            time.sleep(0.02)  # Simulate generation delay
    
    def create_chat_completion(self,
                              model_id: str,
                              messages: List[Dict[str, str]],
                              config: Optional[GenerationConfig] = None,
                              stream: bool = False,
                              max_tokens: int = None,
                              temperature: float = None) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """
        Create a chat completion (OpenAI-compatible format)
        
        Args:
            model_id: ID of the model to use
            messages: List of message dicts with 'role' and 'content'
            config: Generation configuration
            stream: Whether to stream the response
            max_tokens: Maximum number of tokens to generate (overrides config)
            temperature: Temperature for sampling (overrides config)
            
        Returns:
            OpenAI-compatible response dict or stream
        """
        # Convert messages to prompt
        prompt = self._messages_to_prompt(messages)
        
        # Create or update config with provided parameters
        if config is None:
            config = GenerationConfig()
            
        # Override config with explicit parameters if provided
        if max_tokens is not None:
            config.max_tokens = max_tokens
            
        if temperature is not None:
            config.temperature = temperature
        
        if stream:
            return self._stream_chat_completion(model_id, prompt, config)
        else:
            # Generate response
            result = self.generate(model_id, prompt, config)
            
            # Format as OpenAI response
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
            
            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        # Add final assistant prompt
        prompt_parts.append("Assistant:")
        
        return "\n\n".join(prompt_parts)
    
    def _stream_chat_completion(self,
                               model_id: str,
                               prompt: str,
                               config: Optional[GenerationConfig] = None) -> Iterator[Dict[str, Any]]:
        """Stream chat completion in OpenAI format"""
        
        # Initial response
        chunk_id = f"chatcmpl-{int(time.time())}"
        
        # First chunk
        yield {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model_id,
            "choices": [{
                "index": 0,
                "delta": {"role": "assistant"},
                "finish_reason": None
            }]
        }
        
        # Stream content
        for token in self.generate_stream(model_id, prompt, config):
            yield {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model_id,
                "choices": [{
                    "index": 0,
                    "delta": {"content": token},
                    "finish_reason": None
                }]
            }
        
        # Final chunk
        yield {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model_id,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
    
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory"""
        if model_id in self.loaded_models:
            # Clean up model resources
            del self.loaded_models[model_id]
            if model_id in self.tokenizers:
                del self.tokenizers[model_id]
            
            self.logger.info(f"Unloaded model {model_id}")
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
_inference_engine = None

def get_inference_engine() -> GGUFInferenceEngine:
    """Get or create the global inference engine instance"""
    global _inference_engine
    if _inference_engine is None:
        _inference_engine = GGUFInferenceEngine()
    return _inference_engine


def main():
    """Test the inference engine"""
    logging.basicConfig(level=logging.INFO)
    
    engine = get_inference_engine()
    
    # Simulate loading a model
    test_model_info = {
        'name': 'test-gguf-model',
        'architecture': 'llama',
        'context_length': 2048,
        'quantization': 'Q4_K_M'
    }
    
    success = engine.load_model_for_inference(
        'test-model',
        '/path/to/test.gguf',
        test_model_info
    )
    
    if success:
        print("Model loaded successfully!")
        
        # Test generation
        result = engine.generate(
            'test-model',
            'Hello, how are you?',
            GenerationConfig(max_tokens=50)
        )
        
        print(f"\nGenerated: {result.text}")
        print(f"Tokens: {result.tokens_generated}")
        print(f"Speed: {result.tokens_per_second:.2f} tokens/sec")
        
        # Test streaming
        print("\nStreaming test:")
        for token in engine.generate_stream('test-model', 'Tell me a story'):
            print(token, end='', flush=True)
        print()
        
        # Test chat completion
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is Python?"}
        ]
        
        response = engine.create_chat_completion('test-model', messages)
        print(f"\nChat completion: {response['choices'][0]['message']['content']}")


if __name__ == "__main__":
    main()
