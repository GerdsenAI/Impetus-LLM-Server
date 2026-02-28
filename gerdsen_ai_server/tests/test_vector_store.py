"""
Tests for VectorStoreService using ChromaDB EphemeralClient.

Uses a lightweight test embedding function so tests run
without MLX or coremltools.
"""

import chromadb
import pytest
from chromadb.api.types import (
    Documents,
    EmbeddingFunction,
    Embeddings,
)
from src.services.vector_store import VectorStoreService


class _TestEmbeddingFunction(EmbeddingFunction[Documents]):
    """Deterministic embedding function for tests.

    Returns fixed 384-dim vectors.
    """

    def __call__(self, input: Documents) -> Embeddings:  # noqa: A002
        # Simple hash-based vectors so different texts get different embeddings
        result = []
        for text in input:
            h = hash(text) % 1000
            result.append([(h + i) / 1000.0 for i in range(384)])
        return result


@pytest.fixture
def vector_store(tmp_path: object) -> VectorStoreService:
    """Create a VectorStoreService backed by an ephemeral client."""
    svc = VectorStoreService(persist_dir=str(tmp_path / "chroma"))
    svc._client = chromadb.EphemeralClient()
    svc._embedding_fn = _TestEmbeddingFunction()
    return svc


class TestVectorStoreService:

    def test_ingest_and_search(
        self, vector_store: VectorStoreService,
    ) -> None:
        result = vector_store.ingest_text(
            text="ChromaDB is a vector database for AI applications.",
            source="test.txt",
            collection_name="search_test",
        )
        assert result["status"] == "success"
        assert result["chunks_stored"] >= 1
        assert result["source"] == "test.txt"
        assert len(result["document_ids"]) >= 1

        search_result = vector_store.search(
            "vector database", collection_name="search_test",
        )
        assert search_result["count"] >= 1
        assert "ChromaDB" in search_result["documents"][0]

    def test_empty_text_ingest(
        self, vector_store: VectorStoreService,
    ) -> None:
        result = vector_store.ingest_text(text="   ", source="empty.txt")
        assert result["status"] == "empty"
        assert result["chunks_stored"] == 0

    def test_search_empty_collection(
        self, vector_store: VectorStoreService,
    ) -> None:
        vector_store.get_or_create_collection("empty_col")
        result = vector_store.search("anything", collection_name="empty_col")
        assert result["count"] == 0

    def test_list_collections(
        self, vector_store: VectorStoreService,
    ) -> None:
        vector_store.get_or_create_collection("col_a")
        vector_store.get_or_create_collection("col_b")
        collections = vector_store.list_collections()
        names = [c["name"] for c in collections]
        assert "col_a" in names
        assert "col_b" in names

    def test_get_collection_info(
        self, vector_store: VectorStoreService,
    ) -> None:
        vector_store.ingest_text(
            "Some content.",
            source="s.txt",
            collection_name="info_test",
        )
        info = vector_store.get_collection_info("info_test")
        assert info["name"] == "info_test"
        assert info["count"] >= 1

    def test_delete_collection(
        self, vector_store: VectorStoreService,
    ) -> None:
        vector_store.get_or_create_collection("to_delete")
        vector_store.delete_collection("to_delete")
        collections = vector_store.list_collections()
        names = [c["name"] for c in collections]
        assert "to_delete" not in names

    def test_ingest_with_metadata(
        self, vector_store: VectorStoreService,
    ) -> None:
        result = vector_store.ingest_text(
            text="Metadata test document.",
            source="meta.txt",
            metadata={"author": "tester"},
            collection_name="meta_test",
        )
        assert result["status"] == "success"

        search_result = vector_store.search(
            "metadata test", collection_name="meta_test",
        )
        assert search_result["count"] >= 1
        assert search_result["metadatas"][0]["source"] == "meta.txt"

    def test_ingest_custom_chunk_size(
        self, vector_store: VectorStoreService,
    ) -> None:
        long_text = "word " * 500  # ~2500 chars
        result = vector_store.ingest_text(
            text=long_text,
            source="long.txt",
            chunk_size=100,
            chunk_overlap=10,
        )
        assert result["chunks_stored"] > 1

    def test_delete_documents_by_id(
        self, vector_store: VectorStoreService,
    ) -> None:
        result = vector_store.ingest_text(
            "Delete me.", source="del.txt", collection_name="delete_test"
        )
        doc_ids = result["document_ids"]
        assert len(doc_ids) >= 1

        vector_store.delete_documents(
            ids=doc_ids, collection_name="delete_test",
        )
        collection = vector_store.get_or_create_collection("delete_test")
        assert collection.count() == 0
