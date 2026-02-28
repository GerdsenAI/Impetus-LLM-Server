"""
Tests for the /api/documents endpoints.

Uses a test Flask app with a mocked vector_store_service.
Follows the pattern from test_embeddings_api.py.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from src.routes.documents import bp as documents_bp


@pytest.fixture
def mock_vector_store():
    """Create a mock vector_store_service."""
    svc = MagicMock()
    svc.ingest_text.return_value = {
        "status": "success",
        "chunks_stored": 3,
        "collection": "documents",
        "source": "test.txt",
        "document_ids": ["id1", "id2", "id3"],
    }
    svc.search.return_value = {
        "documents": ["doc1 text", "doc2 text"],
        "metadatas": [{"source": "a.txt"}, {"source": "b.txt"}],
        "distances": [0.15, 0.32],
        "count": 2,
        "query": "test query",
    }
    svc.list_collections.return_value = [
        {"name": "documents", "count": 10, "metadata": {}},
    ]
    svc.get_collection_info.return_value = {
        "name": "documents",
        "count": 10,
        "metadata": {},
    }
    return svc


@pytest.fixture
def app():
    """Create a test Flask app with the documents blueprint."""
    test_app = Flask(__name__)
    test_app.config["TESTING"] = True
    test_app.register_blueprint(documents_bp, url_prefix="/api/documents")
    return test_app


@pytest.fixture
def client(app):
    return app.test_client()


def _post_json(client, path, data):
    return client.post(
        path,
        data=json.dumps(data),
        content_type="application/json",
    )


class TestDocumentIngest:

    @patch("src.routes.documents.vector_store_service")
    def test_ingest_success(self, mock_svc, client):
        mock_svc.ingest_text.return_value = {
            "status": "success",
            "chunks_stored": 2,
            "collection": "documents",
            "source": "test.txt",
            "document_ids": ["a", "b"],
        }

        resp = _post_json(client, "/api/documents/ingest", {
            "text": "Hello world. This is a test document.",
            "source": "test.txt",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert data["chunks_stored"] == 2
        mock_svc.ingest_text.assert_called_once()

    @patch("src.routes.documents.vector_store_service")
    def test_ingest_missing_text_returns_400(self, mock_svc, client):
        resp = _post_json(client, "/api/documents/ingest", {"source": "test.txt"})
        assert resp.status_code == 400

    @patch("src.routes.documents.vector_store_service")
    def test_ingest_empty_text_returns_400(self, mock_svc, client):
        resp = _post_json(client, "/api/documents/ingest", {"text": ""})
        assert resp.status_code == 400


class TestDocumentSearch:

    @patch("src.routes.documents.vector_store_service")
    def test_search_success(self, mock_svc, client):
        mock_svc.search.return_value = {
            "documents": ["result"],
            "metadatas": [{"source": "x.txt"}],
            "distances": [0.1],
            "count": 1,
            "query": "test",
        }

        resp = _post_json(client, "/api/documents/search", {"query": "test"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 1
        assert data["query"] == "test"
        mock_svc.search.assert_called_once()

    @patch("src.routes.documents.vector_store_service")
    def test_search_missing_query_returns_400(self, mock_svc, client):
        resp = _post_json(client, "/api/documents/search", {"n_results": 5})
        assert resp.status_code == 400


class TestCollections:

    @patch("src.routes.documents.vector_store_service")
    def test_list_collections(self, mock_svc, client):
        mock_svc.list_collections.return_value = [
            {"name": "docs", "count": 5, "metadata": {}},
        ]

        resp = client.get("/api/documents/collections")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 1
        assert data["collections"][0]["name"] == "docs"

    @patch("src.routes.documents.vector_store_service")
    def test_get_collection_info(self, mock_svc, client):
        mock_svc.get_collection_info.return_value = {
            "name": "test_col",
            "count": 42,
            "metadata": {},
        }

        resp = client.get("/api/documents/collections/test_col")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["name"] == "test_col"
        assert data["count"] == 42

    @patch("src.routes.documents.vector_store_service")
    def test_delete_collection(self, mock_svc, client):
        resp = client.delete("/api/documents/collections/to_delete")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "deleted"
        mock_svc.delete_collection.assert_called_once_with("to_delete")

    @patch("src.routes.documents.vector_store_service")
    def test_get_nonexistent_collection_returns_404(self, mock_svc, client):
        mock_svc.get_collection_info.side_effect = Exception("not found")
        resp = client.get("/api/documents/collections/nonexistent")
        assert resp.status_code == 404
