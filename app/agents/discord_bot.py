"""
RestaurantOS — Discord Bot Integration
Listens on a Discord channel and forwards messages through the workflow.
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Will be lazily imported to avoid requiring discord.py when not used
_bot_thread: Optional[threading.Thread] = None
_bot_running = False


def _build_details_prompt_discord(session: dict) -> str:
    """Build the dynamic template asking for customer details (Discord)."""
    from app.session_manager import get_missing_details
    missing = get_missing_details(session)
    if not missing:
        return "All details collected!"

    lines = ["To confirm your order, please provide the following details:"]
    for field in missing:
        lines.append(f"- {field}")
    lines.append("\nYou can type them all at once, for example:")
    lines.append("Name: Ahmed, Phone: 0300-1234567, Address: Block 5 Clifton, Email: ahmed@email.com")
    return "\n".join(lines)


def _build_final_confirmation_discord(session: dict) -> str:
    """Build the final order confirmation message (Discord)."""
    from app.config import get_settings
    settings = get_settings()

    ticket = session.get("ticket", {})
    ticket_id = ticket.get("ticket_id", "N/A")
    details = session.get("customer_details", {})
    validation = session.get("validation_result", {})
    validated_order = validation.get("validated_order", {})
    items = validated_order.get("items", [])

    order_lines = []
    for item in items:
        qty = item.get("quantity", 1)
        name = item.get("name", "item")
        price = item.get("total_price", 0)
        order_lines.append(f"- {qty}x {name}: {settings.restaurant_currency} {price:.0f}")
    order_text = "\n".join(order_lines) if order_lines else "No items"

    total = validated_order.get("total", 0)
    delivery_fee = validated_order.get("delivery_fee", 0)

    return (
        f"**Order Confirmed!**\n\n"
        f"**Ticket ID:** {ticket_id}\n\n"
        f"**Order Details:**\n{order_text}\n"
        f"Delivery Fee: {settings.restaurant_currency} {delivery_fee:.0f}\n"
        f"**Total: {settings.restaurant_currency} {total:.0f}**\n\n"
        f"**Delivery To:**\n"
        f"- Name: {details.get('name', 'N/A')}\n"
        f"- Phone: {details.get('phone', 'N/A')}\n"
        f"- Address: {details.get('address', 'N/A')}\n"
        f"- Email: {details.get('email', 'N/A')}\n\n"
        f"Estimated delivery: 30-45 minutes.\n"
        f"Thank you for ordering from {settings.restaurant_name}!"
    )


def _run_discord_bot(token: str, channel_id: str) -> None:
    """Run the Discord bot in a background thread."""
    global _bot_running

    try:
        import discord
        from discord.ext import commands
    except ImportError:
        logger.error("discord.py not installed. Run: pip install discord.py")
        return

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        logger.info("Discord bot logged in as %s", bot.user)
        guilds = ", ".join([guild.name for guild in bot.guilds]) or "None"
        logger.info("Connected guilds: %s", guilds)
        _bot_running = True

    @bot.event
    async def on_message(message: discord.Message):
        # Ignore bot's own messages
        if message.author == bot.user:
            return

        logger.info(
            "Received message from %s in channel %s: %s",
            message.author.display_name,
            message.channel.id,
            message.content[:60]
        )

        # Process commands first
        if message.content.startswith("!"):
            await bot.process_commands(message)
            return

        # Only process messages in the configured channel (if valid numeric ID is set)
        if channel_id and channel_id.isdigit() and str(message.channel.id) != channel_id:
            logger.debug("Ignoring message from unconfigured channel: %s", message.channel.id)
            return

        user_message = message.content.strip()
        if not user_message:
            return

        logger.info("Processing message from %s...", message.author.display_name)

        # Use Discord user ID as the session identifier
        discord_session_id = f"discord-{message.author.id}"

        # Send "processing" indicator
        async with message.channel.typing():
            try:
                from app.session_manager import (
                    get_session, update_session, reset_session,
                    parse_customer_details, get_missing_details,
                    generate_upsell_message, is_acceptance, is_rejection,
                    PHASE_IDLE, PHASE_UPSELLING, PHASE_GATHERING_DETAILS,
                    PHASE_CONFIRMED,
                )
                from app.graph.workflow import run_workflow
                from app.config import get_settings

                # Parse any customer details present in the message
                parsed = parse_customer_details(user_message)
                loop = asyncio.get_event_loop()

                # Run the full pipeline natively
                result = await loop.run_in_executor(
                    None,
                    lambda: run_workflow(
                        message=user_message,
                        channel="discord",
                        customer_name=message.author.display_name,
                        customer_phone=parsed.get("phone", ""),
                        customer_address=parsed.get("address", ""),
                        session_id=discord_session_id,
                    ),
                )

                reply = result.get("final_response", "How can I help you?")

                # Discord has a 2000 char limit
                if len(reply) > 2000:
                    reply = reply[:1995] + "..."

                await message.reply(reply)

            except Exception as exc:
                logger.error("Discord workflow error: %s", exc, exc_info=True)
                await message.reply(
                    f"Sorry, something went wrong processing your request.\n"
                    f"Error: {str(exc)[:200]}"
                )

    @bot.command(name="menu")
    async def show_menu(ctx: commands.Context):
        """Show the restaurant menu."""
        from app.rag.restaurant_data import MENU_ITEMS
        from app.config import get_settings

        settings = get_settings()
        categories: dict[str, list[str]] = {}
        for item in MENU_ITEMS:
            cat = item["category"]
            categories.setdefault(cat, []).append(
                f"  • **{item['name']}** — {settings.restaurant_currency} {item['price']}"
            )

        lines = [f"🍽️ **{settings.restaurant_name} Menu**\n"]
        for cat, items in categories.items():
            lines.append(f"\n**{cat}**")
            lines.extend(items)

        menu_text = "\n".join(lines)
        if len(menu_text) > 1900:
            menu_text = menu_text[:1900] + "\n\n_(menu truncated)_"

        await ctx.send(menu_text)

    @bot.command(name="hours")
    async def show_hours(ctx: commands.Context):
        """Show restaurant hours."""
        from app.config import get_settings
        settings = get_settings()
        await ctx.send(
            f"🕐 **{settings.restaurant_name}** is open daily from "
            f"**{settings.restaurant_open_hour}:00** to **{settings.restaurant_close_hour}:00**."
        )

    @bot.command(name="help_order")
    async def help_order(ctx: commands.Context):
        """Show ordering help."""
        await ctx.send(
            "📋 **How to Order:**\n\n"
            "Just type your order naturally! For example:\n"
            "- `I want 2 chicken biryani and 1 soft drink`\n"
            "- `3 beef burgers with fries`\n"
            "- `1 pepperoni pizza and garlic bread`\n\n"
            "**Commands:**\n"
            "- `!menu` — View the full menu\n"
            "- `!hours` — Check operating hours\n"
            "- `!help_order` — Show this help message"
        )

    # Run the bot
    try:
        bot.run(token, log_handler=None)
    except Exception as exc:
        logger.error("Discord bot crashed: %s", exc)
        _bot_running = False


def start_discord_bot() -> bool:
    """
    Start the Discord bot in a background thread.

    Returns:
        True if the bot was started, False if token is missing or already running.
    """
    global _bot_thread, _bot_running

    if _bot_running:
        logger.info("Discord bot is already running.")
        return True

    token = os.getenv("DISCORD_BOT_TOKEN", "")
    channel_id = os.getenv("DISCORD_CHANNEL_ID", "")

    if not token:
        logger.warning("DISCORD_BOT_TOKEN not set. Discord bot will not start.")
        return False

    logger.info("Starting Discord bot in background thread...")
    _bot_thread = threading.Thread(
        target=_run_discord_bot,
        args=(token, channel_id),
        daemon=True,
        name="discord-bot",
    )
    _bot_thread.start()
    return True


def is_discord_bot_running() -> bool:
    """Check if the Discord bot is currently running."""
    return _bot_running
