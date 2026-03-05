"""
Unit tests for the ImpetusEmbeddingFunction embedding bridge.

Mocks compute_dispatcher to avoid importing real MLX / Core ML backends.
"""

from unittest.mock import MagicMock, patch

import pytest
from src.services.embedding_bridge import ImpetusEmbeddingFunction


class TestImpetusEmbeddingFunction:
    """Tests for ImpetusEmbeddingFunction delegation to compute_dispatcher."""

    def test_call_delegates_to_compute_dispatcher(self):
        """__call__ forwards the input documents to compute_dispatcher.embed and returns its result."""
        mock_dispatcher = MagicMock()
        mock_dispatcher.embed.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

        with patch("src.model_loaders.compute_dispatcher.compute_dispatcher", mock_dispatcher):
            fn = ImpetusEmbeddingFunction()
            result = fn(["hello world", "test document"])

        mock_dispatcher.embed.assert_called_once_with(["hello world", "test document"], None)
        # ChromaDB may wrap inner lists as numpy arrays, so verify values not identity
        assert len(result) == 2
        assert list(result[0]) == pytest.approx([0.1, 0.2, 0.3])

    def test_call_with_model_name(self):
        """When a model_name is provided, it is passed through to compute_dispatcher.embed."""
        mock_dispatcher = MagicMock()
        mock_dispatcher.embed.return_value = [[1.0, 2.0]]

        with patch("src.model_loaders.compute_dispatcher.compute_dispatcher", mock_dispatcher):
            fn = ImpetusEmbeddingFunction(model_name="nomic-embed-text-v1.5")
            result = fn(["sample text"])

        mock_dispatcher.embed.assert_called_once_with(["sample text"], "nomic-embed-text-v1.5")
        assert len(result) == 1
        assert list(result[0]) == pytest.approx([1.0, 2.0])

    def test_call_converts_input_to_list(self):
        """The Documents input is converted to a plain list before being passed to embed."""
        mock_dispatcher = MagicMock()
        mock_dispatcher.embed.return_value = [[0.0]]

        # Simulate a Documents-like sequence that is not already a list
        documents = ("tuple doc 1", "tuple doc 2")

        with patch("src.model_loaders.compute_dispatcher.compute_dispatcher", mock_dispatcher):
            fn = ImpetusEmbeddingFunction()
            fn(documents)

        # The first positional arg should be a plain list, not the original tuple
        actual_arg = mock_dispatcher.embed.call_args[0][0]
        assert isinstance(actual_arg, list)
        assert actual_arg == ["tuple doc 1", "tuple doc 2"]

    def test_default_model_name_is_none(self):
        """When no model_name is provided, internal _model_name defaults to None."""
        fn = ImpetusEmbeddingFunction()
        assert fn._model_name is None

    def test_model_name_stored(self):
        """The model_name passed to __init__ is stored as _model_name."""
        fn = ImpetusEmbeddingFunction(model_name="custom-model")
        assert fn._model_name == "custom-model"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
