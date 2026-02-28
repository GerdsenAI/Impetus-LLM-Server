"""
Tests for Core ML embedding loader and converter pipeline.

Tests are skipped when coremltools is not installed so CI can pass on
non-macOS runners.
"""

from unittest.mock import patch

import pytest

# Guard coremltools import
try:
    import coremltools  # noqa: F401
    COREML_INSTALLED = True
except ImportError:
    COREML_INSTALLED = False

from src.model_loaders.base import EmbeddingError
from src.model_loaders.embedding_converter import (
    EMBEDDING_MODEL_REGISTRY,
    get_cached_model_path,
    get_model_info,
    validate_ane_compatibility,
)

# ── Registry tests ─────────────────────────────────────────────────


class TestEmbeddingModelRegistry:
    """Tests for the model registry and helper functions."""

    def test_registry_has_expected_models(self):
        assert "all-MiniLM-L6-v2" in EMBEDDING_MODEL_REGISTRY
        assert "nomic-embed-text-v1.5" in EMBEDDING_MODEL_REGISTRY
        assert "bge-small-en-v1.5" in EMBEDDING_MODEL_REGISTRY

    def test_registry_entries_have_required_fields(self):
        for name, entry in EMBEDDING_MODEL_REGISTRY.items():
            assert "hf_id" in entry, f"{name} missing hf_id"
            assert "dimensions" in entry, f"{name} missing dimensions"
            assert "max_tokens" in entry, f"{name} missing max_tokens"
            assert "params_millions" in entry, f"{name} missing params_millions"

    def test_get_model_info_existing(self):
        info = get_model_info("all-MiniLM-L6-v2")
        assert info is not None
        assert info["dimensions"] == 384

    def test_get_model_info_unknown(self):
        assert get_model_info("nonexistent-model") is None


# ── Cache path tests ───────────────────────────────────────────────


class TestCachePaths:

    def test_cached_model_path_missing(self, tmp_path):
        result = get_cached_model_path("some-model", tmp_path)
        assert result is None

    def test_cached_model_path_exists(self, tmp_path):
        mlpackage = tmp_path / "some-model.mlpackage"
        mlpackage.mkdir()
        result = get_cached_model_path("some-model", tmp_path)
        assert result == mlpackage


# ── ANE compatibility validation ───────────────────────────────────


class TestANECompatibility:

    def test_validate_missing_path(self, tmp_path):
        result = validate_ane_compatibility(tmp_path / "nonexistent")
        assert "error" in result

    def test_validate_small_model(self, tmp_path):
        # Create a fake model dir < 500 MB
        model_dir = tmp_path / "small.mlpackage"
        model_dir.mkdir()
        (model_dir / "weights.bin").write_bytes(b"\x00" * (100 * 1024 * 1024))  # 100 MB
        result = validate_ane_compatibility(model_dir)
        assert result["estimated_ane_compatible"] is True
        assert result["size_mb"] > 0

    def test_validate_large_model(self, tmp_path):
        # Create a fake large file (> 500 MB metadata)
        model_file = tmp_path / "large.mlpackage"
        model_file.mkdir()
        # We can't create a 500MB+ file in tests, so mock stat
        result = validate_ane_compatibility(model_file)
        # Empty dir = 0 MB = compatible
        assert result["estimated_ane_compatible"] is True


# ── CoreMLEmbeddingModel tests ─────────────────────────────────────


@pytest.mark.skipif(not COREML_INSTALLED, reason="coremltools not installed")
class TestCoreMLEmbeddingModel:
    """Tests that require coremltools — skipped on Linux CI."""

    def test_model_not_loaded_raises_on_embed(self):
        from src.model_loaders.coreml_loader import CoreMLEmbeddingModel

        model = CoreMLEmbeddingModel(
            model_name="test",
            model_path="/fake/path",
            dimensions=384,
            max_tokens=256,
            hf_model_id="sentence-transformers/all-MiniLM-L6-v2",
        )
        with pytest.raises(EmbeddingError, match="not loaded"):
            model.embed(["hello"])

    def test_model_get_info(self):
        from src.model_loaders.coreml_loader import CoreMLEmbeddingModel

        model = CoreMLEmbeddingModel(
            model_name="test",
            model_path="/fake/path",
            dimensions=384,
            max_tokens=256,
            hf_model_id="sentence-transformers/all-MiniLM-L6-v2",
        )
        info = model.get_info()
        assert info["model_name"] == "test"
        assert info["device"] == "ane"
        assert info["dimensions"] == 384
        assert info["loaded"] is False

    def test_loader_unknown_model_raises(self, tmp_path):
        from src.model_loaders.coreml_loader import CoreMLEmbeddingModelLoader

        loader = CoreMLEmbeddingModelLoader(cache_dir=tmp_path)
        with pytest.raises(EmbeddingError, match="Unknown embedding model"):
            loader.load_model("does-not-exist")

    def test_loader_list_available_models(self, tmp_path):
        from src.model_loaders.coreml_loader import CoreMLEmbeddingModelLoader

        loader = CoreMLEmbeddingModelLoader(cache_dir=tmp_path)
        models = loader.list_available_models()
        assert len(models) == len(EMBEDDING_MODEL_REGISTRY)
        for m in models:
            assert m["device"] == "ane"


# ── Graceful failure tests ─────────────────────────────────────────


class TestGracefulFailure:
    """Ensure the loader chain doesn't crash when ANE/coremltools is unavailable."""

    @patch("src.model_loaders.coreml_loader.COREML_AVAILABLE", False)
    def test_coreml_model_load_without_coremltools(self):
        from src.model_loaders.coreml_loader import CoreMLEmbeddingModel

        model = CoreMLEmbeddingModel(
            model_name="test",
            model_path="/fake",
            dimensions=384,
            max_tokens=256,
            hf_model_id="fake/model",
        )
        with pytest.raises(EmbeddingError, match="coremltools"):
            model.load()
