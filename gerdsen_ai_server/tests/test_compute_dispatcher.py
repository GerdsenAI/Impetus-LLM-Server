"""
Tests for the ComputeDispatcher — backend selection, fallback chain,
capabilities reporting, and embedding dispatch.
"""

from unittest.mock import MagicMock, patch

import pytest
from src.config.settings import ComputeSettings
from src.model_loaders.base import EmbeddingError
from src.model_loaders.compute_dispatcher import ComputeDispatcher

# ── Helpers ────────────────────────────────────────────────────────


def _make_settings(tmp_path, **overrides) -> ComputeSettings:
    """Create a ComputeSettings with a temp cache dir."""
    defaults = {
        "embedding_cache_dir": tmp_path / "embeddings",
        "enable_ane": True,
        "enable_metal": True,
        "preferred_embedding_device": "auto",
        "default_embedding_model": "all-MiniLM-L6-v2",
        "max_batch_size_embedding": 4,
    }
    defaults.update(overrides)
    return ComputeSettings(**defaults)


# ── Backend selection tests ────────────────────────────────────────


class TestBackendSelection:

    @patch("src.model_loaders.compute_dispatcher.COREML_AVAILABLE", True)
    @patch("src.model_loaders.compute_dispatcher.MLX_AVAILABLE", True)
    @patch("src.model_loaders.compute_dispatcher.detect_ane_availability")
    @patch("src.model_loaders.compute_dispatcher.platform")
    def test_auto_prefers_ane_when_available(self, mock_platform, mock_ane, tmp_path):
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_ane.return_value = {"available": True, "version": 1}

        dispatcher = ComputeDispatcher(_make_settings(tmp_path))
        assert dispatcher.get_active_device() == "ane"

    @patch("src.model_loaders.compute_dispatcher.COREML_AVAILABLE", False)
    @patch("src.model_loaders.compute_dispatcher.MLX_AVAILABLE", True)
    @patch("src.model_loaders.compute_dispatcher.detect_ane_availability")
    @patch("src.model_loaders.compute_dispatcher.platform")
    def test_auto_falls_back_to_gpu(self, mock_platform, mock_ane, tmp_path):
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_ane.return_value = {"available": False}

        dispatcher = ComputeDispatcher(_make_settings(tmp_path))
        assert dispatcher.get_active_device() == "gpu"

    @patch("src.model_loaders.compute_dispatcher.COREML_AVAILABLE", False)
    @patch("src.model_loaders.compute_dispatcher.MLX_AVAILABLE", False)
    @patch("src.model_loaders.compute_dispatcher.detect_ane_availability")
    @patch("src.model_loaders.compute_dispatcher.platform")
    def test_no_backend_returns_none(self, mock_platform, mock_ane, tmp_path):
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_ane.return_value = {"available": False}

        dispatcher = ComputeDispatcher(_make_settings(tmp_path))
        assert dispatcher.get_active_device() == "none"

    @patch("src.model_loaders.compute_dispatcher.COREML_AVAILABLE", True)
    @patch("src.model_loaders.compute_dispatcher.MLX_AVAILABLE", True)
    @patch("src.model_loaders.compute_dispatcher.detect_ane_availability")
    @patch("src.model_loaders.compute_dispatcher.platform")
    def test_explicit_gpu_preference(self, mock_platform, mock_ane, tmp_path):
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_ane.return_value = {"available": True, "version": 1}

        settings = _make_settings(tmp_path, preferred_embedding_device="gpu")
        dispatcher = ComputeDispatcher(settings)
        assert dispatcher.get_active_device() == "gpu"

    @patch("src.model_loaders.compute_dispatcher.COREML_AVAILABLE", True)
    @patch("src.model_loaders.compute_dispatcher.MLX_AVAILABLE", True)
    @patch("src.model_loaders.compute_dispatcher.detect_ane_availability")
    @patch("src.model_loaders.compute_dispatcher.platform")
    def test_ane_disabled_in_settings(self, mock_platform, mock_ane, tmp_path):
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"
        mock_ane.return_value = {"available": True, "version": 1}

        settings = _make_settings(tmp_path, enable_ane=False)
        dispatcher = ComputeDispatcher(settings)
        assert dispatcher.get_active_device() == "gpu"


# ── Capabilities ───────────────────────────────────────────────────


class TestCapabilities:

    @patch("src.model_loaders.compute_dispatcher.COREML_AVAILABLE", False)
    @patch("src.model_loaders.compute_dispatcher.MLX_AVAILABLE", False)
    @patch("src.model_loaders.compute_dispatcher.platform")
    def test_capabilities_structure(self, mock_platform, tmp_path):
        mock_platform.system.return_value = "Linux"
        mock_platform.machine.return_value = "x86_64"

        dispatcher = ComputeDispatcher(_make_settings(tmp_path))
        caps = dispatcher.get_capabilities()

        assert "active_device" in caps
        assert "ane_available" in caps
        assert "mlx_installed" in caps
        assert "coremltools_installed" in caps
        assert "loaded_embedding_models" in caps
        assert "available_embedding_models" in caps
        assert "default_embedding_model" in caps
        assert "max_batch_size" in caps


# ── Embed dispatch ─────────────────────────────────────────────────


class TestEmbedDispatch:

    @patch("src.model_loaders.compute_dispatcher.COREML_AVAILABLE", False)
    @patch("src.model_loaders.compute_dispatcher.MLX_AVAILABLE", False)
    @patch("src.model_loaders.compute_dispatcher.platform")
    def test_embed_without_backend_raises(self, mock_platform, tmp_path):
        mock_platform.system.return_value = "Linux"
        mock_platform.machine.return_value = "x86_64"

        dispatcher = ComputeDispatcher(_make_settings(tmp_path))
        with pytest.raises(EmbeddingError, match="No embedding backend"):
            dispatcher.embed(["hello"])

    @patch("src.model_loaders.compute_dispatcher.COREML_AVAILABLE", False)
    @patch("src.model_loaders.compute_dispatcher.MLX_AVAILABLE", False)
    @patch("src.model_loaders.compute_dispatcher.platform")
    def test_embed_unknown_model_raises(self, mock_platform, tmp_path):
        mock_platform.system.return_value = "Linux"
        mock_platform.machine.return_value = "x86_64"

        dispatcher = ComputeDispatcher(_make_settings(tmp_path))
        # Even with no backend, unknown model check comes after backend check
        with pytest.raises(EmbeddingError):
            dispatcher.embed(["hello"], model_name="nonexistent")

    def test_embed_with_mock_loader(self, tmp_path):
        """Test that embed() correctly delegates to the loader."""
        mock_model = MagicMock()
        mock_model.is_loaded = True
        mock_model.embed.return_value = [[0.1, 0.2, 0.3]]

        mock_loader = MagicMock()
        mock_loader.is_model_loaded.return_value = True
        mock_loader.get_loaded_model.return_value = mock_model

        settings = _make_settings(tmp_path)
        dispatcher = ComputeDispatcher(settings)
        dispatcher._embedding_loader = mock_loader
        dispatcher._active_device = "gpu"

        result = dispatcher.embed(["hello"], model_name="all-MiniLM-L6-v2")
        assert result == [[0.1, 0.2, 0.3]]
        mock_model.embed.assert_called_once_with(["hello"])

    def test_embed_batching(self, tmp_path):
        """Test that large inputs are split into batches."""
        mock_model = MagicMock()
        mock_model.is_loaded = True
        mock_model.embed.side_effect = lambda texts: [[0.1] * 384 for _ in texts]

        mock_loader = MagicMock()
        mock_loader.is_model_loaded.return_value = True
        mock_loader.get_loaded_model.return_value = mock_model

        settings = _make_settings(tmp_path, max_batch_size_embedding=2)
        dispatcher = ComputeDispatcher(settings)
        dispatcher._embedding_loader = mock_loader
        dispatcher._active_device = "gpu"

        texts = ["a", "b", "c", "d", "e"]
        result = dispatcher.embed(texts, model_name="all-MiniLM-L6-v2")
        assert len(result) == 5
        # Should have been called 3 times: [a,b], [c,d], [e]
        assert mock_model.embed.call_count == 3
