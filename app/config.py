"""
RestaurantOS — Centralized Configuration
All settings are loaded from environment variables with sensible defaults.
"""

from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application-wide settings sourced from .env file."""

    # ── Application ──────────────────────────────────────────────
    app_name: str = Field(default="RestaurantOS", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    debug: bool = Field(default=False, alias="DEBUG")

    # ── MongoDB ──────────────────────────────────────────────────
    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    mongodb_db_name: str = Field(default="restaurantdb", alias="MONGODB_DB_NAME")

    # ── OpenRouter / LLM ─────────────────────────────────────────
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL"
    )
    openrouter_model: str = Field(
        default="openai/gpt-4o-mini", alias="OPENROUTER_MODEL"
    )

    # ── ChromaDB ─────────────────────────────────────────────────
    chromadb_persist_dir: str = Field(
        default="./data/chromadb", alias="CHROMADB_PERSIST_DIR"
    )
    chromadb_collection_name: str = Field(
        default="restaurant_knowledge", alias="CHROMADB_COLLECTION_NAME"
    )

    # ── Restaurant ───────────────────────────────────────────────
    restaurant_name: str = Field(
        default="Pizza Max", alias="RESTAURANT_NAME"
    )
    restaurant_open_hour: int = Field(default=10, alias="RESTAURANT_OPEN_HOUR")
    restaurant_close_hour: int = Field(default=23, alias="RESTAURANT_CLOSE_HOUR")
    restaurant_currency: str = Field(default="PKR", alias="RESTAURANT_CURRENCY")

    # ── Discord ──────────────────────────────────────────────────
    discord_bot_token: str = Field(default="", alias="DISCORD_BOT_TOKEN")
    discord_channel_id: str = Field(default="", alias="DISCORD_CHANNEL_ID")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton of application settings."""
    return Settings()
