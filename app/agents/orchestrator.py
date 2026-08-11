"""
RestaurantOS — Orchestrator Agent
Controls execution flow and routes between agents.
Never performs business logic — only coordination.
"""

from __future__ import annotations

import logging
import time

from app.models.schemas import AgentLog

logger = logging.getLogger(__name__)

AGENT_NAME = "OrchestratorAgent"

# Execution order for the workflow
AGENT_SEQUENCE = [
    "ChannelAgent",
    "OrderAgent",
    "KnowledgeAgent",
    "ValidationAgent",
    "VoiceConfirmationAgent",
    "SaveOrder",
]


def run_orchestrator(state: dict) -> dict:
    """
    LangGraph node — Orchestrator Agent.

    Responsibilities:
      1. Controls execution flow.
      2. Routes between agents.
      3. Never performs business logic.

    This is used as an entry/routing node in the LangGraph workflow.
    It determines which agent should run next based on completed_agents.

    Args:
        state: Current state dict from LangGraph.

    Returns:
        Updated state with current_agent set to the next agent.
    """
    start = time.time()
    completed = state.get("completed_agents", [])

    logger.info(
        "[%s] Routing — completed=%s",
        AGENT_NAME,
        completed,
    )

    # Determine next agent
    next_agent = None
    for agent in AGENT_SEQUENCE:
        if agent not in completed:
            next_agent = agent
            break

    if next_agent is None:
        next_agent = "END"

    duration_ms = (time.time() - start) * 1000

    log_entry = AgentLog(
        agent_name=AGENT_NAME,
        action="route",
        message=f"Routing to {next_agent} (completed: {len(completed)}/{len(AGENT_SEQUENCE)})",
        duration_ms=round(duration_ms, 2),
        success=True,
    )

    logger.info("[%s] Next agent → %s", AGENT_NAME, next_agent)

    return {
        "current_agent": next_agent,
        "logs": [log_entry.model_dump()],
    }
