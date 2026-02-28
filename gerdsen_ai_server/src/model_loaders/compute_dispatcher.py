"""
Compute dispatcher — routes embedding workloads to the best available device.

Priority chain:
  1. Core ML + ANE  (if coremltools installed and ANE hardware detected)
  2. MLX Metal GPU  (if MLX installed)
  3. Error          (no usable backend)
"""

import platform
from typing import Any

from loguru import logger

from ..config.settings import ComputeSettings, settings
from ..utils.hardware_detector import detect_ane_availability
from .base import BaseEmbeddingModel, BaseEmbeddingModelLoader, EmbeddingError
from .embedding_converter import EMBEDDING_MODEL_REGISTRY

# Lazy-check backend availability
COREML_AVAILABLE = False
try:
    import coremltools  # noqa: F401

    COREML_AVAILABLE = True
except ImportError:
    pass

MLX_AVAILABLE = False
try:
    import mlx.core  # noqa: F401

    MLX_AVAILABLE = True
except ImportError:
    pass


class ComputeDispatcher:
    """Routes embedding requests to the best available compute backend."""

    def __init__(self, compute_settings: ComputeSettings | None = None):
        self._settings = compute_settings or settings.compute
        self._embedding_loader: BaseEmbeddingModelLoader | None = None
        self._active_device: str = "none"
        self._ane_info: dict[str, Any] = {}

        self._detect_and_init()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _detect_and_init(self) -> None:
        """Detect hardware and initialise the best embedding loader."""
        is_macos_arm = platform.system() == "Darwin" and platform.machine() == "arm64"

        if is_macos_arm:
            self._ane_info = detect_ane_availability()
        else:
            self._ane_info = {"available": False}

        self._embedding_loader = self._select_embedding_loader()

    def _select_embedding_loader(self) -> BaseEmbeddingModelLoader | None:
        """Select the best embedding loader based on hardware and settings."""
        cache_dir = self._settings.embedding_cache_dir
        preferred = self._settings.preferred_embedding_device

        # Explicit preference overrides auto-detection
        if preferred == "ane":
            return self._try_coreml_loader(cache_dir)
        if preferred == "gpu":
            return self._try_mlx_loader(cache_dir)
        if preferred == "cpu":
            # CPU-only: use MLX loader (falls back to CPU-mode torch)
            return self._try_mlx_loader(cache_dir)

        # Auto: prefer ANE -> GPU
        loader = self._try_coreml_loader(cache_dir)
        if loader is not None:
            return loader

        loader = self._try_mlx_loader(cache_dir)
        if loader is not None:
            return loader

        logger.warning("No embedding backend available (install coremltools or mlx)")
        return None

    def _try_coreml_loader(self, cache_dir) -> BaseEmbeddingModelLoader | None:
        if not self._settings.enable_ane:
            return None
        if not COREML_AVAILABLE:
            logger.info("Core ML not available (coremltools not installed)")
            return None
        if not self._ane_info.get("available", False):
            logger.info("ANE hardware not detected — skipping Core ML loader")
            return None

        from .coreml_loader import CoreMLEmbeddingModelLoader

        logger.info("Selected Core ML + ANE for embedding inference")
        self._active_device = "ane"
        return CoreMLEmbeddingModelLoader(cache_dir=cache_dir)

    def _try_mlx_loader(self, cache_dir) -> BaseEmbeddingModelLoader | None:
        if not self._settings.enable_metal:
            return None
        if not MLX_AVAILABLE:
            logger.info("MLX not available")
            return None

        from .mlx_embedding_loader import MLXEmbeddingModelLoader

        logger.info("Selected MLX Metal GPU for embedding inference")
        self._active_device = "gpu"
        return MLXEmbeddingModelLoader(cache_dir=cache_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_embedding_model(self, name: str) -> BaseEmbeddingModel:
        """Load an embedding model via the selected backend."""
        if self._embedding_loader is None:
            raise EmbeddingError(
                "No embedding backend available. Install coremltools (ANE) or mlx (GPU)."
            )
        return self._embedding_loader.load_model(name)

    def unload_embedding_model(self, name: str) -> None:
        """Unload an embedding model."""
        if self._embedding_loader is not None:
            self._embedding_loader.unload_model(name)

    def embed(self, texts: list[str], model_name: str | None = None) -> list[list[float]]:
        """Generate embeddings, loading the model on demand if needed.

        Args:
            texts: List of strings to embed.
            model_name: Short model name (defaults to settings.default_embedding_model).

        Returns:
            List of embedding vectors.
        """
        if self._embedding_loader is None:
            raise EmbeddingError(
                "No embedding backend available. Install coremltools (ANE) or mlx (GPU)."
            )

        name = model_name or self._settings.default_embedding_model

        # Validate model exists in registry
        if name not in EMBEDDING_MODEL_REGISTRY:
            raise EmbeddingError(
                f"Unknown embedding model: '{name}'. "
                f"Available: {list(EMBEDDING_MODEL_REGISTRY)}"
            )

        # Load on demand
        if not self._embedding_loader.is_model_loaded(name):
            self.load_embedding_model(name)

        model = self._embedding_loader.get_loaded_model(name)
        if model is None:
            raise EmbeddingError(f"Failed to load embedding model '{name}'")

        # Batch if needed
        batch_size = self._settings.max_batch_size_embedding
        if len(texts) <= batch_size:
            return model.embed(texts)

        # Process in batches
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            all_embeddings.extend(model.embed(batch))
        return all_embeddings

    def get_capabilities(self) -> dict[str, Any]:
        """Return a summary of available compute capabilities."""
        loaded_models = []
        available_models = []

        if self._embedding_loader is not None:
            available_models = self._embedding_loader.list_available_models()
            for m in available_models:
                if m.get("loaded"):
                    loaded_models.append(m["name"])

        return {
            "active_device": self._active_device,
            "ane_available": self._ane_info.get("available", False),
            "ane_version": self._ane_info.get("version", 0),
            "coremltools_installed": COREML_AVAILABLE,
            "mlx_installed": MLX_AVAILABLE,
            "embedding_backend": type(self._embedding_loader).__name__ if self._embedding_loader else None,
            "loaded_embedding_models": loaded_models,
            "available_embedding_models": available_models,
            "default_embedding_model": self._settings.default_embedding_model,
            "max_batch_size": self._settings.max_batch_size_embedding,
        }

    def get_active_device(self) -> str:
        """Return the active device string: 'ane', 'gpu', or 'none'."""
        return self._active_device


# Singleton instance
compute_dispatcher = ComputeDispatcher()
