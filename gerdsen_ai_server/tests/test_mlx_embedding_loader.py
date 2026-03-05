"""
Unit tests for MLX GPU embedding model loader (model_loaders/mlx_embedding_loader.py).
"""

from unittest.mock import MagicMock, patch

import pytest
from src.model_loaders.mlx_embedding_loader import MLXEmbeddingModel, MLXEmbeddingModelLoader


class TestMLXEmbeddingModel:
    """Tests for MLXEmbeddingModel class."""

    @pytest.fixture
    def model(self, tmp_path):
        """Create MLXEmbeddingModel instance."""
        return MLXEmbeddingModel(
            model_name="test-model",
            model_path=tmp_path / "test-model",
            dimensions=384,
            max_tokens=128,
            hf_model_id="sentence-transformers/all-MiniLM-L6-v2",
        )

    def test_initial_state_not_loaded(self, model):
        """Model starts in unloaded state."""
        assert model.is_loaded is False

    def test_embed_raises_when_not_loaded(self, model):
        """embed raises EmbeddingError when model not loaded."""
        from src.model_loaders.base import EmbeddingError

        with pytest.raises(EmbeddingError, match="not loaded"):
            model.embed(["test"])

    def test_unload_clears_state(self, model):
        """unload sets model to unloaded state."""
        model._loaded = True
        model._hf_model = MagicMock()
        model._tokenizer = MagicMock()

        model.unload()
        assert model.is_loaded is False
        assert model._hf_model is None
        assert model._tokenizer is None

    def test_get_info_includes_hf_model_id(self, model):
        """get_info returns dict with hf_model_id."""
        info = model.get_info()
        assert info["hf_model_id"] == "sentence-transformers/all-MiniLM-L6-v2"
        assert info["max_seq_length"] == 128
        assert info["model_name"] == "test-model"

    @patch("src.model_loaders.mlx_embedding_loader.MLX_AVAILABLE", False)
    def test_load_raises_without_mlx(self, model):
        """load raises EmbeddingError when MLX not available."""
        from src.model_loaders.base import EmbeddingError

        with pytest.raises(EmbeddingError, match="MLX is not installed"):
            model.load()


class TestMLXEmbeddingModelLoader:
    """Tests for MLXEmbeddingModelLoader class."""

    @pytest.fixture
    def loader(self, tmp_path):
        """Create MLXEmbeddingModelLoader instance."""
        return MLXEmbeddingModelLoader(cache_dir=tmp_path / "cache")

    def test_cache_dir_created(self, loader, tmp_path):
        """Loader creates cache directory on init."""
        assert (tmp_path / "cache").exists()

    def test_load_unknown_model_raises(self, loader):
        """Loading unknown model raises EmbeddingError."""
        from src.model_loaders.base import EmbeddingError

        with pytest.raises(EmbeddingError, match="Unknown embedding model"):
            loader.load_model("nonexistent-model")

    def test_unload_nonexistent_model(self, loader):
        """Unloading non-loaded model is a no-op."""
        loader.unload_model("nonexistent")  # Should not raise

    def test_list_available_models(self, loader):
        """list_available_models returns registry entries."""
        models = loader.list_available_models()
        assert len(models) > 0
        assert all("name" in m and "dimensions" in m for m in models)
        assert all(m["device"] == "gpu" for m in models)
