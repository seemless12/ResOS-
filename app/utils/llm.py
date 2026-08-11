"""
RestaurantOS — LLM Client Utility
Wraps OpenRouter API calls with retry logic and error handling.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from openai import OpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)


def get_llm_client() -> OpenAI:
    """Create an OpenAI-compatible client pointing at OpenRouter."""
    settings = get_settings()
    return OpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )


def call_llm(
    prompt: str,
    system_message: str = "You are a helpful restaurant assistant AI.",
    temperature: float = 0.3,
    max_tokens: int = 1024,
    retries: int = 2,
) -> str:
    """
    Send a prompt to the LLM and return the text response.

    Args:
        prompt: The user-facing prompt text.
        system_message: System instruction for the model.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens in response.
        retries: Number of retry attempts on failure.

    Returns:
        The model's response text.
    """
    settings = get_settings()
    client = get_llm_client()

    for attempt in range(1, retries + 1):
        try:
            response = client.chat.completions.create(
                model=settings.openrouter_model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content or ""
            return content.strip()
        except Exception as exc:
            logger.warning(
                "LLM call attempt %d/%d failed: %s", attempt, retries, exc
            )
            if attempt == retries:
                logger.error("LLM call failed after %d attempts", retries)
                raise
    return ""


def call_llm_json(
    prompt: str,
    system_message: str = "You are a helpful restaurant assistant AI. Always respond with valid JSON.",
    temperature: float = 0.1,
    max_tokens: int = 1024,
) -> dict:
    """
    Call the LLM and parse the response as JSON.
    Falls back to empty dict on parse failure.
    """
    raw = call_llm(prompt, system_message, temperature, max_tokens)

    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw = "\n".join(lines)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Failed to parse LLM JSON response: %s", raw[:200])
        return {}
