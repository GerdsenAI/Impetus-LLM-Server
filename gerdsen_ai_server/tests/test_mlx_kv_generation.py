"""
Unit tests for MLX generation with KV cache (inference/mlx_kv_generation.py).
"""

from unittest.mock import MagicMock, patch

import pytest

from src.inference.mlx_kv_generation import clear_model_cache, get_cache_stats


class TestClearModelCache:
    """Tests for clear_model_cache function."""

    @patch("src.inference.mlx_kv_generation.kv_cache_manager")
    def test_delegates_to_cache_manager(self, mock_manager):
        """clear_model_cache calls kv_cache_manager.clear_model_caches."""
        mock_manager.clear_model_caches.return_value = 3
        result = clear_model_cache("test-model")
        mock_manager.clear_model_caches.assert_called_once_with("test-model")
        assert result == 3


class TestGetCacheStats:
    """Tests for get_cache_stats function."""

    @patch("src.inference.mlx_kv_generation.kv_cache_manager")
    def test_delegates_to_cache_manager(self, mock_manager):
        """get_cache_stats calls kv_cache_manager.get_stats."""
        mock_manager.get_stats.return_value = {"enabled": True, "num_caches": 2}
        result = get_cache_stats()
        mock_manager.get_stats.assert_called_once()
        assert result["enabled"] is True
        assert result["num_caches"] == 2


class TestGenerateWithKvCache:
    """Tests for generate_with_kv_cache function (requires MLX mocking)."""

    @patch("src.inference.mlx_kv_generation.MLX_AVAILABLE", False)
    def test_raises_without_mlx(self):
        """generate_with_kv_cache raises RuntimeError when MLX unavailable."""
        from src.inference.mlx_kv_generation import generate_with_kv_cache

        with pytest.raises(RuntimeError, match="MLX is not available"):
            generate_with_kv_cache(
                model=MagicMock(),
                tokenizer=MagicMock(),
                prompt="hello",
            )

    @patch("src.inference.mlx_kv_generation.MLX_AVAILABLE", False)
    def test_stream_raises_without_mlx(self):
        """generate_stream_with_kv_cache raises RuntimeError when MLX unavailable."""
        from src.inference.mlx_kv_generation import generate_stream_with_kv_cache

        with pytest.raises(RuntimeError, match="MLX is not available"):
            list(
                generate_stream_with_kv_cache(
                    model=MagicMock(),
                    tokenizer=MagicMock(),
                    prompt="hello",
                )
            )
