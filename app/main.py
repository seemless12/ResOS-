"""
RestaurantOS — FastAPI Application Entry Point
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import router
from app.database.mongodb import close_async_db, init_database

# ── Logging Setup ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-25s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("RestaurantOS")


# ── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    settings = get_settings()
    logger.info("=" * 60)
    logger.info("  🍽️  %s v%s  Starting...", settings.app_name, settings.app_version)
    logger.info("  📍 Restaurant: %s", settings.restaurant_name)
    logger.info("  🕐 Hours: %d:00 - %d:00", settings.restaurant_open_hour, settings.restaurant_close_hour)
    logger.info("=" * 60)

    # Initialize database and seed knowledge base
    try:
        init_database()
        logger.info("✅ Database initialized and knowledge base seeded.")
    except Exception as exc:
        logger.error("❌ Database init failed: %s", exc)

    # Start Discord bot if token is configured
    try:
        from app.agents.discord_bot import start_discord_bot
        if settings.discord_bot_token:
            started = start_discord_bot()
            if started:
                logger.info("🤖 Discord bot starting in background...")
            else:
                logger.info("⏭️  Discord bot skipped (no token or already running).")
        else:
            logger.info("⏭️  Discord bot skipped (DISCORD_BOT_TOKEN not set).")
    except Exception as exc:
        logger.warning("⚠️  Discord bot failed to start: %s", exc)

    yield

    # Shutdown
    await close_async_db()
    logger.info("🛑 %s shut down.", settings.app_name)


# ── App Factory ──────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "Multi-Agent Restaurant Operations System — "
            "AI-powered order processing with LangGraph orchestration."
        ),
        version=settings.app_version,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Static files (for call audio)
    import os
    from fastapi.staticfiles import StaticFiles
    os.makedirs("static/audio", exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Register routes
    app.include_router(router, prefix="/api")

    return app


# ── Application Instance ────────────────────────────────────────────────────

app = create_app()


# ── Direct Run ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
