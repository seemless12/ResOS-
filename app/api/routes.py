"""
RestaurantOS — FastAPI Routes
API endpoints for chat, tickets, and health checks.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from app.graph.workflow import run_workflow
from app.database.mongodb import async_get_ticket, async_get_all_tickets
from app.models.schemas import ChatRequest, ChatResponse, TicketResponse
from app.session_manager import parse_customer_details

logger = logging.getLogger(__name__)

router = APIRouter()


# ── POST /chat ──────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def process_chat(request: ChatRequest):
    """
    Process a customer chat message through the LangGraph workflow.
    All conversational state (upselling, gathering details) is handled natively by the AI.
    """
    session_id = request.session_id or str(uuid.uuid4())
    logger.info(
        "POST /chat — session=%s, channel=%s, message='%s'",
        session_id, request.channel.value, request.message[:50],
    )

    # Parse details from the message to help the AI
    parsed = parse_customer_details(request.message)

    try:
        result = run_workflow(
            message=request.message,
            channel=request.channel.value,
            customer_name=request.customer_name or parsed.get("name"),
            customer_phone=request.customer_phone or parsed.get("phone"),
            customer_address=request.customer_address or parsed.get("address"),
            session_id=session_id,
        )

        reply = result.get("final_response", "How can I help you?")
        ticket = result.get("ticket", {})

        return ChatResponse(
            ticket_id=ticket.get("ticket_id", "N/A"),
            status=result.get("order_status", "idle"),
            confirmation=reply,
            call_script=result.get("call_script", ""),
            call_audio_path=result.get("call_audio_path", ""),
        )

    except Exception as exc:
        logger.error("POST /chat failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat: {str(exc)}",
        )


# ── POST /ticket ────────────────────────────────────────────────────────────

@router.post("/ticket", status_code=status.HTTP_200_OK)
async def create_ticket(request: ChatRequest):
    """
    Create a new ticket from a customer message.
    Same as /chat — provided for API consistency.
    """
    return await process_chat(request)


# ── GET /ticket/{ticket_id} ────────────────────────────────────────────────

@router.get("/ticket/{ticket_id}", status_code=status.HTTP_200_OK)
async def get_ticket(ticket_id: str):
    """
    Retrieve a ticket by its ID.

    Returns full ticket details including order, validation, and logs.
    """
    logger.info("GET /ticket/%s", ticket_id)

    ticket_data = await async_get_ticket(ticket_id)

    if not ticket_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found.",
        )

    # Remove MongoDB internal _id for clean JSON
    ticket_data.pop("_id", None)
    return ticket_data


# ── GET /tickets ────────────────────────────────────────────────────────────

@router.get("/tickets", status_code=status.HTTP_200_OK)
async def list_tickets(limit: int = 20):
    """
    List the most recent tickets.
    """
    tickets = await async_get_all_tickets(limit=limit)
    for t in tickets:
        t.pop("_id", None)
    return {"tickets": tickets, "count": len(tickets)}


# ── GET /health ─────────────────────────────────────────────────────────────

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint."""
    from app.config import get_settings
    settings = get_settings()

    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "restaurant": settings.restaurant_name,
    }
