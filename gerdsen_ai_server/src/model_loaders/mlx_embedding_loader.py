"""
MLX GPU embedding model loader — fallback when Core ML / ANE is unavailable.

Uses MLX Metal GPU backend for embedding inference on Apple Silicon.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from .base import BaseEmbeddingModel, BaseEmbeddingModelLoader, EmbeddingError
from .embedding_converter import EMBEDDING_MODEL_REGISTRY

MLX_AVAILABLE = False
try:
    import mlx.core as mx
    import mlx.nn as nn  # noqa: F401

    MLX_AVAILABLE = True
except ImportError:
    pass


class MLXEmbeddingModel(BaseEmbeddingModel):
    """Embedding model that runs on MLX Metal GPU."""

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
            device="gpu",
        )
        self.hf_model_id = hf_model_id
        self._hf_model = None
        self._tokenizer = None
        self._max_seq_length = min(128, max_tokens)

    def load(self) -> None:
        if not MLX_AVAILABLE:
            raise EmbeddingError("MLX is not installed")

        from transformers import AutoModel, AutoTokenizer

        logger.info(f"Loading HuggingFace model '{self.hf_model_id}' for MLX GPU embedding")
        self._tokenizer = AutoTokenizer.from_pretrained(self.hf_model_id)
        self._hf_model = AutoModel.from_pretrained(self.hf_model_id)
        self._hf_model.config.output_hidden_states = False

        self._loaded = True
        logger.info(f"MLX embedding model '{self.model_name}' loaded (device=gpu)")

    def unload(self) -> None:
        self._hf_model = None
        self._tokenizer = None
        self._loaded = False
        logger.info(f"MLX embedding model '{self.model_name}' unloaded")

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self._loaded or self._hf_model is None:
            raise EmbeddingError(f"Model '{self.model_name}' is not loaded")

        import numpy as np

        # Tokenize all texts in batch
        encoded = self._tokenizer(
            texts,
            padding=True,
            max_length=self._max_seq_length,
            truncation=True,
            return_tensors="np",
        )

        input_ids = encoded["input_ids"]
        attention_mask = encoded["attention_mask"]

        # Run forward pass through HuggingFace model, then pool via MLX on GPU
        import torch

        with torch.no_grad():
            torch_ids = torch.from_numpy(input_ids.astype(np.int64))
            torch_mask = torch.from_numpy(attention_mask.astype(np.int64))
            outputs = self._hf_model(input_ids=torch_ids, attention_mask=torch_mask)

        hidden_state = outputs.last_hidden_state.numpy()  # (batch, seq_len, hidden_dim)
        attention_float = attention_mask.astype(np.float32)

        # Mean pooling via MLX on GPU
        mx_hidden = mx.array(hidden_state)
        mx_mask_exp = mx.expand_dims(mx.array(attention_float), axis=-1)  # (batch, seq_len, 1)
        summed = mx.sum(mx_hidden * mx_mask_exp, axis=1)  # (batch, hidden_dim)
        counts = mx.maximum(mx.sum(mx_mask_exp, axis=1), mx.array(1e-9))
        pooled = summed / counts  # (batch, hidden_dim)

        # L2 normalize
        norms = mx.linalg.norm(pooled, axis=-1, keepdims=True)
        norms = mx.maximum(norms, mx.array(1e-12))
        normalized = pooled / norms

        # Force computation and convert to Python lists
        result = np.array(normalized)

        embeddings = []
        for vec in result:
            v = vec.tolist()
            if len(v) > self.dimensions:
                v = v[: self.dimensions]
            embeddings.append(v)

        return embeddings

    def get_info(self) -> dict[str, Any]:
        info = super().get_info()
        info["hf_model_id"] = self.hf_model_id
        info["max_seq_length"] = self._max_seq_length
        return info


class MLXEmbeddingModelLoader(BaseEmbeddingModelLoader):
    """Loader that runs HuggingFace embedding models via MLX GPU."""

    def __init__(self, cache_dir: str | Path):
        super().__init__()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load_model(self, name: str) -> MLXEmbeddingModel:
        if name in self._loaded_models and self._loaded_models[name].is_loaded:
            return self._loaded_models[name]

        registry_entry = EMBEDDING_MODEL_REGISTRY.get(name)
        if registry_entry is None:
            raise EmbeddingError(f"Unknown embedding model: '{name}'. Available: {list(EMBEDDING_MODEL_REGISTRY)}")

        hf_id = registry_entry["hf_id"]

        model = MLXEmbeddingModel(
            model_name=name,
            model_path=str(self.cache_dir / name),
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
            models.append({
                "name": name,
                "hf_id": entry["hf_id"],
                "dimensions": entry["dimensions"],
                "max_tokens": entry["max_tokens"],
                "params_millions": entry["params_millions"],
                "cached": False,
                "loaded": self.is_model_loaded(name),
                "device": "gpu",
            })
        return models
