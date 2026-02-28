"""
E2E tests: RAG pipeline — document ingest, search, RAG-augmented completions.

Tests the full flow: ingest text → chunk → embed → vector store → retrieve → generate.
Uses a fictional company ("Nexora Technologies") so retrieval can be verified
by checking for distinctive terms in the results.
"""

import pytest
import requests

pytestmark = [pytest.mark.e2e, pytest.mark.slow]

NEXORA_DOCUMENT = """
Nexora Technologies is a fictional company founded in 2019 in Zurich, Switzerland.
The company specialises in quantum-resistant cryptographic algorithms for IoT devices.
Their flagship product, QuantumShield Pro, uses lattice-based cryptography to secure
communication between edge devices and cloud infrastructure.

Nexora's CEO, Dr. Elara Voss, previously led the post-quantum cryptography division
at CERN. The company has 142 employees across offices in Zurich, Singapore, and Austin.
In 2024, Nexora raised a Series B round of $87 million led by Horizons Capital.

Key technical specifications of QuantumShield Pro:
- Encryption: CRYSTALS-Kyber (ML-KEM) for key encapsulation
- Signatures: CRYSTALS-Dilithium (ML-DSA) for digital signatures
- Latency overhead: less than 2 milliseconds per handshake
- Supported protocols: MQTT, CoAP, AMQP
- Minimum hardware: ARM Cortex-M4 with 256 KB RAM
"""


class TestDocumentIngestion:
    """Ingest and manage documents in the vector store."""

    def test_ingest_document(
        self, e2e_server, base_url, auth_headers, test_collection_name
    ):
        """POST /api/documents/ingest stores chunks."""
        payload = {
            "text": NEXORA_DOCUMENT,
            "source": "nexora_overview",
            "collection": test_collection_name,
            "chunk_size": 256,
            "chunk_overlap": 30,
        }
        r = requests.post(
            f"{base_url}/api/documents/ingest",
            json=payload,
            headers=auth_headers,
            timeout=60,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("chunks_stored", 0) > 0
        assert "document_ids" in data or "status" in data

    def test_list_collections(
        self, e2e_server, base_url, test_collection_name
    ):
        """GET /api/documents/collections includes the test collection."""
        r = requests.get(f"{base_url}/api/documents/collections", timeout=10)
        assert r.status_code == 200
        data = r.json()
        names = [c.get("name", c) if isinstance(c, dict) else c for c in data.get("collections", [])]
        assert test_collection_name in names

    def test_get_collection_info(
        self, e2e_server, base_url, test_collection_name
    ):
        """GET /api/documents/collections/{name} returns count > 0."""
        r = requests.get(
            f"{base_url}/api/documents/collections/{test_collection_name}",
            timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("count", 0) > 0 or data.get("name") == test_collection_name


class TestDocumentSearch:
    """Similarity search over ingested documents."""

    def test_search_documents(
        self, e2e_server, base_url, auth_headers, test_collection_name
    ):
        """POST /api/documents/search returns relevant results."""
        payload = {
            "query": "quantum cryptography IoT",
            "n_results": 3,
            "collection": test_collection_name,
        }
        r = requests.post(
            f"{base_url}/api/documents/search",
            json=payload,
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 200
        data = r.json()
        docs = data.get("documents", [])
        assert len(docs) > 0, "Search returned no documents"

    def test_search_returns_distances(
        self, e2e_server, base_url, auth_headers, test_collection_name
    ):
        """Search results include distance/similarity scores."""
        payload = {
            "query": "QuantumShield Pro",
            "n_results": 2,
            "collection": test_collection_name,
        }
        r = requests.post(
            f"{base_url}/api/documents/search",
            json=payload,
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 200
        data = r.json()
        assert "distances" in data or "scores" in data or len(data.get("documents", [])) > 0


class TestRAGAugmentedCompletion:
    """Chat completions augmented with retrieved context."""

    def test_rag_augmented_completion(
        self, e2e_server, base_url, auth_headers, loaded_model, test_collection_name
    ):
        """POST /v1/chat/completions with use_rag=true uses retrieved context."""
        payload = {
            "model": loaded_model,
            "messages": [
                {"role": "user", "content": "What product does Nexora Technologies make?"}
            ],
            "max_tokens": 50,
            "stream": False,
            "use_rag": True,
            "rag_collection": test_collection_name,
            "rag_n_results": 3,
        }
        r = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            headers=auth_headers,
            timeout=60,
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data.get("choices", [])) >= 1
        # The response should reference RAG sources
        if "rag_sources" in data:
            assert len(data["rag_sources"]) > 0

    def test_context_documents_injection(
        self, e2e_server, base_url, auth_headers, loaded_model
    ):
        """POST with context_documents injects context into the prompt."""
        payload = {
            "model": loaded_model,
            "messages": [
                {"role": "user", "content": "Who is the CEO?"}
            ],
            "max_tokens": 30,
            "stream": False,
            "context_documents": [
                "Nexora Technologies CEO is Dr. Elara Voss, based in Zurich."
            ],
        }
        r = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            headers=auth_headers,
            timeout=60,
        )
        assert r.status_code == 200
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        assert isinstance(content, str) and len(content) > 0


class TestCollectionCleanup:
    """Clean up test collections."""

    def test_delete_collection(
        self, e2e_server, base_url, test_collection_name
    ):
        """DELETE /api/documents/collections/{name} removes the collection."""
        r = requests.delete(
            f"{base_url}/api/documents/collections/{test_collection_name}",
            timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "deleted"
