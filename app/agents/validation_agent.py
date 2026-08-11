"""
RestaurantOS — Validation Agent
Validates extracted orders against the menu, checks quantities,
and verifies restaurant availability.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime

from app.config import get_settings
from app.models.schemas import (
    AgentLog,
    ExtractedOrder,
    OrderItem,
    ValidationResult,
)
from app.rag.restaurant_data import get_menu_lookup

logger = logging.getLogger(__name__)

AGENT_NAME = "ValidationAgent"


def _check_restaurant_open() -> tuple[bool, str]:
    """Check if the restaurant is currently open."""
    settings = get_settings()
    now = datetime.now()
    current_hour = now.hour

    is_open = settings.restaurant_open_hour <= current_hour < settings.restaurant_close_hour
    if is_open:
        return True, ""
    return False, (
        f"Restaurant is currently closed. "
        f"Operating hours: {settings.restaurant_open_hour}:00 - {settings.restaurant_close_hour}:00. "
        f"Current time: {now.strftime('%H:%M')}."
    )


def _deduplicate_items(items: list[dict]) -> list[dict]:
    """
    Merge duplicate items by summing their quantities.

    If the LLM returns the same item multiple times (e.g., 3 separate entries
    of "Chicken Biryani" with quantity 1), this consolidates them into a single
    entry with the combined quantity (e.g., quantity 3).
    """
    merged: dict[str, dict] = {}
    for item in items:
        name = item.get("name", "").strip().lower()
        if not name:
            continue
        if name in merged:
            merged[name]["quantity"] = merged[name].get("quantity", 1) + item.get("quantity", 1)
            # Keep the latest notes if present
            new_notes = item.get("notes", "")
            if new_notes:
                merged[name]["notes"] = new_notes
        else:
            merged[name] = {
                "name": item.get("name", "").strip(),
                "quantity": item.get("quantity", 1),
                "notes": item.get("notes", ""),
            }
    return list(merged.values())


def _validate_items(
    items: list[dict],
    menu_lookup: dict[str, dict],
) -> tuple[list[OrderItem], list[str], list[str]]:
    """
    Validate each order item against the menu.

    Returns:
        Tuple of (validated_items, errors, warnings).
    """
    settings = get_settings()
    validated: list[OrderItem] = []
    errors: list[str] = []
    warnings: list[str] = []

    # Deduplicate items first — merge duplicates by summing quantities
    items = _deduplicate_items(items)

    for item in items:
        name = item.get("name", "").strip()
        quantity = item.get("quantity", 1)
        notes = item.get("notes", "")

        # Check if item exists in menu (case-insensitive)
        menu_item = menu_lookup.get(name.lower())

        if not menu_item:
            # Try fuzzy matching
            best_match = _fuzzy_match(name, menu_lookup)
            if best_match:
                warnings.append(
                    f"'{name}' not found exactly. Did you mean '{best_match}'? Using '{best_match}'."
                )
                menu_item = menu_lookup[best_match.lower()]
                name = best_match
            else:
                errors.append(f"'{name}' is not on our menu.")
                continue

        # Check availability
        if not menu_item.get("available", True):
            errors.append(f"'{name}' is currently unavailable.")
            continue

        # Check quantity
        if quantity < 1:
            errors.append(f"Quantity for '{name}' must be at least 1.")
            continue
        if quantity > 50:
            errors.append(
                f"Maximum quantity for '{name}' is 50. For bulk orders, please contact us."
            )
            continue
        if quantity > 20:
            warnings.append(
                f"Large quantity ({quantity}) for '{name}'. Please confirm this is correct."
            )

        # Build validated item with price
        unit_price = float(menu_item.get("price", 0))
        validated.append(
            OrderItem(
                name=menu_item["name"],  # Use canonical name
                quantity=quantity,
                unit_price=unit_price,
                total_price=unit_price * quantity,
                notes=notes,
            )
        )

    return validated, errors, warnings


def _fuzzy_match(name: str, menu_lookup: dict[str, dict]) -> str | None:
    """
    Fuzzy matching for menu items.

    Matching strategy (in order of priority):
      1. Exact substring — the query is fully contained in a menu name or vice versa,
         but only when the substring is at least 4 chars (avoids matching "ice" to "rice").
      2. High word overlap — at least 2 words in common (e.g., "chicken biryani" ↔ "chicken biryani").
      3. Single-word match ONLY when both the query and the menu item are single words.

    This prevents the old bug where ordering "Chicken Biryani" could accidentally
    match "Chicken Burger" or "Mutton Biryani" via a single shared word.
    """
    name_lower = name.lower().strip()
    if not name_lower:
        return None

    best_match = None
    best_score = 0

    for menu_name, menu_data in menu_lookup.items():
        score = 0

        # Strategy 1: Substring match (only if the substring is meaningful, >= 4 chars)
        if len(name_lower) >= 4 and name_lower in menu_name:
            score = len(name_lower) / len(menu_name)  # Prefer tighter matches
            score += 2  # Bonus for substring match
        elif len(menu_name) >= 4 and menu_name in name_lower:
            score = len(menu_name) / len(name_lower)
            score += 2

        # Strategy 2: Word overlap
        if score == 0:
            name_words = set(name_lower.split())
            menu_words = set(menu_name.split())
            common = name_words & menu_words
            total_unique = name_words | menu_words

            if len(common) >= 2:
                # Strong match: 2+ words in common
                score = len(common) / len(total_unique)
            elif len(common) == 1 and len(name_words) == 1 and len(menu_words) <= 2:
                # Allow single-word match only for single-word queries
                # e.g., "Biryani" matching "Chicken Biryani" — weak match
                score = 0.3

        if score > best_score:
            best_score = score
            best_match = menu_data["name"]

    return best_match if best_score > 0 else None


def run_validation_agent(state: dict) -> dict:
    """
    LangGraph node — Validation Agent.

    Responsibilities:
      1. Check if the restaurant is currently open.
      2. Validate each order item against the menu.
      3. Check quantities are valid.
      4. Calculate prices and totals.
      5. Create ValidationResult.

    Args:
        state: Current state dict from LangGraph.

    Returns:
        Updated state dict with validation_result.
    """
    start = time.time()
    logger.info("[%s] Starting validation", AGENT_NAME)

    try:
        settings = get_settings()
        errors: list[str] = []
        warnings: list[str] = []

        # Check restaurant hours
        is_open, hours_error = _check_restaurant_open()
        if not hours_error:
            pass  # Restaurant is open
        else:
            warnings.append(hours_error)  # Warn but don't block

        # Check intent before validating items
        intent = state.get("detected_intent", "unknown")
        extracted_order = state.get("extracted_order")
        
        if intent != "order":
            # For inquiries/complaints, there's no order to validate. Mark as valid so it passes through.
            validation_result = ValidationResult(
                is_valid=True,
                errors=[],
                warnings=warnings,
                validated_order=ExtractedOrder(),
            )
        elif not extracted_order or not extracted_order.get("items"):
            # It's an order intent, but no items found
            validation_result = ValidationResult(
                is_valid=False,
                errors=["No items found in the order. Please specify what you'd like to order."],
                warnings=warnings,
                validated_order=ExtractedOrder(),
            )
        else:
            items = extracted_order.get("items", [])
            menu_lookup = get_menu_lookup()

            # Validate items
            validated_items, item_errors, item_warnings = _validate_items(items, menu_lookup)
            errors.extend(item_errors)
            warnings.extend(item_warnings)

            # Calculate totals
            subtotal = sum(item.total_price for item in validated_items)
            delivery_fee = 150.0 if subtotal < 1000 else 0.0
            total = subtotal + delivery_fee

            validated_order = ExtractedOrder(
                items=validated_items,
                subtotal=subtotal,
                delivery_fee=delivery_fee,
                total=total,
                special_instructions=extracted_order.get("special_instructions", ""),
            )

            is_valid = len(errors) == 0 and len(validated_items) > 0

            validation_result = ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                validated_order=validated_order,
            )

        duration_ms = (time.time() - start) * 1000

        log_entry = AgentLog(
            agent_name=AGENT_NAME,
            action="validate_order",
            message=(
                f"Validation {'passed' if validation_result.is_valid else 'failed'} — "
                f"errors={len(validation_result.errors)}, warnings={len(validation_result.warnings)}"
            ),
            duration_ms=round(duration_ms, 2),
            success=True,
        )

        logger.info(
            "[%s] Completed — valid=%s, errors=%d, warnings=%d (%.1fms)",
            AGENT_NAME,
            validation_result.is_valid,
            len(validation_result.errors),
            len(validation_result.warnings),
            duration_ms,
        )

        return {
            "validation_result": validation_result.model_dump(),
            "current_agent": AGENT_NAME,
            "completed_agents": [AGENT_NAME],
            "logs": [log_entry.model_dump()],
        }

    except Exception as exc:
        duration_ms = (time.time() - start) * 1000
        logger.error("[%s] Failed: %s", AGENT_NAME, exc)

        log_entry = AgentLog(
            agent_name=AGENT_NAME,
            action="validate_order",
            message=f"Error: {str(exc)}",
            duration_ms=round(duration_ms, 2),
            success=False,
        )

        return {
            "validation_result": ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(exc)}"],
            ).model_dump(),
            "error": str(exc),
            "current_agent": AGENT_NAME,
            "completed_agents": [AGENT_NAME],
            "logs": [log_entry.model_dump()],
        }
