"""
E2E tests: Embeddings — /v1/embeddings via ANE or MLX compute dispatcher.

Tests real embedding generation through the full stack.
"""

import base64
import struct

import pytest
import requests

pytestmark = [pytest.mark.e2e, pytest.mark.slow]

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EXPECTED_DIMS = 384  # all-MiniLM-L6-v2 output dimension


class TestEmbeddings:
    """Embedding generation via the compute dispatcher."""

    def test_single_text_embedding(self, e2e_server, base_url, auth_headers):
        """POST /v1/embeddings with a single string returns correct dimensions."""
        payload = {
            "input": "The quick brown fox jumps over the lazy dog.",
            "model": EMBEDDING_MODEL,
        }
        r = requests.post(
            f"{base_url}/v1/embeddings",
            json=payload,
            headers=auth_headers,
            timeout=60,
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data.get("data", [])) == 1
        embedding = data["data"][0]["embedding"]
        assert isinstance(embedding, list)
        assert len(embedding) == EXPECTED_DIMS

    def test_batch_embeddings(self, e2e_server, base_url, auth_headers):
        """POST /v1/embeddings with a list of 5 strings returns 5 embeddings."""
        texts = [
            "First sentence.",
            "Second sentence.",
            "Third sentence.",
            "Fourth sentence.",
            "Fifth sentence.",
        ]
        payload = {"input": texts, "model": EMBEDDING_MODEL}
        r = requests.post(
            f"{base_url}/v1/embeddings",
            json=payload,
            headers=auth_headers,
            timeout=60,
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data.get("data", [])) == 5
        for i, item in enumerate(data["data"]):
            assert item.get("index") == i
            assert len(item["embedding"]) == EXPECTED_DIMS

    def test_embedding_dimensions_truncation(self, e2e_server, base_url, auth_headers):
        """POST with dimensions=128 truncates the output vector."""
        payload = {
            "input": "Test truncation.",
            "model": EMBEDDING_MODEL,
            "dimensions": 128,
        }
        r = requests.post(
            f"{base_url}/v1/embeddings",
            json=payload,
            headers=auth_headers,
            timeout=60,
        )
        assert r.status_code == 200
        data = r.json()
        embedding = data["data"][0]["embedding"]
        assert len(embedding) == 128

    def test_embedding_base64_format(self, e2e_server, base_url, auth_headers):
        """POST with encoding_format='base64' returns base64 string."""
        payload = {
            "input": "Base64 test.",
            "model": EMBEDDING_MODEL,
            "encoding_format": "base64",
        }
        r = requests.post(
            f"{base_url}/v1/embeddings",
            json=payload,
            headers=auth_headers,
            timeout=60,
        )
        assert r.status_code == 200
        data = r.json()
        embedding_b64 = data["data"][0]["embedding"]
        assert isinstance(embedding_b64, str)
        # Decode and verify length
        raw = base64.b64decode(embedding_b64)
        # Each float32 is 4 bytes
        num_floats = len(raw) // struct.calcsize("f")
        assert num_floats == EXPECTED_DIMS

    def test_embedding_openai_format(self, e2e_server, base_url, auth_headers):
        """Response follows OpenAI embedding format."""
        payload = {"input": "Format check.", "model": EMBEDDING_MODEL}
        r = requests.post(
            f"{base_url}/v1/embeddings",
            json=payload,
            headers=auth_headers,
            timeout=60,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("object") == "list"
        assert data["data"][0].get("object") == "embedding"
        assert "usage" in data
        assert "model" in data

    def test_compute_capabilities(self, e2e_server, base_url):
        """GET /api/hardware/compute/capabilities reports active device."""
        r = requests.get(
            f"{base_url}/api/hardware/compute/capabilities", timeout=10
        )
        assert r.status_code == 200
        data = r.json()
        assert "active_device" in data
        assert data["active_device"] in ("ane", "gpu", "mlx", "cpu", "coreml")
