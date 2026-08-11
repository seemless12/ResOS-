"""
RestaurantOS — Order Agent
Detects customer intent, extracts ordered items and quantities,
and creates a structured order using LLM.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from app.graph.state import RestaurantState
from app.models.schemas import (
    AgentLog,
    ExtractedOrder,
    Intent,
    OrderItem,
)
from app.prompts.templates import ORDER_EXTRACTION_PROMPT
from app.utils.llm import call_llm_json

logger = logging.getLogger(__name__)

AGENT_NAME = "OrderAgent"

# Fallback menu context when Knowledge Agent hasn't run yet
DEFAULT_MENU_CONTEXT = """
- Chicken Biryani: PKR 350
- Mutton Biryani: PKR 550
- Beef Burger: PKR 450
- Chicken Burger: PKR 350
- Margherita Pizza: PKR 800
- Pepperoni Pizza: PKR 950
- Caesar Salad: PKR 400
- French Fries: PKR 200
- Garlic Bread: PKR 250
- Soft Drink: PKR 100
- Fresh Juice: PKR 200
- Mineral Water: PKR 50
- Chocolate Cake: PKR 350
- Ice Cream: PKR 200
"""


def run_order_agent(state: dict) -> dict:
    """
    LangGraph node — Order Agent.

    Responsibilities:
      1. Detect customer intent (order, inquiry, complaint, etc.).
      2. Extract ordered items with quantities.
      3. Create a structured ExtractedOrder.

    Args:
        state: Current state dict from LangGraph.

    Returns:
        Updated state dict with intent and extracted order.
    """
    start = time.time()
    user_message = state.get("user_message", "")
    logger.info("[%s] Starting — message_length=%d", AGENT_NAME, len(user_message))

    try:
        # Use retrieved context if available, else use default menu
        menu_context = state.get("retrieved_context", "") or DEFAULT_MENU_CONTEXT

        current_order = json.dumps(state.get("extracted_order", {}), indent=2)

        # Build prompt
        prompt = ORDER_EXTRACTION_PROMPT.format(
            current_order=current_order,
            message=user_message,
            menu_context=menu_context,
        )

        # Call LLM for extraction
        result = call_llm_json(prompt)

        # Parse intent
        raw_intent = result.get("intent", "unknown").lower()
        try:
            detected_intent = Intent(raw_intent)
        except ValueError:
            detected_intent = Intent.UNKNOWN

        # Parse items
        items: list[dict[str, Any]] = result.get("items", [])

        # Deduplicate: merge items with the same name by summing quantities.
        # This prevents the LLM from creating e.g. 3 separate "Chicken Biryani"
        # entries with quantity 1 instead of 1 entry with quantity 3.
        deduped: dict[str, dict[str, Any]] = {}
        for item in items:
            key = item.get("name", "Unknown").strip().lower()
            if key in deduped:
                deduped[key]["quantity"] = deduped[key].get("quantity", 1) + item.get("quantity", 1)
                # Keep latest notes if present
                if item.get("notes"):
                    deduped[key]["notes"] = item["notes"]
            else:
                deduped[key] = {
                    "name": item.get("name", "Unknown").strip(),
                    "quantity": item.get("quantity", 1),
                    "notes": item.get("notes", ""),
                }
        items = list(deduped.values())

        order_items = []
        for item in items:
            order_items.append(
                OrderItem(
                    name=item.get("name", "Unknown"),
                    quantity=item.get("quantity", 1),
                    notes=item.get("notes", ""),
                ).model_dump()
            )

        extracted_order = ExtractedOrder(
            items=[OrderItem(**i) for i in order_items],
            special_instructions=result.get("special_instructions", ""),
        )

        duration_ms = (time.time() - start) * 1000

        log_entry = AgentLog(
            agent_name=AGENT_NAME,
            action="extract_order",
            message=f"Detected intent={detected_intent.value}, items={len(order_items)}",
            duration_ms=round(duration_ms, 2),
            success=True,
        )

        logger.info(
            "[%s] Completed — intent=%s, items=%d (%.1fms)",
            AGENT_NAME, detected_intent.value, len(order_items), duration_ms,
        )

        return {
            "detected_intent": detected_intent.value,
            "extracted_order": extracted_order.model_dump(),
            "current_agent": AGENT_NAME,
            "completed_agents": [AGENT_NAME],
            "logs": [log_entry.model_dump()],
        }

    except Exception as exc:
        duration_ms = (time.time() - start) * 1000
        logger.error("[%s] Failed: %s", AGENT_NAME, exc)

        log_entry = AgentLog(
            agent_name=AGENT_NAME,
            action="extract_order",
            message=f"Error: {str(exc)}",
            duration_ms=round(duration_ms, 2),
            success=False,
        )

        # Graceful fallback: treat as an inquiry with no items
        return {
            "detected_intent": Intent.UNKNOWN.value,
            "extracted_order": ExtractedOrder().model_dump(),
            "error": str(exc),
            "current_agent": AGENT_NAME,
            "completed_agents": [AGENT_NAME],
            "logs": [log_entry.model_dump()],
        }
