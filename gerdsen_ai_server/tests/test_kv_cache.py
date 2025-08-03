"""
Unit tests for KV cache manager
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Mock MLX if not available
try:
    import mlx.core as mx
except ImportError:
    mx = MagicMock()

from src.inference.kv_cache_manager import CacheEntry, KVCacheManager


class TestKVCacheManager:
    """Test KV cache manager functionality"""

    @pytest.fixture
    def cache_manager(self):
        """Create a test cache manager"""
        return KVCacheManager(max_memory_gb=1.0, max_conversations=5)

    @pytest.fixture
    def mock_mlx_array(self):
        """Create mock MLX array"""
        array = MagicMock()
        array.shape = (1, 32, 100, 128)  # batch, heads, seq_len, head_dim
        array.nbytes = np.prod(array.shape) * 4  # float32
        return array

    def test_cache_manager_init(self):
        """Test cache manager initialization"""
        manager = KVCacheManager(max_memory_gb=2.0, max_conversations=10)
        assert manager.max_memory_mb == 2048
        assert manager.max_conversations == 10
        assert len(manager.caches) == 0
        assert manager.total_memory_mb == 0.0

    def test_cache_key_generation(self, cache_manager):
        """Test cache key generation"""
        key = cache_manager.get_cache_key("model-1", "conv-1")
        assert key == "model-1:conv-1"

    def test_has_cache(self, cache_manager):
        """Test cache existence check"""
        assert not cache_manager.has_cache("model-1", "conv-1")

        # Add a cache entry
        cache_manager.caches["model-1:conv-1"] = MagicMock()
        assert cache_manager.has_cache("model-1", "conv-1")

    @patch('src.inference.kv_cache_manager.MLX_AVAILABLE', True)
    @patch('src.inference.kv_cache_manager.mx')
    def test_create_cache(self, mock_mx, cache_manager):
        """Test cache creation"""
        # Mock mx.zeros
        mock_mx.zeros.return_value = self.mock_mlx_array()

        cache = cache_manager.create_cache(
            model_id="test-model",
            conversation_id="test-conv",
            num_layers=12,
            num_heads=32,
            head_dim=128,
            initial_length=0
        )

        assert cache.model_id == "test-model"
        assert cache.conversation_id == "test-conv"
        assert len(cache.keys) == 12
        assert len(cache.values) == 12
        assert cache.sequence_length == 0

        # Check that cache was stored
        assert cache_manager.has_cache("test-model", "test-conv")

    def test_memory_calculation(self, mock_mlx_array):
        """Test memory calculation for cache entry"""
        cache = CacheEntry(
            model_id="test",
            conversation_id="test",
            keys=[mock_mlx_array] * 12,
            values=[mock_mlx_array] * 12,
            sequence_length=100
        )

        memory_mb = cache.calculate_memory()
        # 24 arrays * (1 * 32 * 100 * 128) * 4 bytes / (1024 * 1024)
        expected_mb = 24 * np.prod(mock_mlx_array.shape) * 4 / (1024 * 1024)
        assert abs(memory_mb - expected_mb) < 0.1

    @patch('src.inference.kv_cache_manager.MLX_AVAILABLE', True)
    @patch('src.inference.kv_cache_manager.mx')
    def test_update_cache(self, mock_mx, cache_manager):
        """Test cache update"""
        # Create initial cache
        mock_mx.zeros.return_value = self.mock_mlx_array()
        cache = cache_manager.create_cache(
            model_id="test-model",
            conversation_id="test-conv",
            num_layers=1,
            num_heads=32,
            head_dim=128,
            initial_length=10
        )

        # Mock concatenate
        new_array = MagicMock()
        new_array.shape = (1, 32, 20, 128)  # 20 new tokens

        concat_result = MagicMock()
        concat_result.shape = (1, 32, 30, 128)  # 10 + 20 tokens
        mock_mx.concatenate.return_value = concat_result

        # Update cache
        updated_cache = cache_manager.update_cache(
            model_id="test-model",
            conversation_id="test-conv",
            new_keys=[new_array],
            new_values=[new_array]
        )

        assert updated_cache.sequence_length == 30
        mock_mx.concatenate.assert_called()

    def test_clear_cache(self, cache_manager):
        """Test clearing specific cache"""
        # Add a cache
        cache_entry = MagicMock()
        cache_entry.memory_mb = 100.0
        cache_manager.caches["model-1:conv-1"] = cache_entry
        cache_manager.total_memory_mb = 100.0

        # Clear it
        success = cache_manager.clear_cache("model-1", "conv-1")
        assert success
        assert not cache_manager.has_cache("model-1", "conv-1")
        assert cache_manager.total_memory_mb == 0.0

    def test_clear_model_caches(self, cache_manager):
        """Test clearing all caches for a model"""
        # Add multiple caches
        cache1 = MagicMock()
        cache1.memory_mb = 50.0
        cache2 = MagicMock()
        cache2.memory_mb = 60.0

        cache_manager.caches["model-1:conv-1"] = cache1
        cache_manager.caches["model-1:conv-2"] = cache2
        cache_manager.caches["model-2:conv-1"] = MagicMock()
        cache_manager.total_memory_mb = 110.0

        # Clear model-1 caches
        cleared = cache_manager.clear_model_caches("model-1")
        assert cleared == 2
        assert len(cache_manager.caches) == 1
        assert "model-2:conv-1" in cache_manager.caches
        assert cache_manager.total_memory_mb == 0.0

    def test_lru_eviction(self, cache_manager):
        """Test LRU cache eviction"""
        import time

        # Set small limits
        cache_manager.max_conversations = 2

        # Add caches with different access times
        cache1 = CacheEntry(
            model_id="model",
            conversation_id="conv1",
            keys=[],
            values=[],
            sequence_length=0,
            last_accessed=time.time() - 10
        )
        cache1.memory_mb = 100.0

        cache2 = CacheEntry(
            model_id="model",
            conversation_id="conv2",
            keys=[],
            values=[],
            sequence_length=0,
            last_accessed=time.time() - 5
        )
        cache2.memory_mb = 100.0

        cache_manager.caches["model:conv1"] = cache1
        cache_manager.caches["model:conv2"] = cache2
        cache_manager.total_memory_mb = 200.0

        # Add third cache - should evict conv1 (oldest)
        cache_manager._maybe_evict_caches()

        # Manually trigger eviction by adding new cache
        cache3 = CacheEntry(
            model_id="model",
            conversation_id="conv3",
            keys=[],
            values=[],
            sequence_length=0
        )
        cache3.memory_mb = 100.0
        cache_manager.caches["model:conv3"] = cache3
        cache_manager._maybe_evict_caches()

        assert "model:conv1" not in cache_manager.caches
        assert "model:conv2" in cache_manager.caches
        assert "model:conv3" in cache_manager.caches

    def test_get_stats(self, cache_manager):
        """Test getting cache statistics"""
        # Add a cache
        cache = CacheEntry(
            model_id="model",
            conversation_id="conv",
            keys=[],
            values=[],
            sequence_length=100
        )
        cache.memory_mb = 50.0
        cache_manager.caches["model:conv"] = cache
        cache_manager.total_memory_mb = 50.0

        stats = cache_manager.get_stats()

        assert stats['num_caches'] == 1
        assert stats['total_memory_mb'] == 50.0
        assert stats['max_memory_mb'] == 1024.0
        assert len(stats['conversations']) == 1
        assert stats['conversations'][0]['sequence_length'] == 100


class TestCacheEntry:
    """Test CacheEntry functionality"""

    def test_cache_entry_creation(self):
        """Test creating a cache entry"""
        entry = CacheEntry(
            model_id="test-model",
            conversation_id="test-conv",
            keys=[],
            values=[],
            sequence_length=0
        )

        assert entry.model_id == "test-model"
        assert entry.conversation_id == "test-conv"
        assert entry.sequence_length == 0
        assert entry.memory_mb == 0.0

    def test_update_access_time(self):
        """Test updating access time"""
        import time

        entry = CacheEntry(
            model_id="test",
            conversation_id="test",
            keys=[],
            values=[],
            sequence_length=0
        )

        old_time = entry.last_accessed
        time.sleep(0.01)  # Small delay
        entry.update_access_time()

        assert entry.last_accessed > old_time


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
