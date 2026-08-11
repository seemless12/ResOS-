"""
RestaurantOS — RAG Retriever (MongoDB-backed)
High-level retrieval logic for restaurant knowledge using MongoDB text search.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.database.mongodb import query_knowledge, init_database

logger = logging.getLogger(__name__)


def ensure_knowledge_base() -> None:
    """Ensure the knowledge base is seeded on startup."""
    init_database()
    logger.info("MongoDB knowledge base ready.")


def retrieve_menu_context(query: str, n_results: int = 8) -> str:
    """
    Retrieve relevant menu items for a given query.

    Args:
        query: Customer message or search query.
        n_results: Number of results to fetch.

    Returns:
        Formatted string of relevant menu information.
    """
    results = query_knowledge(query, n_results=n_results, filter_type="menu")
    if not results:
        return "No menu items found."

    lines = []
    for r in results:
        lines.append(f"- {r['text']}")
    return "\n".join(lines)


def retrieve_full_context(query: str, n_results: int = 10) -> str:
    """
    Retrieve all relevant knowledge (menu, FAQs, policies, delivery).

    Args:
        query: Customer message.
        n_results: Total results to fetch.

    Returns:
        Formatted context string.
    """
    results = query_knowledge(query, n_results=n_results)
    if not results:
        return "No relevant information found."

    sections: dict[str, list[str]] = {
        "menu": [],
        "faq": [],
        "policy": [],
        "delivery": [],
    }

    for r in results:
        doc_type = r.get("metadata", {}).get("type", "menu")
        sections.setdefault(doc_type, []).append(f"  - {r['text']}")

    output_parts = []
    if sections["menu"]:
        output_parts.append("**Menu Items:**\n" + "\n".join(sections["menu"]))
    if sections["faq"]:
        output_parts.append("**FAQs:**\n" + "\n".join(sections["faq"]))
    if sections["policy"]:
        output_parts.append("**Policies:**\n" + "\n".join(sections["policy"]))
    if sections["delivery"]:
        output_parts.append("**Delivery Info:**\n" + "\n".join(sections["delivery"]))

    return "\n\n".join(output_parts) if output_parts else "No relevant information found."


def retrieve_policies() -> str:
    """Retrieve all restaurant policies."""
    results = query_knowledge("restaurant policies rules", n_results=10, filter_type="policy")
    if not results:
        return "No policies found."
    return "\n".join(f"- {r['text']}" for r in results)
