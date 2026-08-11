"""
RestaurantOS — Conversation Session Manager
Manages multi-turn conversation state for upselling and customer detail collection.
Each user session tracks: order items, conversation phase, and customer details.
"""

from __future__ import annotations

import logging
import time
import threading
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Conversation Phases ─────────────────────────────────────────────────────

PHASE_IDLE = "idle"                       # No active order yet
PHASE_ORDER_RECEIVED = "order_received"   # Order detected, about to upsell
PHASE_UPSELLING = "upselling"            # Asked customer about appetizers/drinks
PHASE_GATHERING_DETAILS = "gathering_details"  # Asking for name, address, phone, email
PHASE_CONFIRMED = "confirmed"            # Order finalized


# ── Session Store ───────────────────────────────────────────────────────────

_sessions: dict[str, dict[str, Any]] = {}
_lock = threading.Lock()

# Session TTL in seconds (30 minutes)
SESSION_TTL = 1800


def _new_session() -> dict[str, Any]:
    """Create a fresh session dict."""
    return {
        "phase": PHASE_IDLE,
        "pending_order": {},          # Extracted order from the pipeline
        "validation_result": {},      # Validation result from the pipeline
        "ticket": {},                 # Ticket info from the pipeline
        "customer_details": {         # Details collected via the template
            "name": "",
            "phone": "",
            "address": "",
            "email": "",
        },
        "conversation_history": [],   # List of {"role": "user"/"bot", "text": "..."}
        "last_activity": time.time(),
    }


def get_session(session_id: str) -> dict[str, Any]:
    """Get or create a session for the given ID."""
    with _lock:
        _cleanup_stale_sessions()
        if session_id not in _sessions:
            _sessions[session_id] = _new_session()
            logger.info("[SessionManager] Created new session: %s", session_id)
        _sessions[session_id]["last_activity"] = time.time()
        return _sessions[session_id]


def update_session(session_id: str, updates: dict[str, Any]) -> None:
    """Update specific fields in a session."""
    with _lock:
        if session_id not in _sessions:
            _sessions[session_id] = _new_session()
        _sessions[session_id].update(updates)
        _sessions[session_id]["last_activity"] = time.time()


def reset_session(session_id: str) -> None:
    """Reset a session back to idle (after order is confirmed)."""
    with _lock:
        _sessions[session_id] = _new_session()
        logger.info("[SessionManager] Reset session: %s", session_id)


def _cleanup_stale_sessions() -> None:
    """Remove sessions that have been inactive for longer than TTL."""
    now = time.time()
    stale = [sid for sid, s in _sessions.items() if now - s["last_activity"] > SESSION_TTL]
    for sid in stale:
        del _sessions[sid]
    if stale:
        logger.info("[SessionManager] Cleaned up %d stale sessions", len(stale))


# ── Detail Parsing ──────────────────────────────────────────────────────────

def parse_customer_details(text: str) -> dict[str, str]:
    """
    Attempt to extract name, phone, address, and email from a user message.
    Supports structured input, and falls back to LLM for robust parsing.
    """
    import re
    import json
    from app.utils.llm import call_llm

    details: dict[str, str] = {}
    text_lower = text.lower()

    # Try structured format: "Name: X, Phone: Y, Address: Z, Email: W"
    name_match = re.search(r"(?:name|naam)\s*[:\-]\s*(.+?)(?:,|\n|phone|address|email|$)", text, re.IGNORECASE)
    phone_match = re.search(r"(?:phone|number|no\.?|mobile)\s*[:\-]\s*([\d\+\-\s\(\)xX]+)", text, re.IGNORECASE)
    address_match = re.search(r"(?:address|location|deliver(?:y)?)\s*[:\-]\s*(.+?)(?:,?\s*(?:phone|email|$))", text, re.IGNORECASE)
    email_match = re.search(r"(?:email|e-mail|mail)\s*[:\-]\s*([\w\.\+\-]+@[\w\.\-]+\.\w+)", text, re.IGNORECASE)

    if name_match:
        details["name"] = name_match.group(1).strip().rstrip(",")
    if phone_match:
        details["phone"] = phone_match.group(1).strip().rstrip(",")
    if address_match:
        details["address"] = address_match.group(1).strip().rstrip(",")
    if email_match:
        details["email"] = email_match.group(1).strip()

    # If regex missed anything, try LLM for robust extraction (e.g., comma-separated list)
    if (not details.get("name") or not details.get("phone") or not details.get("address") or not details.get("email")) and len(text.strip()) > 3:
        prompt = f"""Extract customer details from the text below.
Respond ONLY with a valid JSON object containing the keys: "name", "phone", "address", and "email".
If a field is missing, set its value to an empty string "". 
DO NOT wrap the response in markdown blocks. Just output raw JSON.

Text: "{text}"
"""
        try:
            result = call_llm(prompt, temperature=0.1)
            result = result.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(result)
            
            # Only override if LLM found something and we didn't
            if parsed.get("name") and not details.get("name"): details["name"] = parsed["name"].strip()
            if parsed.get("phone") and not details.get("phone"): details["phone"] = parsed["phone"].strip()
            if parsed.get("address") and not details.get("address"): details["address"] = parsed["address"].strip()
            if parsed.get("email") and not details.get("email"): details["email"] = parsed["email"].strip()
        except Exception as e:
            logger.warning(f"[SessionManager] LLM extraction failed: {e}")

    return details


def get_missing_details(session: dict[str, Any]) -> list[str]:
    """Return a list of customer detail fields that are still empty."""
    details = session.get("customer_details", {})
    missing = []
    if not details.get("name"):
        missing.append("Name")
    if not details.get("phone"):
        missing.append("Phone Number")
    if not details.get("address"):
        missing.append("Delivery Address")
    if not details.get("email"):
        missing.append("Email")
    return missing


# ── Upsell Logic ────────────────────────────────────────────────────────────

UPSELL_APPETIZERS = [
    "Tangy Wings (PKR 490)",
    "Mozzarella Sticks (PKR 550)",
    "Chicken Nuggets (PKR 390)",
    "Potato Skins (PKR 390)",
    "Finger Chicken Kebab (PKR 450)",
]

UPSELL_DRINKS = [
    "Soft Drink 345ml (PKR 100)",
    "Soft Drink 1.5L (PKR 200)",
    "Mineral Water 500ml (PKR 80)",
]


def generate_upsell_message(order_items: list[dict]) -> str:
    """
    Generate an upsell suggestion based on the current order.
    Dynamically picks items not already in the order.
    """
    ordered_names = {item.get("name", "").lower() for item in order_items}

    # Pick an appetizer not already ordered
    appetizer_pick = None
    for app in UPSELL_APPETIZERS:
        app_name = app.split(" (")[0].lower()
        if app_name not in ordered_names:
            appetizer_pick = app
            break

    # Pick a drink not already ordered
    drink_pick = None
    for drink in UPSELL_DRINKS:
        drink_name = drink.split(" (")[0].lower()
        if drink_name not in ordered_names:
            drink_pick = drink
            break

    suggestions = []
    if appetizer_pick:
        suggestions.append(appetizer_pick)
    if drink_pick:
        suggestions.append(drink_pick)

    if suggestions:
        items_str = " or ".join(suggestions)
        return (
            f"Great choice! Would you also like to add {items_str} to your order? "
            f"Just say 'yes' to add them, or 'no' to continue with your current order."
        )
    else:
        return ""


def is_acceptance(text: str) -> bool:
    """Check if the user message indicates acceptance of the upsell."""
    import re
    return bool(re.search(r'\b(yes|yeah|yep|sure|ok|okay|add|haan|han|ji)\b', text.lower()))


def is_rejection(text: str) -> bool:
    """Check if the user message indicates rejection of the upsell."""
    import re
    return bool(re.search(r'\b(no|nah|nope|skip|nahi|bas)\b', text.lower()))
