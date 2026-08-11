"""
RestaurantOS — Streamlit Dashboard
Interactive UI for chat, ticket viewing, workflow status, and logs.
"""

from __future__ import annotations

import json
import sys
import os
from datetime import datetime

import streamlit as st
import httpx

# ── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="RestaurantOS — Dashboard",
    page_icon="P",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Configuration ────────────────────────────────────────────────────────────

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")


# ── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    /* Global Typography & Background */
    .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background: #0f172a;
        color: #f8fafc;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid #334155;
    }

    /* Main Header */
    .main-header {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #db2777 100%);
        padding: 2rem 2.5rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 12px 40px rgba(124, 58, 237, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.02em;
    }
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.05rem;
        font-weight: 500;
    }

    /* Glassmorphic Cards */
    .status-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.4rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .status-card:hover {
        transform: translateY(-4px);
        border-color: #818cf8;
        box-shadow: 0 12px 40px rgba(99, 102, 241, 0.2);
    }

    /* Agent Flow Steps */
    .agent-step {
        padding: 0.8rem 1.2rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        font-size: 0.95rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .agent-completed {
        background: rgba(16, 185, 129, 0.15);
        border-left: 5px solid #10b981;
        color: #34d399;
    }
    .agent-active {
        background: rgba(245, 158, 11, 0.15);
        border-left: 5px solid #f59e0b;
        color: #fbbf24;
        animation: pulse 1.5s infinite;
    }
    .agent-pending {
        background: rgba(51, 65, 85, 0.4);
        border-left: 5px solid #64748b;
        color: #94a3b8;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }

    /* Chat Bubbles */
    .chat-user {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: #ffffff;
        padding: 1rem 1.3rem;
        border-radius: 20px 20px 4px 20px;
        margin: 0.75rem 0;
        max-width: 82%;
        margin-left: auto;
        font-weight: 500;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
    }
    .chat-bot {
        background: #1e293b;
        color: #f1f5f9;
        padding: 1rem 1.3rem;
        border-radius: 20px 20px 20px 4px;
        margin: 0.75rem 0;
        max-width: 85%;
        border: 1px solid #334155;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }

    /* Buttons Styling */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        background: linear-gradient(135deg, #312e81 0%, #4338ca 100%) !important;
        color: #ffffff !important;
        border: 1px solid #6366f1 !important;
        transition: all 0.25s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4) !important;
        border-color: #a5b4fc !important;
    }

    /* Audio Player Custom Styling */
    audio {
        width: 100%;
        border-radius: 30px;
        filter: invert(0.9) hue-rotate(180deg);
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Helper Functions ─────────────────────────────────────────────────────────

def call_api(message: str, channel: str, name: str, phone: str, address: str) -> dict:
    """Send a chat request to the FastAPI backend."""
    try:
        response = httpx.post(
            f"{API_BASE}/chat",
            json={
                "message": message,
                "channel": channel,
                "customer_name": name,
                "customer_phone": phone,
                "customer_address": address,
            },
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()
    except httpx.ConnectError:
        return {"error": "Cannot connect to API server. Make sure FastAPI is running on port 8000."}
    except Exception as e:
        return {"error": str(e)}


def get_ticket_api(ticket_id: str) -> dict:
    """Fetch ticket details from API."""
    try:
        response = httpx.get(f"{API_BASE}/ticket/{ticket_id}", timeout=30.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def get_all_tickets_api() -> list:
    """Fetch all recent tickets."""
    try:
        response = httpx.get(f"{API_BASE}/tickets?limit=20", timeout=30.0)
        response.raise_for_status()
        data = response.json()
        return data.get("tickets", [])
    except Exception:
        return []


# ── Session State Init ──────────────────────────────────────────────────────

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_ticket_detail" not in st.session_state:
    st.session_state.last_ticket_detail = None


# ── Header ───────────────────────────────────────────────────────────────────

st.markdown("""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1>Pizza Max — RestaurantOS Dashboard</h1>
            <p>Omni-Channel Operations Center — Powered by LangGraph AI Agents</p>
        </div>
        <div>
            <a href="http://localhost:8000/static/index.html" target="_blank" style="background: rgba(255,255,255,0.2); backdrop-filter: blur(10px); color: white; padding: 0.7rem 1.4rem; border-radius: 30px; text-decoration: none; font-weight: 700; border: 1px solid rgba(255,255,255,0.3); display: inline-flex; align-items: center; gap: 0.5rem;">
                Launch Storefront Website
            </a>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Channel Simulator")
    st.divider()

    channel = st.selectbox(
        "Input Channel",
        ["website", "whatsapp", "discord"],
        index=0,
        help="Simulate customer ordering channel",
    )

    st.markdown("### Customer Info")
    customer_name = st.text_input("Name", value="Ali Khan", placeholder="Customer name")
    customer_phone = st.text_input("Phone", value="+92300-1234567", placeholder="Phone number")
    customer_address = st.text_input("Address", value="Block 5, Clifton, Karachi", placeholder="Delivery address")

    st.divider()
    st.markdown("### System Health & Status")

    # Health check
    try:
        health = httpx.get(f"{API_BASE}/health", timeout=5.0)
        if health.status_code == 200:
            st.success("API Server Online (Port 8000)")
        else:
            st.error("API Server Error")
    except Exception:
        st.error("API Server Offline")
        st.caption("Run: `python -m uvicorn app.main:app --reload`")

    st.divider()
    st.markdown("### Omni-Channel Links")
    st.markdown("- [Customer Storefront Website](http://localhost:8000/static/index.html)")
    st.markdown("- Discord Bot Channel Integration")
    st.markdown("- WhatsApp Business API Simulator")


# ── Main Tabs ────────────────────────────────────────────────────────────────

tab_chat, tab_tickets, tab_workflow, tab_logs = st.tabs([
    "Live Chat", "Active Tickets", "Agent Workflow", "System Logs"
])


# ── Tab 1: Chat ─────────────────────────────────────────────────────────────

with tab_chat:
    col_chat, col_result = st.columns([1, 1])

    with col_chat:
        st.markdown("### Restaurant Chat")
        st.caption(f"Channel: **{channel.upper()}** | Customer: **{customer_name}**")

        # Display chat history
        chat_container = st.container(height=400)
        with chat_container:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(
                        f'<div class="chat-user">{msg["content"]}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="chat-bot">{msg["content"]}</div>',
                        unsafe_allow_html=True,
                    )

        # Input
        user_input = st.chat_input("Type your order... e.g. 'I want 2 chicken biryani and 1 pepperoni pizza'")

        if user_input:
            # Add to history
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            with st.spinner("Processing through AI agents..."):
                result = call_api(user_input, channel, customer_name, customer_phone, customer_address)

            if "error" in result:
                st.session_state.chat_history.append({
                    "role": "bot",
                    "content": f"Error: {result['error']}",
                })
            else:
                confirmation = result.get("confirmation", "Order processed.")
                st.session_state.chat_history.append({"role": "bot", "content": confirmation})
                st.session_state.last_result = result

            st.rerun()

    with col_result:
        st.markdown("### Last Order Result")

        if st.session_state.last_result:
            result = st.session_state.last_result

            # Ticket info
            ticket_id = result.get("ticket_id", "N/A")
            status_val = result.get("status", "unknown")
            status_emoji = "[OK]" if status_val == "completed" else "[...]" if status_val == "processing" else "[FAIL]"

            st.markdown(f"**Ticket:** `{ticket_id}` {status_emoji}")
            st.markdown(f"**Status:** {status_val.upper()}")

            # Order summary
            order = result.get("order_summary")
            if order:
                st.markdown("#### Order Items")
                for item in order.get("items", []):
                    st.markdown(
                        f"- **{item.get('quantity', 1)}x** {item.get('name', 'Unknown')} "
                        f"— PKR {item.get('total_price', 0):.0f}"
                    )
                st.markdown(f"**Subtotal:** PKR {order.get('subtotal', 0):.0f}")
                if order.get("delivery_fee", 0) > 0:
                    st.markdown(f"**Delivery:** PKR {order.get('delivery_fee', 0):.0f}")
                else:
                    st.markdown("**Delivery:** FREE")
                st.markdown(f"### Total: PKR {order.get('total', 0):.0f}")

            # Validation
            validation = result.get("validation")
            if validation:
                if validation.get("is_valid"):
                    st.success("Order validated successfully.")
                else:
                    st.error("Validation failed")
                    for err in validation.get("errors", []):
                        st.markdown(f"  - {err}")
                for warn in validation.get("warnings", []):
                    st.warning(warn)

            # Call script & audio
            call_script = result.get("call_script")
            call_audio_path = result.get("call_audio_path")
            if call_script:
                st.markdown("---")
                st.markdown("#### Automated Customer Call")
                st.info(f"**Call Script:**\n_{call_script}_")
                if call_audio_path and os.path.exists(call_audio_path):
                    st.audio(call_audio_path)
        else:
            st.info("Send a message in the chat to see the order result here.")

    # Quick order buttons
    st.divider()
    st.markdown("### Quick Orders")
    quick_cols = st.columns(4)

    quick_orders = [
        ("Ranch Deal", "I want 1 Medium Ranch Pizza and Tangy Wings"),
        ("Sriracha Pizza", "2 Medium Sriracha Pizzas"),
        ("Max Deal", "I want the Max Deal"),
        ("Lasagne + Sticks", "1 Creamy Chicken Lasagne and Mozzarella Sticks"),
    ]

    for i, (label, order_text) in enumerate(quick_orders):
        with quick_cols[i]:
            if st.button(label, use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": order_text})
                with st.spinner("Processing..."):
                    result = call_api(order_text, channel, customer_name, customer_phone, customer_address)
                if "error" not in result:
                    st.session_state.chat_history.append({
                        "role": "bot",
                        "content": result.get("confirmation", "Order processed."),
                    })
                    st.session_state.last_result = result
                st.rerun()


# ── Tab 2: Tickets ──────────────────────────────────────────────────────────

with tab_tickets:
    st.markdown("### Ticket Viewer")

    col_list, col_detail = st.columns([1, 2])

    with col_list:
        st.markdown("#### Recent Tickets")
        if st.button("Refresh Tickets"):
            st.rerun()

        tickets = get_all_tickets_api()

        if tickets:
            for t in tickets:
                ticket_info = t.get("ticket", {})
                tid = ticket_info.get("ticket_id", "N/A")
                tstatus = ticket_info.get("status", "unknown")
                emoji = "[OK]" if tstatus == "completed" else "[FAIL]" if tstatus == "failed" else "[...]"

                if st.button(f"{emoji} {tid}", key=f"ticket_{tid}", use_container_width=True):
                    st.session_state.last_ticket_detail = t
        else:
            st.info("No tickets found. Send an order in the Chat tab first.")

    with col_detail:
        st.markdown("#### Ticket Details")

        detail = st.session_state.last_ticket_detail
        if detail:
            ticket = detail.get("ticket", {})
            customer = detail.get("customer", {})

            st.markdown(f"**Ticket ID:** `{ticket.get('ticket_id', 'N/A')}`")
            st.markdown(f"**Status:** {ticket.get('status', 'unknown').upper()}")
            st.markdown(f"**Channel:** {detail.get('channel_source', 'N/A')}")
            st.markdown(f"**Customer:** {customer.get('name', 'N/A')}")
            st.markdown(f"**Phone:** {customer.get('phone', 'N/A')}")
            st.markdown(f"**Message:** _{detail.get('user_message', 'N/A')}_")
            st.markdown(f"**Intent:** {detail.get('detected_intent', 'N/A')}")

            # Order details
            validation = detail.get("validation_result", {})
            validated_order = validation.get("validated_order", {})
            if validated_order and validated_order.get("items"):
                st.markdown("---")
                st.markdown("#### Order")
                for item in validated_order["items"]:
                    st.markdown(
                        f"- {item.get('quantity', 1)}x **{item.get('name', '?')}** "
                        f"— PKR {item.get('total_price', 0):.0f}"
                    )
                st.markdown(f"**Total: PKR {validated_order.get('total', 0):.0f}**")

            # Call details
            if detail.get("call_script"):
                st.markdown("---")
                st.markdown("#### Call Script & Audio")
                st.info(detail["call_script"])

            # Confirmation
            if detail.get("confirmation_message"):
                st.markdown("---")
                st.markdown("#### Confirmation")
                st.markdown(detail["confirmation_message"])
        else:
            st.info("Select a ticket from the list to view details.")


# ── Tab 3: Workflow ─────────────────────────────────────────────────────────

with tab_workflow:
    st.markdown("### Agent Workflow Status")

    AGENT_SEQUENCE = [
        ("ChannelAgent", "1", "Accepts request, creates ticket"),
        ("OrderAgent", "2", "Extracts items and intent via LLM"),
        ("KnowledgeAgent", "3", "Retrieves menu & policies (MongoDB RAG)"),
        ("ValidationAgent", "4", "Validates items, quantities, prices"),
        ("VoiceConfirmationAgent", "5", "Generates confirmation message"),
        ("CallingAgent", "6", "Places TTS audio call to customer"),
        ("SaveOrder", "7", "Persists to MongoDB"),
    ]

    # Get completed agents from last result
    completed = []
    if st.session_state.last_result:
        # Fetch the full ticket to get completed agents
        tid = st.session_state.last_result.get("ticket_id", "")
        if tid:
            full_ticket = get_ticket_api(tid)
            completed = full_ticket.get("completed_agents", [])

    for agent_name, icon, description in AGENT_SEQUENCE:
        if agent_name in completed:
            css_class = "agent-completed"
            status_icon = "[OK]"
        else:
            css_class = "agent-pending"
            status_icon = "[--]"

        st.markdown(
            f'<div class="agent-step {css_class}">'
            f'{status_icon} {icon} <strong>{agent_name}</strong> — {description}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Workflow diagram
    st.markdown("---")
    st.markdown("### Workflow Diagram")
    st.markdown("""
    ```
    START
      |-> ChannelAgent     (Create Ticket)
      |-> OrderAgent       (Extract Items via LLM)
      |-> KnowledgeAgent   (MongoDB RAG Lookup)
      |-> ValidationAgent  (Check Menu & Prices)
      |-> VoiceAgent       (Generate Confirmation)
      |-> CallingAgent     (TTS Audio Call)
      |-> SaveOrder        (MongoDB Persist)
    END
    ```
    """)


# ── Tab 4: Logs ─────────────────────────────────────────────────────────────

with tab_logs:
    st.markdown("### Execution Logs")

    if st.session_state.last_result:
        tid = st.session_state.last_result.get("ticket_id", "")
        if tid:
            full_ticket = get_ticket_api(tid)
            if not isinstance(full_ticket, dict) or "error" in full_ticket:
                st.warning("Could not fetch ticket logs.")
            else:
                st.markdown(f"**Ticket:** `{tid}`")
                st.divider()

                # Show completed agents as a timeline
                completed = full_ticket.get("completed_agents", [])
                if completed:
                    st.markdown("#### Agent Execution Order")
                    for i, agent in enumerate(completed):
                        st.markdown(f"**{i+1}.** {agent}")

                # Show raw state
                st.markdown("---")
                st.markdown("#### Full State")
                with st.expander("View raw ticket data", expanded=False):
                    st.json(full_ticket)
    else:
        st.info("Process an order in the Chat tab to see execution logs.")


# ── Footer ───────────────────────────────────────────────────────────────────

st.divider()
st.markdown(
    "<p style='text-align:center; color:#888; font-size:0.85rem;'>"
    "RestaurantOS v1.0.0 — Multi-Agent System powered by LangGraph, FastAPI & MongoDB"
    "</p>",
    unsafe_allow_html=True,
)
