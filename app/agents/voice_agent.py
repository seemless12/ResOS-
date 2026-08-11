"""
RestaurantOS — Voice Confirmation Agent
Generates a human-friendly confirmation message for the customer.
For MVP: text only, no real voice integration.
"""

from __future__ import annotations

import logging
import time

from app.config import get_settings
from app.models.schemas import AgentLog, ExtractedOrder, ValidationResult
from app.prompts.templates import CONFIRMATION_PROMPT
from app.utils.llm import call_llm

logger = logging.getLogger(__name__)

AGENT_NAME = "VoiceConfirmationAgent"


def _build_order_summary(validation_result: dict) -> str:
    """Build a human-readable order summary from validation result."""
    validated_order = validation_result.get("validated_order", {})
    items = validated_order.get("items", [])

    if not items:
        return "No items in order."

    settings = get_settings()
    lines = []
    for item in items:
        name = item.get("name", "Unknown")
        qty = item.get("quantity", 1)
        total = item.get("total_price", 0)
        lines.append(f"  • {qty}x {name} — {settings.restaurant_currency} {total:.0f}")

    subtotal = validated_order.get("subtotal", 0)
    delivery_fee = validated_order.get("delivery_fee", 0)
    total = validated_order.get("total", 0)

    lines.append(f"\n  Subtotal: {settings.restaurant_currency} {subtotal:.0f}")
    if delivery_fee > 0:
        lines.append(f"  Delivery Fee: {settings.restaurant_currency} {delivery_fee:.0f}")
    else:
        lines.append("  Delivery: FREE")
    lines.append(f"  **Total: {settings.restaurant_currency} {total:.0f}**")

    if validated_order.get("special_instructions"):
        lines.append(f"\n  Special Instructions: {validated_order['special_instructions']}")

    return "\n".join(lines)


def _generate_fallback_confirmation(state: dict) -> str:
    """Generate confirmation without LLM as fallback."""
    settings = get_settings()
    customer = state.get("customer", {})
    ticket = state.get("ticket", {})
    validation = state.get("validation_result", {})
    intent = state.get("detected_intent", "unknown")

    customer_name = customer.get("name", "Customer") or "Customer"
    ticket_id = ticket.get("ticket_id", "N/A")

    if intent != "order":
        return f"Thank you for contacting {settings.restaurant_name}. How can we assist you with your order?"

    if validation.get("is_valid", False):
        order_summary = _build_order_summary(validation)
        return (
            f"Hello {customer_name},\n\n"
            f"Your order has been confirmed.\n\n"
            f"Ticket: {ticket_id}\n\n"
            f"Order Details:\n{order_summary}\n\n"
            f"Estimated delivery: 30-45 minutes.\n"
            f"Thank you for ordering from {settings.restaurant_name}."
        )
    else:
        errors = validation.get("errors", ["Unknown issue"])
        return (
            f"Hello {customer_name},\n\n"
            f"We could not process your order.\n\n"
            f"Issues found:\n" +
            "\n".join(f"  - {e}" for e in errors) +
            "\n\nPlease update your order and try again."
        )


def run_voice_agent(state: dict) -> dict:
    """
    LangGraph node — Voice Confirmation Agent.

    Responsibilities:
      1. Generate a customer-facing confirmation message.
      2. Use LLM for natural language generation.
      3. Fall back to template if LLM fails.

    Args:
        state: Current state dict from LangGraph.

    Returns:
        Updated state dict with confirmation_message and final_response.
    """
    start = time.time()
    logger.info("[%s] Starting confirmation generation", AGENT_NAME)

    try:
        settings = get_settings()
        customer = state.get("customer", {})
        ticket = state.get("ticket", {})
        validation = state.get("validation_result", {})

        customer_name = customer.get("name", "Valued Customer") or "Valued Customer"
        ticket_id = ticket.get("ticket_id", "N/A")
        channel = state.get("channel_source", "website")
        order_summary = _build_order_summary(validation)

        validation_status = "VALID ✅" if validation.get("is_valid") else "INVALID ❌"
        validation_details = ""
        if validation.get("errors"):
            validation_details += "Errors: " + "; ".join(validation["errors"])
        if validation.get("warnings"):
            validation_details += "\nWarnings: " + "; ".join(validation["warnings"])

        # Calculate missing details
        from app.session_manager import get_missing_details
        # We can simulate session-like missing details by checking the customer dict
        missing = []
        if not customer.get("name"): missing.append("Name")
        if not customer.get("phone"): missing.append("Phone Number")
        if not customer.get("address"): missing.append("Address")
        missing_details = ", ".join(missing) if missing else ""

        # Get history (last 5 turns to prevent context bloat)
        history_list = state.get("conversation_history", [])[-10:]
        history_str = "\n".join(history_list) if history_list else "None"

        # Try LLM-generated confirmation
        try:
            prompt = CONFIRMATION_PROMPT.format(
                customer_name=customer_name,
                channel=channel,
                intent=state.get("detected_intent", "unknown"),
                missing_details=missing_details,
                retrieved_context=state.get("retrieved_context", "None"),
                history=history_str,
                order_summary=order_summary,
                validation_status=validation_status,
                validation_details=validation_details or "None",
                restaurant_name=settings.restaurant_name,
                ticket_id=ticket_id,
            )

            confirmation = call_llm(prompt, temperature=0.7)
            if not confirmation or len(confirmation) < 20:
                raise ValueError("LLM response too short")

        except Exception as llm_exc:
            logger.warning("[%s] LLM failed, using fallback: %s", AGENT_NAME, llm_exc)
            confirmation = _generate_fallback_confirmation(state)

        duration_ms = (time.time() - start) * 1000

        log_entry = AgentLog(
            agent_name=AGENT_NAME,
            action="generate_confirmation",
            message=f"Generated confirmation message ({len(confirmation)} chars)",
            duration_ms=round(duration_ms, 2),
            success=True,
        )

        logger.info("[%s] Completed (%.1fms)", AGENT_NAME, duration_ms)

        return {
            "confirmation_message": confirmation,
            "final_response": confirmation,
            "conversation_history": [f"Bot: {confirmation}"],
            "current_agent": AGENT_NAME,
            "completed_agents": [AGENT_NAME],
            "logs": [log_entry.model_dump()],
        }

    except Exception as exc:
        duration_ms = (time.time() - start) * 1000
        logger.error("[%s] Failed: %s", AGENT_NAME, exc)

        fallback = _generate_fallback_confirmation(state)

        log_entry = AgentLog(
            agent_name=AGENT_NAME,
            action="generate_confirmation",
            message=f"Error: {str(exc)} — used fallback",
            duration_ms=round(duration_ms, 2),
            success=False,
        )

        return {
            "confirmation_message": fallback,
            "final_response": fallback,
            "conversation_history": [f"Bot: {fallback}"],
            "error": str(exc),
            "current_agent": AGENT_NAME,
            "completed_agents": [AGENT_NAME],
            "logs": [log_entry.model_dump()],
        }
