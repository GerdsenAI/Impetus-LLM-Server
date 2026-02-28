"""
Naive RAG pipeline — retrieves relevant docs and formats them as LLM context.
"""

from loguru import logger

from .vector_store import vector_store_service


def build_rag_context(
    query: str,
    n_results: int = 5,
    collection_name: str | None = None,
) -> tuple[str, list[dict]]:
    """Retrieve relevant documents and format as LLM context.

    Args:
        query: The user's query to search for.
        n_results: Number of documents to retrieve.
        collection_name: Optional collection to search in.

    Returns:
        Tuple of (context_string, source_documents).
        context_string is empty if no results found.
    """
    try:
        results = vector_store_service.search(
            query=query,
            n_results=n_results,
            collection_name=collection_name,
        )
    except Exception as e:
        logger.warning(f"RAG search failed: {e}")
        return "", []

    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])
    distances = results.get("distances", [])

    if not documents:
        return "", []

    # Build numbered context string
    context_parts = [
        "Use the following context to answer the question. "
        "Cite sources using [N] notation.\n"
    ]
    sources: list[dict] = []

    for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances, strict=True), start=1):
        context_parts.append(f"[{i}] {doc}")

        # Relevance score: cosine distance -> similarity
        relevance = max(0.0, 1.0 - dist)

        sources.append({
            "text": doc[:200] + "..." if len(doc) > 200 else doc,
            "source": meta.get("source", "unknown"),
            "relevance": round(relevance, 3),
            "chunk_index": meta.get("chunk_index", 0),
        })

    # Sort sources by relevance (highest first)
    sources.sort(key=lambda s: s["relevance"], reverse=True)

    context_str = "\n\n".join(context_parts)
    logger.info(f"RAG context built: {len(sources)} sources for query '{query[:50]}...'")

    return context_str, sources
