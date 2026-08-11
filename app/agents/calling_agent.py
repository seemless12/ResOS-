"""
RestaurantOS — Calling Agent
Generates spoken confirmation scripts and optional TTS audio files using gTTS (Google Text-to-Speech).
Simulates placing a phone call to confirm customer orders.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Optional

from gtts import gTTS

from app.config import get_settings
from app.models.schemas import AgentLog

logger = logging.getLogger(__name__)

AGENT_NAME = "CallingAgent"


def generate_call_script(state: dict) -> str:
    """
    Generate the call script text for the customer order confirmation call.
    Format:
    "Hello Mr/Ms {customer_name}, your order details are: {items_summary}.
     Your total bill is {total} {currency}.
     If you want to confirm your order press 1.
     For changes press 2 and go to our chatapp."
    """
    customer = state.get("customer", {})
    customer_name = customer.get("name", "").strip() or "Customer"

    validation = state.get("validation_result", {})
    validated_order = validation.get("validated_order", {})
    items = validated_order.get("items", [])

    if not items:
        items_summary = "No items specified"
        total = 0
    else:
        item_parts = []
        for item in items:
            qty = item.get("quantity", 1)
            name = item.get("name", "item")
            item_parts.append(f"{qty} {name}")
        
        if len(item_parts) == 1:
            items_summary = item_parts[0]
        elif len(item_parts) == 2:
            items_summary = f"{item_parts[0]} and {item_parts[1]}"
        else:
            items_summary = ", ".join(item_parts[:-1]) + f", and {item_parts[-1]}"
        
        total = validated_order.get("total", 0)

    settings = get_settings()
    currency = settings.restaurant_currency

    script = (
        f"Hello Mr {customer_name}, your order details are: {items_summary}. "
        f"Your total bill is {total:.0f} {currency}. "
        f"If you want to confirm your order press 1. "
        f"For changes press 2 and go to our chatapp."
    )
    return script


def generate_tts_audio(text: str, filename: str = "order_call.mp3") -> Optional[str]:
    """
    Convert text to speech MP3 file using Google TTS (gTTS).
    Returns file path or None on failure.
    """
    try:
        audio_dir = Path("static/audio")
        audio_dir.mkdir(parents=True, exist_ok=True)
        file_path = audio_dir / filename

        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(str(file_path))
        logger.info("[%s] Saved TTS audio to %s", AGENT_NAME, file_path)
        return str(file_path)
    except Exception as exc:
        logger.warning("[%s] gTTS audio generation failed: %s", AGENT_NAME, exc)
        return None


def run_calling_agent(state: dict) -> dict:
    """
    LangGraph node — Calling Agent.

    Responsibilities:
      1. Generate structured call script for order confirmation.
      2. Synthesize audio file via Google Text-To-Speech (gTTS) ONLY if a valid order.
      3. Store call script and audio reference in shared state.
    """
    start = time.time()
    logger.info("[%s] Starting calling agent", AGENT_NAME)

    try:
        intent = state.get("detected_intent", "unknown")
        validation = state.get("validation_result", {})
        is_valid = validation.get("is_valid", False)

        # Optimization: Only generate call script and TTS if it's a valid order
        if intent == "order" and is_valid:
            script = generate_call_script(state)
            ticket_id = state.get("ticket", {}).get("ticket_id", "call")
            audio_path = generate_tts_audio(script, filename=f"call_{ticket_id}.mp3")
        else:
            logger.info("[%s] Skipping TTS generation for non-order/invalid state.", AGENT_NAME)
            script = ""
            audio_path = ""

        duration_ms = (time.time() - start) * 1000

        log_entry = AgentLog(
            agent_name=AGENT_NAME,
            action="make_confirmation_call",
            message=f"Generated call script and TTS audio ({len(script)} chars)",
            duration_ms=round(duration_ms, 2),
            success=True,
        )

        logger.info("[%s] Completed (%.1fms)", AGENT_NAME, duration_ms)

        return {
            "call_script": script,
            "call_audio_path": audio_path or "",
            "current_agent": AGENT_NAME,
            "completed_agents": [AGENT_NAME],
            "logs": [log_entry.model_dump()],
        }

    except Exception as exc:
        duration_ms = (time.time() - start) * 1000
        logger.error("[%s] Failed: %s", AGENT_NAME, exc)

        log_entry = AgentLog(
            agent_name=AGENT_NAME,
            action="make_confirmation_call",
            message=f"Error: {str(exc)}",
            duration_ms=round(duration_ms, 2),
            success=False,
        )

        return {
            "call_script": "",
            "call_audio_path": "",
            "error": str(exc),
            "current_agent": AGENT_NAME,
            "completed_agents": [AGENT_NAME],
            "logs": [log_entry.model_dump()],
        }
