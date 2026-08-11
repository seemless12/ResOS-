"""
RestaurantOS — Pydantic Models / Schemas
All domain models used across the system.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────

class ChannelSource(str, Enum):
    """Supported input channels."""
    WEBSITE = "website"
    WHATSAPP = "whatsapp"
    DISCORD = "discord"


class TicketStatus(str, Enum):
    """Lifecycle status of a ticket."""
    OPEN = "open"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Intent(str, Enum):
    """Customer intent categories."""
    ORDER = "order"
    INQUIRY = "inquiry"
    COMPLAINT = "complaint"
    MODIFICATION = "modification"
    CANCELLATION = "cancellation"
    UNKNOWN = "unknown"


# ── Domain Models ────────────────────────────────────────────────────────────

class CustomerInfo(BaseModel):
    """Customer details extracted from the conversation."""
    name: str = ""
    phone: str = ""
    address: str = ""
    channel: ChannelSource = ChannelSource.WEBSITE


class OrderItem(BaseModel):
    """Single item within an order."""
    name: str
    quantity: int = 1
    unit_price: float = 0.0
    total_price: float = 0.0
    notes: str = ""


class ExtractedOrder(BaseModel):
    """Structured order extracted by the Order Agent."""
    items: list[OrderItem] = Field(default_factory=list)
    subtotal: float = 0.0
    delivery_fee: float = 0.0
    total: float = 0.0
    special_instructions: str = ""


class ValidationResult(BaseModel):
    """Output of the Validation Agent."""
    is_valid: bool = False
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    validated_order: Optional[ExtractedOrder] = None


class AgentLog(BaseModel):
    """Execution log entry for an agent."""
    agent_name: str
    action: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0
    success: bool = True


class TicketInfo(BaseModel):
    """Ticket metadata."""
    ticket_id: str = ""
    status: TicketStatus = TicketStatus.OPEN
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ── API Request / Response Models ────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Incoming chat request from any channel."""
    message: str
    channel: ChannelSource = ChannelSource.WEBSITE
    customer_name: str = ""
    customer_phone: str = ""
    customer_address: str = ""
    session_id: str = ""  # Unique session ID for multi-turn conversations


class ChatResponse(BaseModel):
    """Response returned to the client."""
    ticket_id: str
    status: str
    confirmation: str
    call_script: Optional[str] = ""
    call_audio_path: Optional[str] = ""
    order_summary: Optional[ExtractedOrder] = None
    validation: Optional[ValidationResult] = None


class TicketResponse(BaseModel):
    """Full ticket detail response."""
    ticket_id: str
    status: str
    channel: str
    customer: CustomerInfo
    message: str
    intent: str
    order: Optional[ExtractedOrder] = None
    validation: Optional[ValidationResult] = None
    confirmation: str
    logs: list[AgentLog] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
