# How to Run RestaurantOS

This guide covers how to set up and run the RestaurantOS multi-agent system. The application consists of a **FastAPI Backend** (which hosts the LangGraph agents, MongoDB connection, and Discord bot) and a **Streamlit Dashboard** (for viewing orders and tickets).

## 1. Prerequisites
Make sure your `.env` file is properly configured in the root directory. You must have:
- `MONGODB_URI` (Your MongoDB connection string)
- `OPENROUTER_API_KEY` (Your OpenRouter API key for the LLM)
- `DISCORD_BOT_TOKEN` (Your Discord bot token)
- *Note: Leave `DISCORD_CHANNEL_ID` blank if you want the bot to reply in all channels.*

## 2. Start the Backend (FastAPI + Discord Bot)
The backend handles all the AI agent logic, database interactions, and runs the Discord bot in the background.

Open a terminal in the root directory (`Resturent-Os`) and run:
```bash
python -m uvicorn app.main:app --reload --port 8000
```
*Wait until you see the logs stating `Discord bot logged in as...` and `Connected guilds: ...` before testing the Discord bot.*

## 3. Start the Dashboard (Streamlit)
The dashboard provides a visual interface for the restaurant staff to see incoming orders, active tickets, and chat history.

Open a **new, separate terminal** in the root directory and run:
```bash
python -m streamlit run streamlit_app.py --server.port 8501
```
*(If port 8501 is already in use, you can change `--server.port 8501` to `--server.port 8502`)*

## 4. How to Test
Once both servers are running, you can test the system in multiple ways:

- **Via Discord:** Go to your Discord server and type `!menu` to see the menu. Then send a message like `I want 2 beef burgers and fries` to place an order.
- **Via the Dashboard:** Open the Streamlit URL provided in the terminal (usually `http://localhost:8501`). You can view tickets here as they are created.
- **Via API directly:** You can view the API documentation at `http://localhost:8000/docs`.

## Useful Commands
- **Run the Test Suite:** `python -m pytest tests/ -v`
- **Seed Dummy Data:** `python seed_dummy_data.py` (If you want to inject some fake orders to see what the dashboard looks like)
