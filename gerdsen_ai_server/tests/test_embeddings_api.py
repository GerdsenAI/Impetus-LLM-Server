"""
Tests for the /v1/embeddings API endpoint.

Uses a test Flask app with a mocked compute_dispatcher so tests
run without MLX or coremltools installed.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from src.routes.openai_api import bp as openai_bp


@pytest.fixture
def mock_dispatcher():
    """Create a mock compute_dispatcher that returns fixed embeddings."""
    dispatcher = MagicMock()
    dispatcher.embed.return_value = [[0.1, 0.2, 0.3, 0.4] * 96]  # 384-dim
    dispatcher.get_active_device.return_value = "gpu"
    return dispatcher


@pytest.fixture
def app(mock_dispatcher):
    """Create a test Flask app with the OpenAI blueprint."""
    test_app = Flask(__name__)
    test_app.config["TESTING"] = True
    test_app.config["app_state"] = {
        "loaded_models": {},
        "metrics": {},
    }
    test_app.register_blueprint(openai_bp, url_prefix="/v1")
    return test_app


@pytest.fixture
def client(app):
    return app.test_client()


def _post_embeddings(client, data, api_key="test-key"):
    """Helper to POST to /v1/embeddings with auth."""
    return client.post(
        "/v1/embeddings",
        data=json.dumps(data),
        content_type="application/json",
        headers={"Authorization": f"Bearer {api_key}"},
    )


# ── Single string input ───────────────────────────────────────────


class TestEmbeddingsEndpoint:

    @patch("src.routes.openai_api.verify_api_key", return_value=True)
    @patch("src.model_loaders.compute_dispatcher.compute_dispatcher")
    def test_single_string_input(self, mock_cd, mock_auth, client):
        mock_cd.embed.return_value = [[0.1, 0.2, 0.3]]

        resp = _post_embeddings(client, {"input": "Hello world", "model": "all-MiniLM-L6-v2"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["object"] == "list"
        assert len(data["data"]) == 1
        assert data["data"][0]["object"] == "embedding"
        assert data["data"][0]["index"] == 0
        assert isinstance(data["data"][0]["embedding"], list)
        assert data["model"] == "all-MiniLM-L6-v2"
        assert "usage" in data
        assert data["usage"]["prompt_tokens"] > 0

    @patch("src.routes.openai_api.verify_api_key", return_value=True)
    @patch("src.model_loaders.compute_dispatcher.compute_dispatcher")
    def test_list_input(self, mock_cd, mock_auth, client):
        mock_cd.embed.return_value = [[0.1], [0.2]]

        resp = _post_embeddings(client, {
            "input": ["Hello", "World"],
            "model": "all-MiniLM-L6-v2",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]) == 2
        assert data["data"][0]["index"] == 0
        assert data["data"][1]["index"] == 1

    @patch("src.routes.openai_api.verify_api_key", return_value=True)
    @patch("src.model_loaders.compute_dispatcher.compute_dispatcher")
    def test_unknown_model_returns_404(self, mock_cd, mock_auth, client):
        mock_cd.embed.side_effect = Exception("Unknown embedding model: 'fake-model'")

        resp = _post_embeddings(client, {"input": "hi", "model": "fake-model"})
        assert resp.status_code == 404

    @patch("src.routes.openai_api.verify_api_key", return_value=True)
    @patch("src.model_loaders.compute_dispatcher.compute_dispatcher")
    def test_no_backend_returns_503(self, mock_cd, mock_auth, client):
        mock_cd.embed.side_effect = Exception("No embedding backend available")

        resp = _post_embeddings(client, {"input": "hi"})
        assert resp.status_code == 503

    @patch("src.routes.openai_api.verify_api_key", return_value=True)
    @patch("src.model_loaders.compute_dispatcher.compute_dispatcher")
    def test_server_error_returns_500(self, mock_cd, mock_auth, client):
        mock_cd.embed.side_effect = RuntimeError("GPU out of memory")

        resp = _post_embeddings(client, {"input": "hi"})
        assert resp.status_code == 500
        data = resp.get_json()
        assert "error" in data

    @patch("src.routes.openai_api.verify_api_key", return_value=True)
    @patch("src.model_loaders.compute_dispatcher.compute_dispatcher")
    def test_token_counting(self, mock_cd, mock_auth, client):
        mock_cd.embed.return_value = [[0.5]]

        resp = _post_embeddings(client, {"input": "one two three four five"})
        data = resp.get_json()
        assert data["usage"]["prompt_tokens"] == 5
        assert data["usage"]["total_tokens"] == 5

    @patch("src.routes.openai_api.verify_api_key", return_value=True)
    @patch("src.model_loaders.compute_dispatcher.compute_dispatcher")
    def test_dimension_truncation(self, mock_cd, mock_auth, client):
        mock_cd.embed.return_value = [[0.1, 0.2, 0.3, 0.4, 0.5]]

        resp = _post_embeddings(client, {
            "input": "test",
            "dimensions": 3,
        })
        data = resp.get_json()
        assert len(data["data"][0]["embedding"]) == 3

    @patch("src.routes.openai_api.verify_api_key", return_value=True)
    @patch("src.model_loaders.compute_dispatcher.compute_dispatcher")
    def test_base64_encoding(self, mock_cd, mock_auth, client):
        mock_cd.embed.return_value = [[1.0, 2.0, 3.0]]

        resp = _post_embeddings(client, {
            "input": "test",
            "encoding_format": "base64",
        })
        data = resp.get_json()
        embedding = data["data"][0]["embedding"]
        # base64 returns a string, not a list
        assert isinstance(embedding, str)

    @patch("src.routes.openai_api.verify_api_key", return_value=True)
    def test_missing_input_returns_400(self, mock_auth, client):
        resp = _post_embeddings(client, {"model": "all-MiniLM-L6-v2"})
        assert resp.status_code == 400

    @patch("src.routes.openai_api.verify_api_key", return_value=True)
    @patch("src.model_loaders.compute_dispatcher.compute_dispatcher")
    def test_response_matches_openai_format(self, mock_cd, mock_auth, client):
        mock_cd.embed.return_value = [[0.1, 0.2]]

        resp = _post_embeddings(client, {"input": "hello"})
        data = resp.get_json()

        # Required top-level keys per OpenAI spec
        assert data["object"] == "list"
        assert "data" in data
        assert "model" in data
        assert "usage" in data

        # Data item structure
        item = data["data"][0]
        assert item["object"] == "embedding"
        assert "embedding" in item
        assert "index" in item
