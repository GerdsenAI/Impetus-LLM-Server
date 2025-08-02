"""
MLX model loader for Apple Silicon optimization
"""

import gc
from pathlib import Path
from typing import Dict, Any, List, Optional, Generator
import json
from loguru import logger

from .base import BaseModelLoader, BaseModel, ModelLoadError, ModelNotFoundError, InferenceError
from ..config.settings import settings
from ..inference.kv_cache_manager import kv_cache_manager, CacheEntry
from ..services.model_warmup import model_warmup_service

# MLX imports with error handling
try:
    import mlx
    import mlx.core as mx
    import mlx.nn as nn
    from mlx_lm import load, generate
    from mlx_lm.tokenizer_utils import load_tokenizer
    MLX_AVAILABLE = True
except ImportError as e:
    logger.warning(f"MLX not available: {e}")
    MLX_AVAILABLE = False


class MLXModel(BaseModel):
    """MLX model implementation"""
    
    def __init__(self, model_id: str, model_path: Path):
        super().__init__(model_id, model_path)
        self.device = "gpu"  # MLX uses unified memory on Apple Silicon
        self.model_instance = None
        self.tokenizer_instance = None
        self.adapter_path = None
        self.supports_kv_cache = True
        self.model_config = None
        
    def load(self, **kwargs) -> None:
        """Load MLX model into memory"""
        if not MLX_AVAILABLE:
            raise ModelLoadError("MLX is not installed. Please install mlx and mlx-lm.")
        
        try:
            logger.info(f"Loading MLX model: {self.model_id}")
            
            # Load model and tokenizer
            if self.model_path.exists():
                # Load from local path
                self.model_instance, self.tokenizer_instance = load(
                    str(self.model_path),
                    tokenizer_config=kwargs.get('tokenizer_config', {}),
                    model_config=kwargs.get('model_config', {}),
                    adapter_path=kwargs.get('adapter_path'),
                    lazy=kwargs.get('lazy', True)
                )
            else:
                # Load from HuggingFace Hub
                self.model_instance, self.tokenizer_instance = load(
                    self.model_id,
                    tokenizer_config=kwargs.get('tokenizer_config', {}),
                    model_config=kwargs.get('model_config', {}),
                    adapter_path=kwargs.get('adapter_path'),
                    lazy=kwargs.get('lazy', True)
                )
            
            # Load config if available
            config_path = self.model_path / "config.json" if self.model_path.exists() else None
            if config_path and config_path.exists():
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
                    self.model_config = self.config
            
            # Try to get model config from the model instance if not loaded from file
            if not self.model_config and hasattr(self.model_instance, 'config'):
                self.model_config = self.model_instance.config
            
            self.loaded = True
            logger.info(f"Successfully loaded MLX model: {self.model_id}")
            
        except Exception as e:
            logger.error(f"Failed to load MLX model {self.model_id}: {e}")
            raise ModelLoadError(f"Failed to load model: {e}")
    
    def unload(self) -> None:
        """Unload model from memory"""
        if self.loaded:
            logger.info(f"Unloading MLX model: {self.model_id}")
            
            # Clear model and tokenizer
            self.model_instance = None
            self.tokenizer_instance = None
            
            # Force garbage collection
            gc.collect()
            
            # MLX specific cleanup
            if MLX_AVAILABLE:
                mx.metal.clear_cache()
            
            self.loaded = False
            logger.info(f"Successfully unloaded MLX model: {self.model_id}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt with optional KV cache support"""
        if not self.loaded:
            raise InferenceError("Model is not loaded")
        
        try:
            # Extract generation parameters
            max_tokens = kwargs.get('max_tokens', settings.inference.max_tokens)
            temperature = kwargs.get('temperature', settings.inference.temperature)
            top_p = kwargs.get('top_p', settings.inference.top_p)
            repetition_penalty = kwargs.get('repetition_penalty', settings.inference.repetition_penalty)
            
            # KV cache parameters
            use_cache = kwargs.get('use_cache', settings.inference.use_cache)
            conversation_id = kwargs.get('conversation_id', 'default')
            
            # Check context window limits
            prompt_tokens = self.tokenize(prompt)
            context_length = self.config.get('max_position_embeddings', 2048) if self.config else 2048
            
            if len(prompt_tokens) > context_length:
                raise InferenceError(f"Prompt exceeds context window ({len(prompt_tokens)} > {context_length})")
            
            # Adjust max_tokens if it would exceed context window
            available_tokens = context_length - len(prompt_tokens)
            if max_tokens > available_tokens:
                logger.warning(f"Reducing max_tokens from {max_tokens} to {available_tokens} to fit context window")
                max_tokens = available_tokens
            
            # Check if we should use KV cache
            cache_entry = None
            if use_cache and self.supports_kv_cache and kv_cache_manager.enabled:
                cache_entry = kv_cache_manager.get_cache(self.model_id, conversation_id)
                if cache_entry:
                    logger.debug(f"Using KV cache for conversation {conversation_id}")
            
            # Generate response
            # Note: The actual KV cache integration would require modifying the mlx_lm.generate function
            # or using a custom generation loop. For now, we use the standard generation.
            response = generate(
                self.model_instance,
                self.tokenizer_instance,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
                verbose=False
            )
            
            # Update cache if needed (placeholder for now)
            if use_cache and self.supports_kv_cache and kv_cache_manager.enabled:
                # In a real implementation, we would extract and store the KV states here
                pass
            
            return response
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            raise InferenceError(f"Failed to generate text: {e}")
    
    def generate_stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Generate text in streaming mode with optional KV cache support"""
        if not self.loaded:
            raise InferenceError("Model is not loaded")
        
        try:
            # Extract generation parameters
            max_tokens = kwargs.get('max_tokens', settings.inference.max_tokens)
            temperature = kwargs.get('temperature', settings.inference.temperature)
            top_p = kwargs.get('top_p', settings.inference.top_p)
            repetition_penalty = kwargs.get('repetition_penalty', settings.inference.repetition_penalty)
            
            # KV cache parameters
            use_cache = kwargs.get('use_cache', settings.inference.use_cache)
            conversation_id = kwargs.get('conversation_id', 'default')
            
            # Check if mlx_lm has streaming support
            if hasattr(generate, 'stream') or 'stream' in dir(self.model_instance):
                # Use native streaming if available
                logger.info("Using native MLX streaming generation")
                # This would be the ideal implementation once mlx_lm supports it
                pass
            
            # Fallback: Generate in chunks for a streaming-like experience
            # This is more efficient than generating the full response at once
            prompt_tokens = self.tokenize(prompt)
            generated_tokens = []
            previous_text = ""
            
            # Generate tokens in small batches
            batch_size = 10  # Generate 10 tokens at a time
            for i in range(0, max_tokens, batch_size):
                current_max = min(i + batch_size, max_tokens)
                
                # Generate up to current_max tokens
                response = generate(
                    self.model_instance,
                    self.tokenizer_instance,
                    prompt=prompt,
                    max_tokens=current_max,
                    temperature=temperature,
                    top_p=top_p,
                    repetition_penalty=repetition_penalty,
                    verbose=False
                )
                
                # Extract only the new tokens
                if response.startswith(previous_text):
                    new_text = response[len(previous_text):]
                    previous_text = response
                    
                    # Yield the new text
                    for char in new_text:
                        yield char
                    
                    # Check if generation is complete
                    if len(new_text) == 0 or response.endswith(('.', '!', '?', '\n')):
                        break
                else:
                    # Shouldn't happen, but handle gracefully
                    logger.warning("Unexpected response format in streaming generation")
                    yield response[len(previous_text):]
                    break
                
        except Exception as e:
            logger.error(f"Streaming generation error: {e}")
            raise InferenceError(f"Failed to generate text stream: {e}")
    
    def tokenize(self, text: str) -> List[int]:
        """Tokenize text"""
        if not self.loaded or not self.tokenizer_instance:
            raise InferenceError("Model or tokenizer not loaded")
        
        return self.tokenizer_instance.encode(text)
    
    def detokenize(self, tokens: List[int]) -> str:
        """Detokenize tokens"""
        if not self.loaded or not self.tokenizer_instance:
            raise InferenceError("Model or tokenizer not loaded")
        
        return self.tokenizer_instance.decode(tokens)
    
    def get_model_dimensions(self) -> Dict[str, int]:
        """Get model dimensions for KV cache initialization"""
        if not self.model_config:
            return {
                'num_layers': 32,  # Default for 7B models
                'num_heads': 32,
                'head_dim': 128,
                'hidden_size': 4096
            }
        
        # Extract dimensions from config
        num_layers = self.model_config.get('num_hidden_layers', 32)
        num_heads = self.model_config.get('num_attention_heads', 32)
        hidden_size = self.model_config.get('hidden_size', 4096)
        head_dim = hidden_size // num_heads
        
        return {
            'num_layers': num_layers,
            'num_heads': num_heads,
            'head_dim': head_dim,
            'hidden_size': hidden_size
        }
    
    def clear_conversation_cache(self, conversation_id: str = 'default') -> bool:
        """Clear KV cache for a specific conversation"""
        if kv_cache_manager.enabled:
            return kv_cache_manager.clear_cache(self.model_id, conversation_id)
        return False


class MLXModelLoader(BaseModelLoader):
    """Model loader for MLX models"""
    
    def __init__(self):
        super().__init__()
        if not MLX_AVAILABLE:
            logger.warning("MLX is not available. MLX model loading will fail.")
    
    def load_model(self, model_id: str, **kwargs) -> MLXModel:
        """Load an MLX model with optional warmup"""
        # Check if already loaded
        if self.is_model_loaded(model_id):
            logger.info(f"Model {model_id} is already loaded")
            return self.loaded_models[model_id]
        
        # Determine model path
        if '/' in model_id:
            # HuggingFace model ID
            model_path = settings.model.models_dir / model_id.replace('/', '_')
        else:
            # Local model
            model_path = settings.model.models_dir / model_id
        
        # Create model instance
        model = MLXModel(model_id, model_path)
        
        # Load the model
        model.load(**kwargs)
        
        # Store in loaded models
        self.loaded_models[model_id] = model
        self.model_configs[model_id] = model.config
        
        # Auto-warmup if requested
        if kwargs.get('auto_warmup', False):
            logger.info(f"Auto-warming up model {model_id}")
            warmup_async = kwargs.get('warmup_async', True)
            model_warmup_service.warmup_model(
                model,
                model_id,
                num_prompts=kwargs.get('warmup_prompts', 3),
                async_warmup=warmup_async
            )
        
        return model
    
    def unload_model(self, model_id: str) -> bool:
        """Unload a model"""
        if not self.is_model_loaded(model_id):
            logger.warning(f"Model {model_id} is not loaded")
            return False
        
        try:
            model = self.loaded_models[model_id]
            model.unload()
            
            # Remove from loaded models
            del self.loaded_models[model_id]
            del self.model_configs[model_id]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload model {model_id}: {e}")
            return False
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """List available MLX models"""
        models = []
        
        # Check local models directory
        if settings.model.models_dir.exists():
            for model_dir in settings.model.models_dir.iterdir():
                if model_dir.is_dir() and (model_dir / "config.json").exists():
                    try:
                        with open(model_dir / "config.json", 'r') as f:
                            config = json.load(f)
                        
                        models.append({
                            'id': model_dir.name,
                            'name': config.get('name', model_dir.name),
                            'type': 'mlx',
                            'path': str(model_dir),
                            'loaded': self.is_model_loaded(model_dir.name),
                            'size_gb': sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file()) / (1024 ** 3)
                        })
                    except Exception as e:
                        logger.error(f"Error reading model config for {model_dir}: {e}")
        
        # Add loaded HuggingFace models
        for model_id, model in self.loaded_models.items():
            if '/' in model_id:  # HuggingFace model
                models.append({
                    'id': model_id,
                    'name': model_id,
                    'type': 'mlx',
                    'path': 'huggingface',
                    'loaded': True,
                    'size_gb': 0  # Size unknown for HF models
                })
        
        return models
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get model information including warmup status"""
        if self.is_model_loaded(model_id):
            model = self.loaded_models[model_id]
            info = model.get_info()
            
            # Add warmup status
            warmup_status = model_warmup_service.get_warmup_status(model_id)
            if warmup_status:
                info['warmup'] = {
                    'is_warmed': warmup_status.is_warmed,
                    'warmup_time_ms': warmup_status.warmup_time_ms,
                    'last_warmup': warmup_status.last_warmup,
                    'kernel_compilation_time_ms': warmup_status.kernel_compilation_time_ms
                }
            else:
                info['warmup'] = {'is_warmed': False}
            
            return info
        
        # Check if model exists locally
        model_path = settings.model.models_dir / model_id
        if model_path.exists() and (model_path / "config.json").exists():
            try:
                with open(model_path / "config.json", 'r') as f:
                    config = json.load(f)
                
                return {
                    'model_id': model_id,
                    'model_path': str(model_path),
                    'loaded': False,
                    'config': config,
                    'size_gb': sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file()) / (1024 ** 3)
                }
            except Exception as e:
                logger.error(f"Error reading model info for {model_id}: {e}")
        
        raise ModelNotFoundError(f"Model {model_id} not found")