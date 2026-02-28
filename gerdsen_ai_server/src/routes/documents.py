"""
Document management endpoints — ingest, search, and collection CRUD.
"""

from flask import Blueprint, jsonify
from loguru import logger

from ..schemas.openai_schemas import (
    DocumentIngestRequest,
    DocumentSearchRequest,
)
from ..services.vector_store import vector_store_service
from ..utils.validation import validate_json

bp = Blueprint("documents", __name__)


@bp.route("/ingest", methods=["POST"])
@validate_json(DocumentIngestRequest)
def ingest_document(validated_data: DocumentIngestRequest):
    """Chunk + embed + store a text document."""
    try:
        result = vector_store_service.ingest_text(
            text=validated_data.text,
            source=validated_data.source,
            collection_name=validated_data.collection,
            metadata=validated_data.metadata,
            chunk_size=validated_data.chunk_size,
            chunk_overlap=validated_data.chunk_overlap,
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Document ingest error: {e}")
        return jsonify({"error": {"message": str(e), "type": "server_error"}}), 500


@bp.route("/search", methods=["POST"])
@validate_json(DocumentSearchRequest)
def search_documents(validated_data: DocumentSearchRequest):
    """Similarity search across stored documents."""
    try:
        result = vector_store_service.search(
            query=validated_data.query,
            n_results=validated_data.n_results,
            collection_name=validated_data.collection,
            where=validated_data.where,
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Document search error: {e}")
        return jsonify({"error": {"message": str(e), "type": "server_error"}}), 500


@bp.route("/collections", methods=["GET"])
def list_collections():
    """List all vector store collections."""
    try:
        collections = vector_store_service.list_collections()
        return jsonify({"collections": collections, "count": len(collections)})
    except Exception as e:
        logger.error(f"List collections error: {e}")
        return jsonify({"error": {"message": str(e), "type": "server_error"}}), 500


@bp.route("/collections/<name>", methods=["GET"])
def get_collection(name: str):
    """Get info about a specific collection."""
    try:
        info = vector_store_service.get_collection_info(name)
        return jsonify(info)
    except Exception as e:
        logger.error(f"Get collection error: {e}")
        return jsonify({"error": {"message": f"Collection '{name}' not found", "type": "not_found"}}), 404


@bp.route("/collections/<name>", methods=["DELETE"])
def delete_collection(name: str):
    """Delete an entire collection."""
    try:
        vector_store_service.delete_collection(name)
        return jsonify({"status": "deleted", "collection": name})
    except Exception as e:
        logger.error(f"Delete collection error: {e}")
        return jsonify({"error": {"message": str(e), "type": "server_error"}}), 500
