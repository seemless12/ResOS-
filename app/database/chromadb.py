"""
RestaurantOS — ChromaDB Client
Manages the vector store for restaurant knowledge retrieval (RAG).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings
from app.rag.restaurant_data import get_all_documents

logger = logging.getLogger(__name__)

# Module-level singleton
_client: Optional[chromadb.ClientAPI] = None
_collection: Optional[chromadb.Collection] = None


def get_chroma_client() -> chromadb.ClientAPI:
    """Return a persistent ChromaDB client (singleton)."""
    global _client
    if _client is None:
        settings = get_settings()
        persist_dir = Path(settings.chromadb_persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(persist_dir))
        logger.info("ChromaDB client initialized at %s", persist_dir)
    return _client


def get_collection() -> chromadb.Collection:
    """Return the restaurant knowledge collection, creating it if needed."""
    global _collection
    if _collection is None:
        settings = get_settings()
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=settings.chromadb_collection_name,
            metadata={"description": "Restaurant menu, FAQs, policies, delivery info"},
        )
        logger.info(
            "ChromaDB collection '%s' ready (count=%d)",
            settings.chromadb_collection_name,
            _collection.count(),
        )
    return _collection


def seed_knowledge_base(force: bool = False) -> int:
    """
    Seed ChromaDB with restaurant knowledge data.

    Args:
        force: If True, re-seed even if data already exists.

    Returns:
        Number of documents added.
    """
    collection = get_collection()

    if collection.count() > 0 and not force:
        logger.info("Knowledge base already seeded (%d docs). Skipping.", collection.count())
        return collection.count()

    # Clear existing data if forcing
    if force and collection.count() > 0:
        # Get all existing IDs and delete them
        existing = collection.get()
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
        logger.info("Cleared existing knowledge base for re-seeding.")

    documents = get_all_documents()

    # Batch upsert
    ids = [doc["id"] for doc in documents]
    texts = [doc["text"] for doc in documents]
    metadatas = [doc["metadata"] for doc in documents]

    collection.upsert(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
    )

    logger.info("Seeded knowledge base with %d documents.", len(documents))
    return len(documents)


def query_knowledge(
    query: str,
    n_results: int = 5,
    filter_type: Optional[str] = None,
) -> list[dict]:
    """
    Query the knowledge base for relevant documents.

    Args:
        query: The search query text.
        n_results: Maximum number of results to return.
        filter_type: Optional filter by document type (menu, faq, policy, delivery).

    Returns:
        List of result dicts with 'text', 'metadata', and 'distance' keys.
    """
    collection = get_collection()

    where_filter = None
    if filter_type:
        where_filter = {"type": filter_type}

    try:
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count()) if collection.count() > 0 else 1,
            where=where_filter,
        )
    except Exception as exc:
        logger.error("ChromaDB query failed: %s", exc)
        return []

    output = []
    if results and results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            output.append({
                "text": doc,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 0.0,
            })

    return output
