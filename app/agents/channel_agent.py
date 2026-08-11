"""
RestaurantOS — Channel Agent
Accepts customer requests from any channel, creates a unified ticket,
and initializes the shared state.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime

from app.graph.state import RestaurantState
from app.models.schemas import (
    AgentLog,
    ChannelSource,
    CustomerInfo,
    TicketInfo,
    TicketStatus,
)

logger = logging.getLogger(__name__)

AGENT_NAME = "ChannelAgent"


def run_channel_agent(state: dict) -> dict:
    """
    LangGraph node — Channel Agent.

    Responsibilities:
      1. Accept customer request from any channel.
      2. Generate a unique Ticket ID.
      3. Store channel source and customer info.
      4. Initialize state for downstream agents.

    Args:
        state: Current state dict from LangGraph.

    Returns:
        Updated state dict with ticket and customer info.
    """
    start = time.time()
    logger.info("[%s] Starting — channel=%s", AGENT_NAME, state.get("channel_source"))

    try:
        # Generate unique ticket ID
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"

        # Build ticket info
        ticket = TicketInfo(
            ticket_id=ticket_id,
            status=TicketStatus.PROCESSING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Build customer info
        customer = CustomerInfo(
            name=state.get("customer", {}).get("name", "") if isinstance(state.get("customer"), dict) else "",
            phone=state.get("customer", {}).get("phone", "") if isinstance(state.get("customer"), dict) else "",
            address=state.get("customer", {}).get("address", "") if isinstance(state.get("customer"), dict) else "",
            channel=state.get("channel_source", ChannelSource.WEBSITE),
        )

        duration_ms = (time.time() - start) * 1000

        log_entry = AgentLog(
            agent_name=AGENT_NAME,
            action="initialize_ticket",
            message=f"Created ticket {ticket_id} from {state.get('channel_source', 'website')} channel",
            duration_ms=round(duration_ms, 2),
            success=True,
        )

        logger.info("[%s] Completed — ticket_id=%s (%.1fms)", AGENT_NAME, ticket_id, duration_ms)

        return {
            "ticket": ticket.model_dump(),
            "customer": customer.model_dump(),
            "current_agent": AGENT_NAME,
            "completed_agents": [AGENT_NAME],
            "logs": [log_entry.model_dump()],
        }

    except Exception as exc:
        duration_ms = (time.time() - start) * 1000
        logger.error("[%s] Failed: %s", AGENT_NAME, exc)

        log_entry = AgentLog(
            agent_name=AGENT_NAME,
            action="initialize_ticket",
            message=f"Error: {str(exc)}",
            duration_ms=round(duration_ms, 2),
            success=False,
        )

        return {
            "error": str(exc),
            "current_agent": AGENT_NAME,
            "completed_agents": [AGENT_NAME],
            "logs": [log_entry.model_dump()],
        }
