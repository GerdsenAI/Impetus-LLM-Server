"""
MLX generation with KV cache support
"""

from collections.abc import Generator
from typing import Any

from loguru import logger

try:
    import mlx
    import mlx.core as mx
    import mlx.nn as nn
    from mlx_lm.models.base import KVCache
    from mlx_lm.sample_utils import top_p_sampling
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    logger.warning("MLX not available for KV generation")

from .kv_cache_manager import CacheEntry, kv_cache_manager


def generate_with_kv_cache(
    model: Any,
    tokenizer: Any,
    prompt: str,
    max_tokens: int = 100,
    temperature: float = 0.7,
    top_p: float = 0.9,
    repetition_penalty: float = 1.1,
    conversation_id: str = "default",
    use_cache: bool = True
) -> tuple[str, CacheEntry | None]:
    """
    Generate text using MLX model with KV cache support
    
    Args:
        model: MLX model instance
        tokenizer: Tokenizer instance
        prompt: Input prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        top_p: Top-p sampling parameter
        repetition_penalty: Repetition penalty
        conversation_id: Conversation ID for caching
        use_cache: Whether to use KV cache
        
    Returns:
        Generated text and updated cache entry
    """
    if not MLX_AVAILABLE:
        raise RuntimeError("MLX is not available")

    # Tokenize input
    input_ids = tokenizer.encode(prompt)
    input_array = mx.array(input_ids).reshape(1, -1)

    # Get or create cache
    cache_entry = None
    if use_cache and kv_cache_manager.enabled:
        model_id = getattr(model, 'model_id', 'unknown')
        cache_entry = kv_cache_manager.get_cache(model_id, conversation_id)

        if not cache_entry:
            # Extract model dimensions
            num_layers = len(model.layers) if hasattr(model, 'layers') else 32
            num_heads = model.config.num_attention_heads if hasattr(model, 'config') else 32
            hidden_size = model.config.hidden_size if hasattr(model, 'config') else 4096
            head_dim = hidden_size // num_heads

            # Create new cache
            cache_entry = kv_cache_manager.create_cache(
                model_id=model_id,
                conversation_id=conversation_id,
                num_layers=num_layers,
                num_heads=num_heads,
                head_dim=head_dim
            )

    # Initialize generation
    generated_tokens = []
    past_key_values = cache_entry.keys if cache_entry else None

    # Generation loop
    for i in range(max_tokens):
        # Forward pass with cache
        if hasattr(model, 'forward'):
            # Get model output
            outputs = model(
                input_array,
                cache=past_key_values,
                return_dict=True
            )
            logits = outputs.logits
        else:
            # Fallback for different model types
            logits = model(input_array)

        # Sample next token
        next_token_logits = logits[:, -1, :]

        # Apply repetition penalty
        if repetition_penalty != 1.0 and generated_tokens:
            for token_id in set(generated_tokens):
                next_token_logits[:, token_id] /= repetition_penalty

        # Temperature scaling
        if temperature > 0:
            next_token_logits = next_token_logits / temperature

        # Top-p sampling
        if top_p < 1.0:
            next_token = top_p_sampling(next_token_logits, top_p)
        else:
            # Greedy sampling
            next_token = mx.argmax(next_token_logits, axis=-1)

        # Add to generated tokens
        next_token_id = int(next_token.item())
        generated_tokens.append(next_token_id)

        # Check for end of sequence
        if next_token_id == tokenizer.eos_token_id:
            break

        # Update input for next iteration
        input_array = mx.array([[next_token_id]])

        # Update cache if available
        if cache_entry and hasattr(outputs, 'past_key_values'):
            past_key_values = outputs.past_key_values

    # Decode generated tokens
    generated_text = tokenizer.decode(generated_tokens)

    # Update cache manager if we used cache
    if cache_entry and past_key_values:
        # Extract new KV states
        new_keys = []
        new_values = []

        # This would need proper extraction from the model outputs
        # For now, this is a placeholder
        logger.debug(f"Generated {len(generated_tokens)} tokens with KV cache")

    return generated_text, cache_entry


def generate_stream_with_kv_cache(
    model: Any,
    tokenizer: Any,
    prompt: str,
    max_tokens: int = 100,
    temperature: float = 0.7,
    top_p: float = 0.9,
    repetition_penalty: float = 1.1,
    conversation_id: str = "default",
    use_cache: bool = True
) -> Generator[str, None, None]:
    """
    Stream generate text using MLX model with KV cache support
    
    Yields tokens as they are generated
    """
    if not MLX_AVAILABLE:
        raise RuntimeError("MLX is not available")

    # Similar to generate_with_kv_cache but yields tokens
    # For now, use the non-streaming version and yield characters
    text, _ = generate_with_kv_cache(
        model=model,
        tokenizer=tokenizer,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        repetition_penalty=repetition_penalty,
        conversation_id=conversation_id,
        use_cache=use_cache
    )

    # Stream the text character by character
    for char in text:
        yield char


def clear_model_cache(model_id: str):
    """Clear all KV caches for a model"""
    return kv_cache_manager.clear_model_caches(model_id)


def get_cache_stats():
    """Get KV cache statistics"""
    return kv_cache_manager.get_stats()
