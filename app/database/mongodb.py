"""
RestaurantOS — MongoDB Client
Handles all database operations: customers, tickets, orders, logs,
AND the knowledge base for RAG (replacing ChromaDB).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient, TEXT
from pymongo.database import Database

from app.config import get_settings

logger = logging.getLogger(__name__)

# ── Singleton clients ────────────────────────────────────────────────────────

_async_client: Optional[AsyncIOMotorClient] = None
_async_db: Optional[AsyncIOMotorDatabase] = None
_sync_client: Optional[MongoClient] = None
_sync_db: Optional[Database] = None


# ═══════════════════════════════════════════════════════════════════════════════
#  ASYNC CLIENT  (used by FastAPI)
# ═══════════════════════════════════════════════════════════════════════════════

async def get_async_db() -> AsyncIOMotorDatabase:
    """Return the async Motor database (creates client on first call)."""
    global _async_client, _async_db
    if _async_db is None:
        settings = get_settings()
        _async_client = AsyncIOMotorClient(settings.mongodb_uri)
        _async_db = _async_client[settings.mongodb_db_name]
        logger.info("Async MongoDB connected → %s", settings.mongodb_db_name)
    return _async_db


async def close_async_db() -> None:
    """Close the async MongoDB connection."""
    global _async_client, _async_db
    if _async_client:
        _async_client.close()
        _async_client = None
        _async_db = None
        logger.info("Async MongoDB connection closed.")


# ═══════════════════════════════════════════════════════════════════════════════
#  SYNC CLIENT  (used by LangGraph agents & Streamlit)
# ═══════════════════════════════════════════════════════════════════════════════

def get_sync_db() -> Database:
    """Return the synchronous PyMongo database."""
    global _sync_client, _sync_db
    if _sync_db is None:
        settings = get_settings()
        _sync_client = MongoClient(settings.mongodb_uri)
        _sync_db = _sync_client[settings.mongodb_db_name]
        logger.info("Sync MongoDB connected → %s", settings.mongodb_db_name)
    return _sync_db


def close_sync_db() -> None:
    """Close the sync MongoDB connection."""
    global _sync_client, _sync_db
    if _sync_client:
        _sync_client.close()
        _sync_client = None
        _sync_db = None


# ═══════════════════════════════════════════════════════════════════════════════
#  TICKET OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def save_ticket(ticket_data: dict) -> str:
    """Insert or update a ticket document. Returns the ticket_id."""
    db = get_sync_db()
    ticket_data = ticket_data.copy()
    ticket_id = ticket_data.get("ticket", {}).get("ticket_id", "")
    ticket_data["_id"] = ticket_id
    ticket_data["updated_at"] = datetime.utcnow().isoformat()

    db.tickets.replace_one({"_id": ticket_id}, ticket_data, upsert=True)
    logger.info("Saved ticket %s", ticket_id)
    return ticket_id


async def async_save_ticket(ticket_data: dict) -> str:
    """Async version — insert or update a ticket."""
    db = await get_async_db()
    ticket_data = ticket_data.copy()
    ticket_id = ticket_data.get("ticket", {}).get("ticket_id", "")
    ticket_data["_id"] = ticket_id
    ticket_data["updated_at"] = datetime.utcnow().isoformat()

    await db.tickets.replace_one({"_id": ticket_id}, ticket_data, upsert=True)
    logger.info("Async saved ticket %s", ticket_id)
    return ticket_id


def get_ticket(ticket_id: str) -> Optional[dict]:
    """Retrieve a ticket by its ID."""
    db = get_sync_db()
    return db.tickets.find_one({"_id": ticket_id})


async def async_get_ticket(ticket_id: str) -> Optional[dict]:
    """Async version — retrieve a ticket by ID."""
    db = await get_async_db()
    return await db.tickets.find_one({"_id": ticket_id})


def get_all_tickets(limit: int = 50) -> list[dict]:
    """Return the most recent tickets."""
    db = get_sync_db()
    return list(
        db.tickets.find()
        .sort("updated_at", -1)
        .limit(limit)
    )


async def async_get_all_tickets(limit: int = 50) -> list[dict]:
    """Async — return the most recent tickets."""
    db = await get_async_db()
    cursor = db.tickets.find().sort("updated_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


# ═══════════════════════════════════════════════════════════════════════════════
#  ORDER OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def save_order(ticket_id: str, order_data: dict) -> None:
    """Save a structured order linked to a ticket."""
    db = get_sync_db()
    order_data = order_data.copy()
    order_data["ticket_id"] = ticket_id
    order_data["created_at"] = datetime.utcnow().isoformat()
    db.orders.replace_one({"ticket_id": ticket_id}, order_data, upsert=True)


async def async_save_order(ticket_id: str, order_data: dict) -> None:
    """Async — save order."""
    db = await get_async_db()
    order_data = order_data.copy()
    order_data["ticket_id"] = ticket_id
    order_data["created_at"] = datetime.utcnow().isoformat()
    await db.orders.replace_one({"ticket_id": ticket_id}, order_data, upsert=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  CUSTOMER OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def save_customer(customer_data: dict) -> None:
    """Upsert a customer document (keyed by phone or name)."""
    db = get_sync_db()
    customer_data = customer_data.copy()
    key = customer_data.get("phone") or customer_data.get("name") or "anonymous"
    customer_data["_id"] = key
    customer_data["updated_at"] = datetime.utcnow().isoformat()
    db.customers.replace_one({"_id": key}, customer_data, upsert=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  LOG OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def save_logs(ticket_id: str, logs: list[dict]) -> None:
    """Append execution logs for a ticket."""
    db = get_sync_db()
    if logs:
        logs_to_insert = []
        for log in logs:
            log_copy = log.copy()
            log_copy["ticket_id"] = ticket_id
            logs_to_insert.append(log_copy)
        db.logs.insert_many(logs_to_insert)


async def async_save_logs(ticket_id: str, logs: list[dict]) -> None:
    """Async — append execution logs."""
    db = await get_async_db()
    if logs:
        logs_to_insert = []
        for log in logs:
            log_copy = log.copy()
            log_copy["ticket_id"] = ticket_id
            logs_to_insert.append(log_copy)
        await db.logs.insert_many(logs_to_insert)


def get_logs_for_ticket(ticket_id: str) -> list[dict]:
    """Get all logs for a specific ticket."""
    db = get_sync_db()
    return list(db.logs.find({"ticket_id": ticket_id}).sort("timestamp", 1))


# ═══════════════════════════════════════════════════════════════════════════════
#  KNOWLEDGE BASE (RAG via MongoDB)
# ═══════════════════════════════════════════════════════════════════════════════

def _ensure_text_index() -> None:
    """Create a text index on the knowledge collection if it doesn't exist."""
    db = get_sync_db()
    existing = db.knowledge.index_information()
    if "text_search" not in existing:
        db.knowledge.create_index(
            [("text", TEXT)],
            name="text_search",
            default_language="english",
        )
        logger.info("Created text index on knowledge collection.")


def seed_knowledge_base(documents: list[dict], force: bool = False) -> int:
    """
    Seed the knowledge collection with restaurant data.

    Args:
        documents: List of dicts with 'id', 'text', 'metadata' keys.
        force: If True, drop and re-seed.

    Returns:
        Number of documents in the collection.
    """
    db = get_sync_db()

    count = db.knowledge.count_documents({})
    if count > 0 and not force:
        logger.info("Knowledge base already seeded (%d docs). Skipping.", count)
        _ensure_text_index()
        return count

    if force:
        db.knowledge.drop()
        logger.info("Dropped knowledge collection for re-seeding.")

    # Insert all documents
    mongo_docs = []
    for doc in documents:
        mongo_docs.append({
            "_id": doc["id"],
            "text": doc["text"],
            "doc_type": doc["metadata"].get("type", "unknown"),
            "category": doc["metadata"].get("category", ""),
            "name": doc["metadata"].get("name", ""),
            "price": doc["metadata"].get("price", 0),
            "metadata": doc["metadata"],
        })

    if mongo_docs:
        db.knowledge.insert_many(mongo_docs)

    _ensure_text_index()
    logger.info("Seeded knowledge base with %d documents.", len(mongo_docs))
    return len(mongo_docs)


def query_knowledge(query: str, n_results: int = 10, filter_type: Optional[str] = None) -> list[dict]:
    """
    Search the knowledge base using MongoDB text search.

    Args:
        query: Search query.
        n_results: Max results.
        filter_type: Optional filter (menu, faq, policy, delivery).

    Returns:
        List of matching documents.
    """
    db = get_sync_db()

    # Build the filter
    search_filter: dict[str, Any] = {}
    if filter_type:
        search_filter["doc_type"] = filter_type

    # Try text search first
    try:
        search_filter["$text"] = {"$search": query}
        cursor = db.knowledge.find(
            search_filter,
            {"score": {"$meta": "textScore"}},
        ).sort([("score", {"$meta": "textScore"})]).limit(n_results)

        results = list(cursor)
        if results:
            return [{"text": r["text"], "metadata": r.get("metadata", {})} for r in results]
    except Exception as e:
        logger.warning("Text search failed, falling back to regex: %s", e)

    # Fallback: simple regex search on individual words
    search_filter.pop("$text", None)
    words = query.lower().split()
    if words:
        regex_pattern = "|".join(words[:5])  # Limit to first 5 words
        search_filter["text"] = {"$regex": regex_pattern, "$options": "i"}

    cursor = db.knowledge.find(search_filter).limit(n_results)
    results = list(cursor)
    return [{"text": r["text"], "metadata": r.get("metadata", {})} for r in results]


def get_menu_items() -> list[dict]:
    """Get all menu items from the knowledge base."""
    db = get_sync_db()
    return list(db.knowledge.find({"doc_type": "menu"}))


# ═══════════════════════════════════════════════════════════════════════════════
#  INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def init_database() -> None:
    """Initialize database: seed knowledge base and create indexes."""
    from app.rag.restaurant_data import get_all_documents

    db = get_sync_db()
    logger.info("Initializing database...")

    # Seed knowledge base
    documents = get_all_documents()
    seed_knowledge_base(documents, force=False)

    # Create indexes on other collections
    db.tickets.create_index("updated_at")
    db.orders.create_index("ticket_id")
    db.logs.create_index("ticket_id")
    db.customers.create_index("phone")

    logger.info("Database initialization complete.")
