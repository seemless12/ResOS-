"""
RestaurantOS — Shared State
Central state object that flows through every agent in the LangGraph workflow.
Every agent reads from and writes to this state — agents NEVER communicate directly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, Field

from app.models.schemas import (
    AgentLog,
    ChannelSource,
    CustomerInfo,
    ExtractedOrder,
    Intent,
    TicketInfo,
    TicketStatus,
    ValidationResult,
)


def _merge_logs(left: list[AgentLog], right: list[AgentLog]) -> list[AgentLog]:
    """Reducer that appends new logs to existing ones (used by LangGraph)."""
    return left + right


def _merge_completed(left: list[str], right: list[str]) -> list[str]:
    """Reducer that appends newly completed agents."""
    return left + right


class RestaurantState(BaseModel):
    """
    Shared state passed through the entire LangGraph workflow.

    Field ownership:
      - Channel Agent  → customer, ticket, channel_source, user_message
      - Order Agent    → detected_intent, extracted_order
      - Knowledge Agent → retrieved_context
      - Validation Agent → validation_result
      - Voice Agent    → confirmation_message, final_response
      - Orchestrator   → current_agent, completed_agents
      - All agents     → logs (append-only)
    """

    # ── Customer & Ticket ────────────────────────────────────────
    customer: CustomerInfo = Field(default_factory=CustomerInfo)
    ticket: TicketInfo = Field(default_factory=TicketInfo)

    # ── Input ────────────────────────────────────────────────────
    channel_source: ChannelSource = ChannelSource.WEBSITE
    user_message: str = ""

    # ── Order Agent output ───────────────────────────────────────
    detected_intent: Intent = Intent.UNKNOWN
    extracted_order: Optional[ExtractedOrder] = None

    # ── Knowledge Agent output ───────────────────────────────────
    retrieved_context: str = ""

    # ── Validation Agent output ──────────────────────────────────
    validation_result: Optional[ValidationResult] = None

    # ── Voice / Confirmation Agent output ────────────────────────
    confirmation_message: str = ""
    final_response: str = ""

    # ── Calling Agent output ─────────────────────────────────────
    call_script: str = ""
    call_audio_path: str = ""

    # ── Orchestrator bookkeeping ─────────────────────────────────
    current_agent: str = ""
    completed_agents: list[str] = Field(default_factory=list)

    # ── Logging ──────────────────────────────────────────────────
    logs: list[AgentLog] = Field(default_factory=list)

    # ── Error tracking ───────────────────────────────────────────
    error: str = ""

    class Config:
        arbitrary_types_allowed = True
