"""
RestaurantOS — LangGraph Workflow
Connects all agents into a sequential workflow using LangGraph.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, TypedDict, Annotated

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.channel_agent import run_channel_agent
from app.agents.order_agent import run_order_agent
from app.agents.knowledge_agent import run_knowledge_agent
from app.agents.validation_agent import run_validation_agent
from app.agents.voice_agent import run_voice_agent
from app.agents.calling_agent import run_calling_agent
from app.database.mongodb import save_ticket, save_order, save_customer, save_logs
from app.models.schemas import AgentLog, TicketStatus

logger = logging.getLogger(__name__)


# ── LangGraph State Schema ──────────────────────────────────────────────────

def _merge_lists(left: list, right: list) -> list:
    """Reducer: append new items to existing list."""
    return left + right

def _merge_dicts(left: dict, right: dict) -> dict:
    """Reducer: update left dict with right dict."""
    if not left: return right.copy() if right else {}
    if not right: return left.copy()
    merged = left.copy()
    merged.update(right)
    return merged


class GraphState(TypedDict, total=False):
    """State schema for LangGraph — uses reducers for list fields."""
    # Input
    user_message: str
    channel_source: str
    customer: Annotated[dict, _merge_dicts]
    # Ticket
    ticket: dict
    # Order Agent
    detected_intent: str
    extracted_order: dict
    order_status: str  # new: gathering_items, upselling, gathering_details, confirmed
    upsell_offered: bool
    missing_details: list[str]
    conversation_history: Annotated[list[str], _merge_lists]  # new
    # Knowledge Agent
    retrieved_context: str
    # Validation Agent
    validation_result: dict
    # Voice Agent
    confirmation_message: str
    final_response: str
    # Calling Agent
    call_script: str
    call_audio_path: str
    # Orchestrator
    current_agent: str
    completed_agents: Annotated[list[str], _merge_lists]
    logs: Annotated[list[dict], _merge_lists]
    # Error
    error: str


# ── Save Order Node ─────────────────────────────────────────────────────────

def save_order_node(state: dict) -> dict:
    """
    LangGraph node — Save the completed order to MongoDB.

    Stores ticket, order, customer, and logs.
    """
    start = time.time()
    logger.info("[SaveOrder] Persisting to MongoDB...")

    try:
        ticket = state.get("ticket", {})
        ticket_id = ticket.get("ticket_id", "UNKNOWN")

        # Update ticket status
        ticket["status"] = (
            TicketStatus.COMPLETED.value
            if state.get("validation_result", {}).get("is_valid", False)
            else TicketStatus.FAILED.value
        )
        ticket["updated_at"] = datetime.utcnow().isoformat()

        # Build the full ticket document
        ticket_doc = {
            "ticket": ticket,
            "customer": state.get("customer", {}),
            "channel_source": state.get("channel_source", "website"),
            "user_message": state.get("user_message", ""),
            "detected_intent": state.get("detected_intent", "unknown"),
            "extracted_order": state.get("extracted_order", {}),
            "retrieved_context": state.get("retrieved_context", ""),
            "validation_result": state.get("validation_result", {}),
            "confirmation_message": state.get("confirmation_message", ""),
            "final_response": state.get("final_response", ""),
            "call_script": state.get("call_script", ""),
            "call_audio_path": state.get("call_audio_path", ""),
            "completed_agents": state.get("completed_agents", []),
        }

        # Save to MongoDB
        save_ticket(ticket_doc)

        # Save order separately
        if state.get("validation_result", {}).get("validated_order"):
            save_order(ticket_id, state["validation_result"]["validated_order"])

        # Save customer
        customer = state.get("customer", {})
        if customer.get("name") or customer.get("phone"):
            save_customer(customer)

        # Save logs
        logs = state.get("logs", [])
        if logs:
            save_logs(ticket_id, [l if isinstance(l, dict) else l for l in logs])

        duration_ms = (time.time() - start) * 1000

        log_entry = AgentLog(
            agent_name="SaveOrder",
            action="persist_to_mongodb",
            message=f"Saved ticket {ticket_id} with status={ticket['status']}",
            duration_ms=round(duration_ms, 2),
            success=True,
        )

        logger.info("[SaveOrder] Completed — ticket=%s (%.1fms)", ticket_id, duration_ms)

        return {
            "ticket": ticket,
            "current_agent": "SaveOrder",
            "completed_agents": ["SaveOrder"],
            "logs": [log_entry.model_dump()],
        }

    except Exception as exc:
        duration_ms = (time.time() - start) * 1000
        logger.error("[SaveOrder] Failed: %s", exc)

        log_entry = AgentLog(
            agent_name="SaveOrder",
            action="persist_to_mongodb",
            message=f"Error: {str(exc)}",
            duration_ms=round(duration_ms, 2),
            success=False,
        )

        return {
            "error": str(exc),
            "current_agent": "SaveOrder",
            "completed_agents": ["SaveOrder"],
            "logs": [log_entry.model_dump()],
        }


# ── Build the LangGraph Workflow ────────────────────────────────────────────

# Global memory saver to persist state across sessions
memory = MemorySaver()

def build_workflow() -> StateGraph:
    """
    Build and compile the LangGraph workflow.

    Flow:
      START → ChannelAgent → OrderAgent → KnowledgeAgent
            → ValidationAgent → VoiceAgent → CallingAgent → SaveOrder → END
    """
    workflow = StateGraph(GraphState)

    # Add all agent nodes
    workflow.add_node("channel_agent", run_channel_agent)
    workflow.add_node("order_agent", run_order_agent)
    workflow.add_node("knowledge_agent", run_knowledge_agent)
    workflow.add_node("validation_agent", run_validation_agent)
    workflow.add_node("voice_agent", run_voice_agent)
    workflow.add_node("calling_agent", run_calling_agent)
    workflow.add_node("save_order", save_order_node)

    # Set entry point
    workflow.set_entry_point("channel_agent")

    # Define sequential edges
    workflow.add_edge("channel_agent", "knowledge_agent")
    workflow.add_edge("knowledge_agent", "order_agent")
    workflow.add_edge("order_agent", "validation_agent")
    workflow.add_edge("validation_agent", "voice_agent")
    workflow.add_edge("voice_agent", "calling_agent")
    workflow.add_edge("calling_agent", "save_order")
    workflow.add_edge("save_order", END)

    logger.info("LangGraph workflow built successfully.")
    return workflow


def get_compiled_workflow():
    """Build and compile the workflow graph."""
    workflow = build_workflow()
    compiled = workflow.compile(checkpointer=memory)
    logger.info("LangGraph workflow compiled.")
    return compiled


# ── Run the Workflow ────────────────────────────────────────────────────────

def run_workflow(
    message: str,
    channel: str = "website",
    customer_name: str = "",
    customer_phone: str = "",
    customer_address: str = "",
    session_id: str = "",
) -> dict:
    """
    Execute the full restaurant workflow for a customer message.

    Args:
        message: Customer's message text.
        channel: Source channel (website, whatsapp, discord).
        customer_name: Customer's name.
        customer_phone: Customer's phone number.
        customer_address: Customer's delivery address.

    Returns:
        Final state dict with all agent outputs.
    """
    logger.info("Starting workflow — channel=%s, message='%s'", channel, message[:50])

    # Build initial state
    # We only include the new input data.
    # We do NOT include fields like `extracted_order` or `ticket` with empty values,
    # because that would overwrite the short-term memory from previous turns!
    initial_state = {
        "user_message": message,
        "channel_source": channel,
        "conversation_history": [f"User: {message}"],
    }

    # Only update customer details if provided, to avoid overwriting with empty strings
    customer_update = {}
    if customer_name: customer_update["name"] = customer_name
    if customer_phone: customer_update["phone"] = customer_phone
    if customer_address: customer_update["address"] = customer_address
    customer_update["channel"] = channel

    if customer_update:
        initial_state["customer"] = customer_update

    # Ensure we have a valid session ID for the thread
    if not session_id:
        session_id = f"{channel}-{customer_name or 'anon'}-{customer_phone or 'none'}"

    config = {"configurable": {"thread_id": session_id}}

    # Compile and run
    app = get_compiled_workflow()
    final_state = app.invoke(initial_state, config=config)

    logger.info(
        "Workflow completed — ticket=%s, agents=%d",
        final_state.get("ticket", {}).get("ticket_id", "N/A"),
        len(final_state.get("completed_agents", [])),
    )

    return dict(final_state)
