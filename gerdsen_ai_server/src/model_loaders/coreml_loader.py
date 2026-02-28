"""
Core ML embedding model loader for Apple Neural Engine (ANE) inference.

Routes embedding workloads to the ANE for 20-30x faster inference
on small models compared to GPU-only execution.
"""

from pathlib import Path
from typing import Any

import numpy as np
from loguru import logger

from .base import BaseEmbeddingModel, BaseEmbeddingModelLoader, EmbeddingError
from .embedding_converter import (
    EMBEDDING_MODEL_REGISTRY,
    convert_to_coreml,
    get_cached_model_path,
    validate_ane_compatibility,
)

COREML_AVAILABLE = False
try:
    import coremltools as ct

    COREML_AVAILABLE = True
except ImportError:
    pass


class CoreMLEmbeddingModel(BaseEmbeddingModel):
    """Embedding model backed by Core ML for ANE execution."""

    def __init__(
        self,
        model_name: str,
        model_path: str | Path,
        dimensions: int,
        max_tokens: int,
        hf_model_id: str,
    ):
        super().__init__(
            model_name=model_name,
            model_path=model_path,
            dimensions=dimensions,
            max_tokens=max_tokens,
            device="ane",
        )
        self.hf_model_id = hf_model_id
        self._coreml_model = None
        self._tokenizer = None
        self._max_seq_length = min(128, max_tokens)

    def load(self) -> None:
        if not COREML_AVAILABLE:
            raise EmbeddingError("coremltools is not installed")

        from transformers import AutoTokenizer

        logger.info(f"Loading Core ML model from {self.model_path}")
        self._coreml_model = ct.models.MLModel(
            str(self.model_path),
            compute_units=ct.ComputeUnit.ALL,
        )
        self._tokenizer = AutoTokenizer.from_pretrained(self.hf_model_id)
        self._loaded = True
        logger.info(f"Core ML model '{self.model_name}' loaded (device=ane)")

    def unload(self) -> None:
        self._coreml_model = None
        self._tokenizer = None
        self._loaded = False
        logger.info(f"Core ML model '{self.model_name}' unloaded")

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self._loaded or self._coreml_model is None:
            raise EmbeddingError(f"Model '{self.model_name}' is not loaded")

        embeddings: list[list[float]] = []
        for text in texts:
            encoded = self._tokenizer(
                text,
                padding="max_length",
                max_length=self._max_seq_length,
                truncation=True,
                return_tensors="np",
            )

            prediction = self._coreml_model.predict({
                "input_ids": encoded["input_ids"].astype(np.int32),
                "attention_mask": encoded["attention_mask"].astype(np.int32),
            })

            # Get the last hidden state (first output key)
            output_key = list(prediction.keys())[0]
            hidden_state = prediction[output_key]  # (1, seq_len, hidden_dim)

            # Mean pooling over non-padding tokens
            mask = encoded["attention_mask"].astype(np.float32)
            if hidden_state.ndim == 3:
                mask_expanded = np.expand_dims(mask, axis=-1)  # (1, seq_len, 1)
                summed = np.sum(hidden_state * mask_expanded, axis=1)  # (1, hidden_dim)
                count = np.clip(mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
                pooled = summed / count
            else:
                # Already pooled (some models output (1, hidden_dim))
                pooled = hidden_state

            # L2 normalize
            norm = np.linalg.norm(pooled, axis=-1, keepdims=True)
            norm = np.clip(norm, a_min=1e-12, a_max=None)
            normalized = pooled / norm

            # Truncate to requested dimensions if needed
            vec = normalized.flatten().tolist()
            if len(vec) > self.dimensions:
                vec = vec[: self.dimensions]

            embeddings.append(vec)

        return embeddings

    def get_info(self) -> dict[str, Any]:
        info = super().get_info()
        info["hf_model_id"] = self.hf_model_id
        info["max_seq_length"] = self._max_seq_length
        return info


class CoreMLEmbeddingModelLoader(BaseEmbeddingModelLoader):
    """Loader that converts HuggingFace models to Core ML and runs on ANE."""

    def __init__(self, cache_dir: str | Path):
        super().__init__()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load_model(self, name: str) -> CoreMLEmbeddingModel:
        if name in self._loaded_models and self._loaded_models[name].is_loaded:
            return self._loaded_models[name]

        registry_entry = EMBEDDING_MODEL_REGISTRY.get(name)
        if registry_entry is None:
            raise EmbeddingError(f"Unknown embedding model: '{name}'. Available: {list(EMBEDDING_MODEL_REGISTRY)}")

        hf_id = registry_entry["hf_id"]
        safe_name = hf_id.replace("/", "_")

        # Check cache for existing .mlpackage
        cached = get_cached_model_path(safe_name, self.cache_dir)
        if cached is None:
            logger.info(f"No cached Core ML model for '{name}', converting from HuggingFace...")
            cached = convert_to_coreml(
                hf_model_name=hf_id,
                output_dir=self.cache_dir,
            )

        # Validate ANE compatibility
        compat = validate_ane_compatibility(cached)
        if not compat.get("estimated_ane_compatible", True):
            logger.warning(f"Model '{name}' may not run efficiently on ANE: {compat.get('notes', [])}")

        model = CoreMLEmbeddingModel(
            model_name=name,
            model_path=cached,
            dimensions=registry_entry["dimensions"],
            max_tokens=registry_entry["max_tokens"],
            hf_model_id=hf_id,
        )
        model.load()
        self._loaded_models[name] = model
        return model

    def unload_model(self, name: str) -> None:
        model = self._loaded_models.pop(name, None)
        if model is not None:
            model.unload()

    def list_available_models(self) -> list[dict[str, Any]]:
        models = []
        for name, entry in EMBEDDING_MODEL_REGISTRY.items():
            safe_name = entry["hf_id"].replace("/", "_")
            cached = get_cached_model_path(safe_name, self.cache_dir)
            models.append({
                "name": name,
                "hf_id": entry["hf_id"],
                "dimensions": entry["dimensions"],
                "max_tokens": entry["max_tokens"],
                "params_millions": entry["params_millions"],
                "cached": cached is not None,
                "loaded": self.is_model_loaded(name),
                "device": "ane",
            })
        return models
