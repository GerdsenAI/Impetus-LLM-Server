"""
KV Cache Manager for MLX models to improve multi-turn conversation performance
"""

import gc
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from loguru import logger

try:
    import mlx
    import mlx.core as mx
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    logger.warning("MLX not available for KV cache")


@dataclass
class CacheEntry:
    """Single cache entry for a conversation"""
    model_id: str
    conversation_id: str
    keys: list[mx.array]  # List of key tensors for each layer
    values: list[mx.array]  # List of value tensors for each layer
    sequence_length: int
    last_accessed: float = field(default_factory=time.time)
    memory_mb: float = 0.0

    def update_access_time(self):
        """Update last accessed time"""
        self.last_accessed = time.time()

    def calculate_memory(self) -> float:
        """Calculate memory usage in MB"""
        total_bytes = 0
        for k, v in zip(self.keys, self.values, strict=False):
            # Each array has shape [batch, heads, seq_len, head_dim]
            total_bytes += k.nbytes if hasattr(k, 'nbytes') else np.prod(k.shape) * 4
            total_bytes += v.nbytes if hasattr(v, 'nbytes') else np.prod(v.shape) * 4
        self.memory_mb = total_bytes / (1024 * 1024)
        return self.memory_mb


class KVCacheManager:
    """
    Manages KV caches for multiple conversations and models.
    Implements LRU eviction and memory management.
    """

    def __init__(self, max_memory_gb: float = 2.0, max_conversations: int = 10):
        """
        Initialize KV cache manager
        
        Args:
            max_memory_gb: Maximum memory to use for caching (GB)
            max_conversations: Maximum number of concurrent conversations
        """
        self.max_memory_mb = max_memory_gb * 1024
        self.max_conversations = max_conversations
        self.caches: dict[str, CacheEntry] = {}
        self.total_memory_mb = 0.0
        self.enabled = MLX_AVAILABLE

        if self.enabled:
            logger.info(f"KV Cache Manager initialized with {max_memory_gb}GB limit")
        else:
            logger.warning("KV Cache Manager disabled - MLX not available")

    def get_cache_key(self, model_id: str, conversation_id: str) -> str:
        """Generate unique cache key"""
        return f"{model_id}:{conversation_id}"

    def has_cache(self, model_id: str, conversation_id: str) -> bool:
        """Check if cache exists for conversation"""
        if not self.enabled:
            return False
        key = self.get_cache_key(model_id, conversation_id)
        return key in self.caches

    def get_cache(self, model_id: str, conversation_id: str) -> CacheEntry | None:
        """
        Get cache entry for conversation
        
        Returns:
            CacheEntry if exists, None otherwise
        """
        if not self.enabled:
            return None

        key = self.get_cache_key(model_id, conversation_id)
        cache = self.caches.get(key)

        if cache:
            cache.update_access_time()
            logger.debug(f"Cache hit for {key}, seq_len: {cache.sequence_length}")

        return cache

    def create_cache(self,
                    model_id: str,
                    conversation_id: str,
                    num_layers: int,
                    num_heads: int,
                    head_dim: int,
                    initial_length: int = 0) -> CacheEntry:
        """
        Create new cache entry
        
        Args:
            model_id: Model identifier
            conversation_id: Conversation identifier
            num_layers: Number of transformer layers
            num_heads: Number of attention heads
            head_dim: Dimension of each attention head
            initial_length: Initial sequence length
            
        Returns:
            New CacheEntry
        """
        if not self.enabled:
            raise RuntimeError("KV cache is not available without MLX")

        # Check if we need to evict caches
        self._maybe_evict_caches()

        # Initialize empty cache tensors
        keys = []
        values = []

        # For now, create zero-initialized tensors
        # In practice, these will be populated during first forward pass
        for _ in range(num_layers):
            # Shape: [batch=1, num_heads, seq_len, head_dim]
            if initial_length > 0:
                k = mx.zeros((1, num_heads, initial_length, head_dim))
                v = mx.zeros((1, num_heads, initial_length, head_dim))
            else:
                # Start with empty tensors that will be concatenated to
                k = mx.zeros((1, num_heads, 0, head_dim))
                v = mx.zeros((1, num_heads, 0, head_dim))
            keys.append(k)
            values.append(v)

        # Create cache entry
        cache = CacheEntry(
            model_id=model_id,
            conversation_id=conversation_id,
            keys=keys,
            values=values,
            sequence_length=initial_length
        )

        # Calculate memory usage
        cache.calculate_memory()

        # Store cache
        key = self.get_cache_key(model_id, conversation_id)
        self.caches[key] = cache
        self.total_memory_mb += cache.memory_mb

        logger.info(f"Created KV cache for {key}, memory: {cache.memory_mb:.1f}MB")

        return cache

    def update_cache(self,
                    model_id: str,
                    conversation_id: str,
                    new_keys: list[mx.array],
                    new_values: list[mx.array],
                    truncate_length: int | None = None) -> CacheEntry:
        """
        Update existing cache with new key-value pairs
        
        Args:
            model_id: Model identifier
            conversation_id: Conversation identifier
            new_keys: New key tensors to append
            new_values: New value tensors to append
            truncate_length: Optional max sequence length (for sliding window)
            
        Returns:
            Updated CacheEntry
        """
        if not self.enabled:
            raise RuntimeError("KV cache is not available without MLX")

        key = self.get_cache_key(model_id, conversation_id)
        cache = self.caches.get(key)

        if not cache:
            raise ValueError(f"No cache found for {key}")

        # Update memory tracking
        old_memory = cache.memory_mb

        # Concatenate new keys and values
        updated_keys = []
        updated_values = []

        for layer_idx, (old_k, old_v, new_k, new_v) in enumerate(
            zip(cache.keys, cache.values, new_keys, new_values, strict=False)
        ):
            # Concatenate along sequence dimension (axis=2)
            updated_k = mx.concatenate([old_k, new_k], axis=2)
            updated_v = mx.concatenate([old_v, new_v], axis=2)

            # Apply truncation if needed (sliding window attention)
            if truncate_length and updated_k.shape[2] > truncate_length:
                start_idx = updated_k.shape[2] - truncate_length
                updated_k = updated_k[:, :, start_idx:, :]
                updated_v = updated_v[:, :, start_idx:, :]

            updated_keys.append(updated_k)
            updated_values.append(updated_v)

        # Update cache
        cache.keys = updated_keys
        cache.values = updated_values
        cache.sequence_length = updated_keys[0].shape[2]
        cache.update_access_time()

        # Recalculate memory
        new_memory = cache.calculate_memory()
        self.total_memory_mb += (new_memory - old_memory)

        logger.debug(f"Updated cache for {key}, new seq_len: {cache.sequence_length}, "
                    f"memory: {old_memory:.1f}MB -> {new_memory:.1f}MB")

        # Check if we need to evict after update
        self._maybe_evict_caches()

        return cache

    def clear_cache(self, model_id: str, conversation_id: str) -> bool:
        """
        Clear cache for specific conversation
        
        Returns:
            True if cache was cleared, False if not found
        """
        key = self.get_cache_key(model_id, conversation_id)
        cache = self.caches.pop(key, None)

        if cache:
            self.total_memory_mb -= cache.memory_mb
            logger.info(f"Cleared cache for {key}, freed {cache.memory_mb:.1f}MB")

            # Force garbage collection
            del cache
            gc.collect()
            if MLX_AVAILABLE:
                mx.metal.clear_cache()

            return True

        return False

    def clear_model_caches(self, model_id: str) -> int:
        """
        Clear all caches for a specific model
        
        Returns:
            Number of caches cleared
        """
        keys_to_remove = [k for k in self.caches.keys() if k.startswith(f"{model_id}:")]

        cleared = 0
        for key in keys_to_remove:
            cache = self.caches.pop(key)
            self.total_memory_mb -= cache.memory_mb
            cleared += 1

        if cleared > 0:
            logger.info(f"Cleared {cleared} caches for model {model_id}")
            gc.collect()
            if MLX_AVAILABLE:
                mx.metal.clear_cache()

        return cleared

    def clear_all_caches(self):
        """Clear all caches"""
        num_caches = len(self.caches)
        self.caches.clear()
        self.total_memory_mb = 0.0

        if num_caches > 0:
            logger.info(f"Cleared all {num_caches} caches")
            gc.collect()
            if MLX_AVAILABLE:
                mx.metal.clear_cache()

    def _maybe_evict_caches(self):
        """Evict caches if memory or count limits exceeded"""
        # Check memory limit
        while self.total_memory_mb > self.max_memory_mb and self.caches:
            self._evict_lru_cache()

        # Check conversation limit
        while len(self.caches) > self.max_conversations:
            self._evict_lru_cache()

    def _evict_lru_cache(self):
        """Evict least recently used cache"""
        if not self.caches:
            return

        # Find LRU cache
        lru_key = min(self.caches.keys(), key=lambda k: self.caches[k].last_accessed)
        cache = self.caches.pop(lru_key)

        self.total_memory_mb -= cache.memory_mb
        logger.info(f"Evicted cache for {lru_key}, freed {cache.memory_mb:.1f}MB")

        # Cleanup
        del cache
        gc.collect()

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        return {
            'enabled': self.enabled,
            'num_caches': len(self.caches),
            'total_memory_mb': self.total_memory_mb,
            'max_memory_mb': self.max_memory_mb,
            'memory_usage_percent': (self.total_memory_mb / self.max_memory_mb * 100) if self.max_memory_mb > 0 else 0,
            'conversations': [
                {
                    'key': key,
                    'model_id': cache.model_id,
                    'conversation_id': cache.conversation_id,
                    'sequence_length': cache.sequence_length,
                    'memory_mb': cache.memory_mb,
                    'age_seconds': time.time() - cache.last_accessed
                }
                for key, cache in self.caches.items()
            ]
        }


# Global KV cache manager instance
kv_cache_manager = KVCacheManager()
