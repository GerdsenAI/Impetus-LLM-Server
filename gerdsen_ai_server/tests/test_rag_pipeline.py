"""Tests for the RAG pipeline service."""

from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# build_rag_context
# ---------------------------------------------------------------------------


class TestBuildRagContext:
    """Tests for build_rag_context()."""

    @patch("gerdsen_ai_server.src.services.rag_pipeline.vector_store_service")
    def test_returns_context_and_sources(self, mock_vs):
        """RAG context is built from search results."""
        mock_vs.search.return_value = {
            "documents": ["Doc about cats.", "Doc about dogs."],
            "metadatas": [
                {"source": "pets.txt", "chunk_index": 0},
                {"source": "animals.txt", "chunk_index": 1},
            ],
            "distances": [0.2, 0.5],
        }

        from gerdsen_ai_server.src.services.rag_pipeline import build_rag_context

        context_str, sources = build_rag_context("pets", n_results=2)

        # Context string contains numbered docs
        assert "[1]" in context_str
        assert "[2]" in context_str
        assert "Doc about cats." in context_str
        assert "Doc about dogs." in context_str

        # Sources list
        assert len(sources) == 2
        # Sorted by relevance descending (0.8 > 0.5)
        assert sources[0]["relevance"] >= sources[1]["relevance"]
        assert sources[0]["source"] == "pets.txt"

    @patch("gerdsen_ai_server.src.services.rag_pipeline.vector_store_service")
    def test_empty_results_returns_empty(self, mock_vs):
        """Empty search returns empty context."""
        mock_vs.search.return_value = {
            "documents": [],
            "metadatas": [],
            "distances": [],
        }

        from gerdsen_ai_server.src.services.rag_pipeline import build_rag_context

        context_str, sources = build_rag_context("nonexistent topic")

        assert context_str == ""
        assert sources == []

    @patch("gerdsen_ai_server.src.services.rag_pipeline.vector_store_service")
    def test_search_failure_returns_empty(self, mock_vs):
        """If vector store search raises, return empty gracefully."""
        mock_vs.search.side_effect = RuntimeError("connection failed")

        from gerdsen_ai_server.src.services.rag_pipeline import build_rag_context

        context_str, sources = build_rag_context("query")

        assert context_str == ""
        assert sources == []

    @patch("gerdsen_ai_server.src.services.rag_pipeline.vector_store_service")
    def test_relevance_score_clamped(self, mock_vs):
        """Relevance scores are clamped to [0, 1]."""
        mock_vs.search.return_value = {
            "documents": ["text"],
            "metadatas": [{"source": "f.txt", "chunk_index": 0}],
            "distances": [1.5],  # Would give negative relevance without clamping
        }

        from gerdsen_ai_server.src.services.rag_pipeline import build_rag_context

        _, sources = build_rag_context("query")

        assert sources[0]["relevance"] >= 0.0

    @patch("gerdsen_ai_server.src.services.rag_pipeline.vector_store_service")
    def test_long_text_truncated_in_source(self, mock_vs):
        """Long document text is truncated in source preview."""
        long_text = "A" * 300
        mock_vs.search.return_value = {
            "documents": [long_text],
            "metadatas": [{"source": "long.txt", "chunk_index": 0}],
            "distances": [0.1],
        }

        from gerdsen_ai_server.src.services.rag_pipeline import build_rag_context

        _, sources = build_rag_context("query")

        # Truncated to 200 chars + "..."
        assert len(sources[0]["text"]) == 203
        assert sources[0]["text"].endswith("...")

    @patch("gerdsen_ai_server.src.services.rag_pipeline.vector_store_service")
    def test_collection_name_passed_through(self, mock_vs):
        """Collection name is forwarded to vector store search."""
        mock_vs.search.return_value = {
            "documents": [],
            "metadatas": [],
            "distances": [],
        }

        from gerdsen_ai_server.src.services.rag_pipeline import build_rag_context

        build_rag_context("q", collection_name="my_collection")

        mock_vs.search.assert_called_once_with(
            query="q",
            n_results=5,
            collection_name="my_collection",
        )


# ---------------------------------------------------------------------------
# RAG injection in chat completions (integration-style with Flask test client)
# ---------------------------------------------------------------------------


class TestChatCompletionsRAG:
    """Test RAG context injection in the chat completions endpoint."""

    @pytest.fixture
    def app(self):
        """Create Flask test app with mocked model."""
        from gerdsen_ai_server.src.main import create_app

        app, _socketio = create_app()

        # Create a mock model
        mock_model = MagicMock()
        mock_model.model_id = "test-model"
        mock_model.generate.return_value = "Test response"
        mock_model.tokenize.return_value = [1, 2, 3]

        app.config["app_state"]["loaded_models"]["test-model"] = mock_model

        # Set a known API key
        from gerdsen_ai_server.src.config.settings import settings
        settings.server.api_key = "test-key"

        return app

    @patch("gerdsen_ai_server.src.services.rag_pipeline.build_rag_context")
    def test_rag_context_injected(self, mock_rag, app):
        """When use_rag=True, RAG context is prepended as system message."""
        mock_rag.return_value = (
            "Use the following context...\n\n[1] relevant doc",
            [{"text": "relevant doc", "source": "test.txt", "relevance": 0.9, "chunk_index": 0}],
        )

        with app.test_client() as client:
            resp = client.post(
                "/v1/chat/completions",
                json={
                    "model": "test-model",
                    "messages": [{"role": "user", "content": "What is RAG?"}],
                    "use_rag": True,
                    "stream": False,
                },
                headers={"Authorization": "Bearer test-key"},
            )

        assert resp.status_code == 200
        data = resp.get_json()

        # RAG sources included in response
        assert "rag_sources" in data
        assert len(data["rag_sources"]) == 1
        assert data["rag_sources"][0]["source"] == "test.txt"

        # build_rag_context was called
        mock_rag.assert_called_once()

    def test_rag_disabled_no_context(self, app):
        """When use_rag=False (default), no RAG context is added."""
        with app.test_client() as client:
            resp = client.post(
                "/v1/chat/completions",
                json={
                    "model": "test-model",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "stream": False,
                },
                headers={"Authorization": "Bearer test-key"},
            )

        assert resp.status_code == 200
        data = resp.get_json()

        # No RAG sources in response
        assert "rag_sources" not in data

    def test_context_documents_injected(self, app):
        """Pre-provided context_documents are injected as system message."""
        with app.test_client() as client:
            resp = client.post(
                "/v1/chat/completions",
                json={
                    "model": "test-model",
                    "messages": [{"role": "user", "content": "Summarize"}],
                    "context_documents": ["Doc A content", "Doc B content"],
                    "stream": False,
                },
                headers={"Authorization": "Bearer test-key"},
            )

        assert resp.status_code == 200

        # Verify the model was called (context docs injected into messages)
        mock_model = app.config["app_state"]["loaded_models"]["test-model"]
        call_args = mock_model.generate.call_args
        prompt = call_args[0][0] if call_args[0] else call_args.kwargs.get("prompt", "")
        # The prompt should contain context documents
        assert "Doc A content" in prompt or "Use this context" in prompt
