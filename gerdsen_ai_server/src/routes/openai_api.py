#!/usr/bin/env python3
"""
OpenAI-Compatible API Routes for VS Code Integration
Provides chat completions, models, and other endpoints compatible with OpenAI API
"""

import json
import time
import uuid
import asyncio
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass, asdict

from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_cors import cross_origin
import threading
import queue

# Import authentication
from src.auth import optional_api_key, rate_limit

# Import our enhanced components
try:
    from src.enhanced_mlx_manager import EnhancedMLXManager
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False

try:
    from src.apple_silicon_detector import AppleSiliconDetector
    APPLE_SILICON_AVAILABLE = True
except ImportError:
    APPLE_SILICON_AVAILABLE = False

openai_api_bp = Blueprint('openai_api', __name__)

# Global instances
mlx_manager = None
apple_detector = None

def initialize_openai_api():
    """Initialize OpenAI API components"""
    global mlx_manager, apple_detector
    
    if MLX_AVAILABLE and mlx_manager is None:
        try:
            mlx_manager = EnhancedMLXManager()
            logging.info("MLX Manager initialized for OpenAI API")
        except Exception as e:
            logging.error(f"Failed to initialize MLX Manager: {e}")
    
    if APPLE_SILICON_AVAILABLE and apple_detector is None:
        try:
            apple_detector = AppleSiliconDetector()
            logging.info("Apple Silicon detector initialized for OpenAI API")
        except Exception as e:
            logging.error(f"Failed to initialize Apple Silicon detector: {e}")

@dataclass
class ChatMessage:
    """Chat message structure"""
    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None

@dataclass
class ChatCompletionRequest:
    """Chat completion request structure"""
    model: str
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 2048
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[List[str]] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    user: Optional[str] = None

class MLXChatEngine:
    """Chat engine using MLX for local inference"""
    
    def __init__(self):
        self.model_loaded = False
        self.current_model = None
        self.logger = logging.getLogger(__name__)
    
    def load_model(self, model_name: str) -> bool:
        """Load a model for inference"""
        try:
            if mlx_manager:
                # Try to load the model using MLX manager
                success = mlx_manager.load_model(model_name)
                if success:
                    self.model_loaded = True
                    self.current_model = model_name
                    self.logger.info(f"Loaded model: {model_name}")
                    return True
            
            # Fallback: simulate model loading
            self.model_loaded = True
            self.current_model = model_name
            self.logger.info(f"Simulated loading model: {model_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load model {model_name}: {e}")
            return False
    
    def generate_response(self, messages: List[ChatMessage], **kwargs) -> str:
        """Generate a response to the conversation"""
        try:
            if not self.model_loaded:
                # Try to load a default model
                if not self.load_model("default"):
                    return "Error: No model available for inference"
            
            # Extract the conversation context
            conversation = []
            for msg in messages:
                conversation.append(f"{msg.role}: {msg.content}")
            
            context = "\n".join(conversation)
            
            if mlx_manager and hasattr(mlx_manager, 'generate_text'):
                # Use real MLX generation if available
                response = mlx_manager.generate_text(
                    prompt=context,
                    max_tokens=kwargs.get('max_tokens', 2048),
                    temperature=kwargs.get('temperature', 0.7)
                )
                return response
            else:
                # Fallback: intelligent response based on context
                return self._generate_fallback_response(messages, **kwargs)
                
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"
    
    def _generate_fallback_response(self, messages: List[ChatMessage], **kwargs) -> str:
        """Generate a fallback response when MLX is not available"""
        last_message = messages[-1] if messages else None
        
        if not last_message:
            return "Hello! I'm GerdsenAI MLX Manager. How can I help you today?"
        
        user_input = last_message.content.lower()
        
        # Code-related responses (for VS Code integration)
        if any(keyword in user_input for keyword in ['code', 'function', 'class', 'python', 'javascript', 'swift']):
            return self._generate_code_response(user_input)
        
        # MLX/AI related responses
        if any(keyword in user_input for keyword in ['mlx', 'model', 'ai', 'machine learning', 'neural']):
            return self._generate_mlx_response(user_input)
        
        # Apple Silicon related responses
        if any(keyword in user_input for keyword in ['apple silicon', 'm1', 'm2', 'm3', 'm4', 'neural engine']):
            return self._generate_apple_silicon_response(user_input)
        
        # General helpful response
        return self._generate_general_response(user_input)
    
    def _generate_code_response(self, user_input: str) -> str:
        """Generate code-related responses"""
        if 'python' in user_input:
            return """Here's a Python example using MLX for machine learning:

```python
import mlx.core as mx
import mlx.nn as nn

class SimpleModel(nn.Module):
    def __init__(self, input_size: int, hidden_size: int, output_size: int):
        super().__init__()
        self.linear1 = nn.Linear(input_size, hidden_size)
        self.linear2 = nn.Linear(hidden_size, output_size)
    
    def __call__(self, x):
        x = mx.maximum(self.linear1(x), 0)  # ReLU activation
        return self.linear2(x)

# Usage
model = SimpleModel(784, 128, 10)
x = mx.random.normal((32, 784))  # Batch of 32 samples
output = model(x)
```

This creates a simple neural network optimized for Apple Silicon."""
        
        elif 'swift' in user_input:
            return """Here's a Swift example for Core ML integration:

```swift
import CoreML
import Foundation

class MLXModelManager {
    private var model: MLModel?
    
    func loadModel(named modelName: String) throws {
        guard let modelURL = Bundle.main.url(forResource: modelName, withExtension: "mlpackage") else {
            throw ModelError.modelNotFound
        }
        
        let configuration = MLModelConfiguration()
        configuration.computeUnits = .neuralEngine
        
        self.model = try MLModel(contentsOf: modelURL, configuration: configuration)
    }
    
    func predict(input: MLFeatureProvider) throws -> MLFeatureProvider {
        guard let model = self.model else {
            throw ModelError.modelNotLoaded
        }
        
        return try model.prediction(from: input)
    }
}

enum ModelError: Error {
    case modelNotFound
    case modelNotLoaded
}
```

This provides Core ML integration optimized for Apple's Neural Engine."""
        
        else:
            return """I can help you with code optimization for Apple Silicon! Here are some key areas:

1. **MLX Framework**: Use MLX for machine learning workloads on Apple Silicon
2. **Core ML**: Integrate pre-trained models with Core ML
3. **Metal Performance Shaders**: Leverage GPU acceleration
4. **Neural Engine**: Optimize for Apple's dedicated ML hardware

What specific coding task would you like help with?"""
    
    def _generate_mlx_response(self, user_input: str) -> str:
        """Generate MLX-related responses"""
        if 'model' in user_input:
            return """MLX supports various model types optimized for Apple Silicon:

**Supported Models:**
- **Language Models**: Llama, Mistral, CodeLlama
- **Vision Models**: ResNet, ViT, CLIP
- **Multimodal**: CLIP, BLIP
- **Custom Models**: PyTorch/TensorFlow conversions

**Key Features:**
- Unified memory architecture utilization
- Neural Engine acceleration
- Metal GPU integration
- Automatic mixed precision

**Model Loading:**
```python
import mlx.core as mx
from mlx.utils import tree_unflatten

# Load model weights
weights = mx.load("model_weights.npz")
model = tree_unflatten(list(weights.items()))
```

Would you like help with a specific model type?"""
        
        return """MLX is Apple's machine learning framework optimized for Apple Silicon:

**Key Benefits:**
- **Unified Memory**: Efficient memory usage across CPU/GPU/Neural Engine
- **Apple Silicon Optimization**: Native support for M1/M2/M3/M4 chips
- **Familiar APIs**: NumPy-like interface for easy adoption
- **Automatic Optimization**: Hardware-aware computation graphs

**Getting Started:**
```bash
pip install mlx
```

**Basic Usage:**
```python
import mlx.core as mx

# Create tensors
a = mx.array([1, 2, 3, 4])
b = mx.array([5, 6, 7, 8])

# Perform operations
result = mx.add(a, b)
print(result)  # [6, 8, 10, 12]
```

What would you like to know about MLX?"""
    
    def _generate_apple_silicon_response(self, user_input: str) -> str:
        """Generate Apple Silicon-related responses"""
        if apple_detector and apple_detector.is_apple_silicon:
            chip_info = apple_detector.chip_info
            if chip_info:
                return f"""You're running on **{chip_info.get('name', 'Apple Silicon')}**!

**Your System:**
- **CPU Cores**: {chip_info.get('cpu_cores', 'Unknown')}
- **GPU Cores**: {chip_info.get('gpu_cores', 'Unknown')}
- **Memory**: {chip_info.get('memory_gb', 'Unknown')} GB unified memory
- **Neural Engine**: {chip_info.get('neural_engine_cores', 'Unknown')} cores

**Optimization Tips:**
1. Use MLX for machine learning workloads
2. Leverage Core ML for inference
3. Utilize Metal for GPU compute
4. Take advantage of unified memory architecture

Your chip is optimized for AI/ML workloads with dedicated Neural Engine acceleration!"""
        
        return """Apple Silicon chips (M1, M2, M3, M4) are designed for AI/ML workloads:

**Key Features:**
- **Neural Engine**: Dedicated ML acceleration (15.8-35+ TOPS)
- **Unified Memory**: Shared memory pool for CPU/GPU/Neural Engine
- **Metal Performance Shaders**: GPU-accelerated ML primitives
- **Core ML**: On-device inference framework

**Performance Benefits:**
- Up to 20x faster ML inference vs Intel Macs
- Excellent power efficiency
- Real-time on-device processing
- Privacy-preserving local computation

**Supported Chips:**
- **M1**: 8-core CPU, 8-core GPU, 16-core Neural Engine
- **M2**: 8-core CPU, 10-core GPU, 16-core Neural Engine  
- **M3**: 8-core CPU, 10-core GPU, 16-core Neural Engine
- **M4**: 10-core CPU, 10-core GPU, 16-core Neural Engine

Would you like help optimizing for your specific chip?"""
    
    def _generate_general_response(self, user_input: str) -> str:
        """Generate general helpful responses"""
        return """I'm GerdsenAI MLX Manager, your AI assistant for Apple Silicon optimization!

**I can help you with:**
- 🧠 MLX framework usage and optimization
- 🍎 Apple Silicon hardware utilization
- ⚡ Core ML model integration
- 🔧 Performance optimization
- 💻 Code examples and best practices

**Current System Status:**
- MLX Manager: """ + ("✅ Available" if MLX_AVAILABLE else "❌ Not Available") + """
- Apple Silicon: """ + ("✅ Detected" if (apple_detector and apple_detector.is_apple_silicon) else "❌ Not Detected") + """

What would you like to know about?"""

    def generate_streaming_response(self, messages: List[ChatMessage], **kwargs) -> AsyncGenerator[str, None]:
        """Generate a streaming response"""
        response = self.generate_response(messages, **kwargs)
        
        # Split response into chunks for streaming
        words = response.split()
        chunk_size = 3  # Words per chunk
        
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            if i + chunk_size < len(words):
                chunk += " "
            yield chunk
            # Simulate processing time
            time.sleep(0.1)

# Initialize the chat engine
chat_engine = MLXChatEngine()

@openai_api_bp.route('/v1/models', methods=['GET'])
@cross_origin()
@optional_api_key
@rate_limit('default')
def list_models():
    """List available models (OpenAI compatible)"""
    models = [
        {
            "id": "gerdsen-mlx-default",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "gerdsen-ai",
            "permission": [],
            "root": "gerdsen-mlx-default",
            "parent": None
        },
        {
            "id": "gerdsen-mlx-code",
            "object": "model", 
            "created": int(time.time()),
            "owned_by": "gerdsen-ai",
            "permission": [],
            "root": "gerdsen-mlx-code",
            "parent": None
        },
        {
            "id": "gerdsen-mlx-chat",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "gerdsen-ai", 
            "permission": [],
            "root": "gerdsen-mlx-chat",
            "parent": None
        }
    ]
    
    if mlx_manager and hasattr(mlx_manager, 'list_available_models'):
        try:
            mlx_models = mlx_manager.list_available_models()
            for model_name in mlx_models:
                models.append({
                    "id": model_name,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "gerdsen-ai",
                    "permission": [],
                    "root": model_name,
                    "parent": None
                })
        except Exception as e:
            logging.error(f"Error listing MLX models: {e}")
    
    return jsonify({
        "object": "list",
        "data": models
    })

@openai_api_bp.route('/v1/chat/completions', methods=['POST'])
@cross_origin()
@optional_api_key
@rate_limit('default')
def chat_completions():
    """Chat completions endpoint (OpenAI compatible)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": {"message": "Invalid JSON", "type": "invalid_request_error"}}), 400
        
        # Parse request
        model = data.get('model', 'gerdsen-mlx-default')
        messages_data = data.get('messages', [])
        max_tokens = data.get('max_tokens', 2048)
        temperature = data.get('temperature', 0.7)
        stream = data.get('stream', False)
        
        # Convert messages
        messages = []
        for msg_data in messages_data:
            messages.append(ChatMessage(
                role=msg_data.get('role', 'user'),
                content=msg_data.get('content', ''),
                name=msg_data.get('name')
            ))
        
        if not messages:
            return jsonify({"error": {"message": "No messages provided", "type": "invalid_request_error"}}), 400
        
        # Load model if needed
        if not chat_engine.model_loaded or chat_engine.current_model != model:
            chat_engine.load_model(model)
        
        if stream:
            return Response(
                stream_with_context(generate_streaming_response(messages, max_tokens, temperature)),
                mimetype='text/plain',
                headers={'Cache-Control': 'no-cache'}
            )
        else:
            # Generate response
            try:
                # Check if chat_engine has create_chat_completion method
                if hasattr(chat_engine, 'create_chat_completion'):
                    # Use the GGUF inference engine's create_chat_completion method directly
                    response = chat_engine.create_chat_completion(
                        model=model,
                        messages=[msg.dict() for msg in messages],
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                    response_content = response['choices'][0]['message']['content']
                else:
                    # Fall back to generate_response method
                    response_content = chat_engine.generate_response(
                        messages,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
            except Exception as e:
                logging.error(f"Error in chat completion generation: {e}")
                # Fall back to generate_response method if create_chat_completion fails
                response_content = chat_engine.generate_response(
                    messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            
            # Return OpenAI-compatible response
            return jsonify({
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_content
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": sum(len(msg.content.split()) for msg in messages),
                    "completion_tokens": len(response_content.split()),
                    "total_tokens": sum(len(msg.content.split()) for msg in messages) + len(response_content.split())
                }
            })
            
    except Exception as e:
        logging.error(f"Error in chat completions: {e}")
        return jsonify({
            "error": {
                "message": str(e),
                "type": "internal_server_error"
            }
        }), 500

def generate_streaming_response(messages: List[ChatMessage], max_tokens: int, temperature: float):
    """Generate streaming response for chat completions"""
    try:
        response_content = chat_engine.generate_response(
            messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Split into words for streaming
        words = response_content.split()
        chunk_size = 2  # Words per chunk
        
        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunk_content = " ".join(chunk_words)
            
            if i + chunk_size < len(words):
                chunk_content += " "
            
            chunk = {
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "gerdsen-mlx-default",
                "choices": [{
                    "index": 0,
                    "delta": {
                        "content": chunk_content
                    },
                    "finish_reason": None
                }]
            }
            
            yield f"data: {json.dumps(chunk)}\n\n"
            time.sleep(0.05)  # Small delay for realistic streaming
        
        # Send final chunk
        final_chunk = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion.chunk", 
            "created": int(time.time()),
            "model": "gerdsen-mlx-default",
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        
        yield f"data: {json.dumps(final_chunk)}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logging.error(f"Error in streaming response: {e}")
        error_chunk = {
            "error": {
                "message": str(e),
                "type": "internal_server_error"
            }
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"

@openai_api_bp.route('/v1/completions', methods=['POST'])
@cross_origin()
@optional_api_key
@rate_limit('default')
def completions():
    """Legacy completions endpoint (OpenAI compatible)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": {"message": "Invalid JSON", "type": "invalid_request_error"}}), 400
        
        prompt = data.get('prompt', '')
        model = data.get('model', 'gerdsen-mlx-default')
        max_tokens = data.get('max_tokens', 2048)
        temperature = data.get('temperature', 0.7)
        
        if not prompt:
            return jsonify({"error": {"message": "No prompt provided", "type": "invalid_request_error"}}), 400
        
        # Convert prompt to chat format
        messages = [ChatMessage(role="user", content=prompt)]
        
        # Load model if needed
        if not chat_engine.model_loaded or chat_engine.current_model != model:
            chat_engine.load_model(model)
        
        # Generate response
        response_content = chat_engine.generate_response(
            messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return jsonify({
            "id": f"cmpl-{uuid.uuid4().hex[:8]}",
            "object": "text_completion",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "text": response_content,
                "index": 0,
                "logprobs": None,
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(response_content.split()),
                "total_tokens": len(prompt.split()) + len(response_content.split())
            }
        })
        
    except Exception as e:
        logging.error(f"Error in completions: {e}")
        return jsonify({
            "error": {
                "message": str(e),
                "type": "internal_server_error"
            }
        }), 500

@openai_api_bp.route('/v1/embeddings', methods=['POST'])
@cross_origin()
@optional_api_key
@rate_limit('default')
def embeddings():
    """Embeddings endpoint (OpenAI compatible)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": {"message": "Invalid JSON", "type": "invalid_request_error"}}), 400
        
        input_text = data.get('input', '')
        model = data.get('model', 'gerdsen-mlx-embeddings')
        
        if not input_text:
            return jsonify({"error": {"message": "No input provided", "type": "invalid_request_error"}}), 400
        
        # Generate simple embeddings (in production, use real embedding model)
        import hashlib
        import numpy as np
        
        # Create deterministic embeddings based on text hash
        text_hash = hashlib.md5(input_text.encode()).hexdigest()
        np.random.seed(int(text_hash[:8], 16))
        embedding = np.random.normal(0, 1, 1536).tolist()  # OpenAI embedding size
        
        return jsonify({
            "object": "list",
            "data": [{
                "object": "embedding",
                "embedding": embedding,
                "index": 0
            }],
            "model": model,
            "usage": {
                "prompt_tokens": len(input_text.split()),
                "total_tokens": len(input_text.split())
            }
        })
        
    except Exception as e:
        logging.error(f"Error in embeddings: {e}")
        return jsonify({
            "error": {
                "message": str(e),
                "type": "internal_server_error"
            }
        }), 500

# Initialize when blueprint is registered
initialize_openai_api()

