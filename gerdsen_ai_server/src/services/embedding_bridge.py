"""
Bridge between compute_dispatcher embeddings and
ChromaDB's EmbeddingFunction protocol.
"""

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings


class ImpetusEmbeddingFunction(EmbeddingFunction[Documents]):
    """Adapts compute_dispatcher.embed() for ChromaDB."""

    def __init__(self, model_name: str | None = None):
        self._model_name = model_name

    def __call__(self, input: Documents) -> Embeddings:  # noqa: A002
        # Lazy import to avoid circular imports
        # (same pattern as openai_api.py:428)
        from ..model_loaders.compute_dispatcher import compute_dispatcher

        return compute_dispatcher.embed(list(input), self._model_name)
