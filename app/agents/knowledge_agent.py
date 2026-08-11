"""
RestaurantOS — Knowledge Agent
Uses ChromaDB to retrieve restaurant menu, FAQs, policies, and delivery
information. Injects retrieved context into RestaurantState for downstream agents.
"""

from __future__ import annotations

import logging
import time

from app.models.schemas import AgentLog
from app.rag.retriever import retrieve_full_context

logger = logging.getLogger(__name__)

AGENT_NAME = "KnowledgeAgent"


def run_knowledge_agent(state: dict) -> dict:
    """
    LangGraph node — Knowledge Agent.

    Responsibilities:
      1. Query ChromaDB with the customer message.
      2. Retrieve relevant menu items, FAQs, policies, delivery info.
      3. Store retrieved context in state for Validation & Voice agents.

    Args:
        state: Current state dict from LangGraph.

    Returns:
        Updated state dict with retrieved_context.
    """
    start = time.time()
    user_message = state.get("user_message", "")
    logger.info("[%s] Starting — query_length=%d", AGENT_NAME, len(user_message))

    try:
        # Retrieve full context from ChromaDB/MongoDB (high limit to include all pizzas if asked for full menu)
        context = retrieve_full_context(user_message, n_results=50)

        duration_ms = (time.time() - start) * 1000

        log_entry = AgentLog(
            agent_name=AGENT_NAME,
            action="retrieve_knowledge",
            message=f"Retrieved {len(context)} chars of context from knowledge base",
            duration_ms=round(duration_ms, 2),
            success=True,
        )

        logger.info(
            "[%s] Completed — context_length=%d (%.1fms)",
            AGENT_NAME, len(context), duration_ms,
        )

        return {
            "retrieved_context": context,
            "current_agent": AGENT_NAME,
            "completed_agents": [AGENT_NAME],
            "logs": [log_entry.model_dump()],
        }

    except Exception as exc:
        duration_ms = (time.time() - start) * 1000
        logger.error("[%s] Failed: %s", AGENT_NAME, exc)

        log_entry = AgentLog(
            agent_name=AGENT_NAME,
            action="retrieve_knowledge",
            message=f"Error: {str(exc)}",
            duration_ms=round(duration_ms, 2),
            success=False,
        )

        return {
            "retrieved_context": "",
            "error": str(exc),
            "current_agent": AGENT_NAME,
            "completed_agents": [AGENT_NAME],
            "logs": [log_entry.model_dump()],
        }
