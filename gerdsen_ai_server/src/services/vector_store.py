"""
VectorStoreService — ChromaDB wrapper for document storage and similarity search.

Uses PersistentClient for data that survives restarts.
Lazy-initialised: ChromaDB doesn't start until first use (fast server startup).
"""

import uuid

from loguru import logger

from ..config.settings import settings
from ..utils.document_chunker import chunk_text


class VectorStoreService:
    """ChromaDB-backed vector store with lazy initialisation."""

    def __init__(self, persist_dir: str | None = None):
        self._persist_dir = persist_dir
        self._client = None
        self._embedding_fn = None

    # ------------------------------------------------------------------
    # Lazy init
    # ------------------------------------------------------------------

    @property
    def client(self):
        if self._client is None:
            import chromadb

            persist_dir = self._persist_dir or str(settings.vectorstore.persist_directory)
            self._client = chromadb.PersistentClient(path=persist_dir)
            logger.info(f"ChromaDB PersistentClient initialised at {persist_dir}")
        return self._client

    @property
    def embedding_fn(self):
        if self._embedding_fn is None:
            from .embedding_bridge import ImpetusEmbeddingFunction

            model = settings.vectorstore.embedding_model
            self._embedding_fn = ImpetusEmbeddingFunction(model_name=model)
            logger.info(f"Embedding bridge initialised with model '{model}'")
        return self._embedding_fn

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def get_or_create_collection(self, name: str | None = None):
        """Get or create a ChromaDB collection with cosine similarity."""
        name = name or settings.vectorstore.default_collection
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def list_collections(self) -> list[dict]:
        """List all collections with document counts."""
        collections = self.client.list_collections()
        result = []
        for col in collections:
            # Re-fetch with embedding fn to get accurate count
            collection = self.client.get_collection(col.name, embedding_function=self.embedding_fn)
            result.append({
                "name": col.name,
                "count": collection.count(),
                "metadata": col.metadata or {},
            })
        return result

    def get_collection_info(self, name: str) -> dict:
        """Get detailed info about a single collection."""
        collection = self.client.get_collection(name, embedding_function=self.embedding_fn)
        return {
            "name": name,
            "count": collection.count(),
            "metadata": collection.metadata or {},
        }

    def delete_collection(self, name: str) -> None:
        """Delete an entire collection."""
        self.client.delete_collection(name)
        logger.info(f"Deleted collection '{name}'")

    # ------------------------------------------------------------------
    # Document operations
    # ------------------------------------------------------------------

    def ingest_text(
        self,
        text: str,
        source: str = "unknown",
        collection_name: str | None = None,
        metadata: dict | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> dict:
        """Chunk text and store embeddings in ChromaDB.

        Returns dict with status, chunks_stored, collection, source, document_ids.
        """
        collection = self.get_or_create_collection(collection_name)

        cs = chunk_size or settings.vectorstore.chunk_size
        co = chunk_overlap or settings.vectorstore.chunk_overlap

        chunks = chunk_text(text, chunk_size=cs, chunk_overlap=co)
        if not chunks:
            return {
                "status": "empty",
                "chunks_stored": 0,
                "collection": collection.name,
                "source": source,
                "document_ids": [],
            }

        doc_ids = [f"{source}_{uuid.uuid4().hex[:8]}" for _ in chunks]
        documents = [c.text for c in chunks]
        metadatas = []
        for c in chunks:
            m = {"source": source, "chunk_index": c.index}
            m.update(c.metadata)
            if metadata:
                m.update(metadata)
            metadatas.append(m)

        collection.add(
            ids=doc_ids,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(f"Ingested {len(chunks)} chunks from '{source}' into '{collection.name}'")

        return {
            "status": "success",
            "chunks_stored": len(chunks),
            "collection": collection.name,
            "source": source,
            "document_ids": doc_ids,
        }

    def search(
        self,
        query: str,
        n_results: int = 5,
        collection_name: str | None = None,
        where: dict | None = None,
    ) -> dict:
        """Similarity search using the query text.

        ChromaDB calls our ImpetusEmbeddingFunction to embed the query.
        """
        collection = self.get_or_create_collection(collection_name)

        kwargs: dict = {
            "query_texts": [query],
            "n_results": min(n_results, collection.count() or 1),
        }
        if where:
            kwargs["where"] = where

        results = collection.query(**kwargs)

        return {
            "documents": results.get("documents", [[]])[0],
            "metadatas": results.get("metadatas", [[]])[0],
            "distances": results.get("distances", [[]])[0],
            "count": len(results.get("documents", [[]])[0]),
            "query": query,
        }

    def delete_documents(
        self,
        ids: list[str] | None = None,
        where: dict | None = None,
        collection_name: str | None = None,
    ) -> None:
        """Delete documents by ID or filter."""
        collection = self.get_or_create_collection(collection_name)

        kwargs: dict = {}
        if ids:
            kwargs["ids"] = ids
        if where:
            kwargs["where"] = where

        collection.delete(**kwargs)


# Singleton instance
vector_store_service = VectorStoreService()
