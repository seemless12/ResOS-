# 🍽️ RestaurantOS — Multi-Agent Restaurant Operations System

A production-grade MVP Multi-Agent AI System built with **LangGraph** where customer requests from multiple channels (Website Chat, WhatsApp, Discord) become unified tickets, pass through specialized AI agents, are validated via RAG, stored in MongoDB, and generate confirmation messages.

---

## 🏗️ Architecture

```
                    ┌──────────────┐
                    │   Channels   │
                    │ Web│WA│Discord│
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ Channel Agent │  📡 Create Ticket & Init State
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Order Agent  │  📝 Extract Items via LLM
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │Knowledge Agent│  🧠 MongoDB RAG Retrieval
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │Validation Agt │  ✅ Validate Menu & Prices
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Voice Agent  │  🔊 Generate Confirmation
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Save Order   │  💾 Persist to MongoDB
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │     END       │
                    └───────────────┘
```

All agents communicate **only** through the shared `RestaurantState`. The Orchestrator controls routing — agents never call each other directly.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3.10+** | Core language |
| **FastAPI** | REST API server |
| **LangGraph** | Multi-agent orchestration |
| **MongoDB** | Database + RAG knowledge store |
| **OpenRouter** | LLM API (GPT-4o-mini) |
| **Streamlit** | Dashboard UI |
| **Pydantic** | Data validation |
| **Discord.py** | Discord bot integration |

---

## 📁 Project Structure

```
restaurant_os/
├── app/
│   ├── agents/
│   │   ├── channel_agent.py      # Ticket creation & state init
│   │   ├── order_agent.py        # LLM-powered order extraction
│   │   ├── knowledge_agent.py    # MongoDB RAG retrieval
│   │   ├── validation_agent.py   # Menu & price validation
│   │   ├── voice_agent.py        # Confirmation message generation
│   │   ├── orchestrator.py       # Execution flow control
│   │   └── discord_bot.py        # Discord channel integration
│   ├── graph/
│   │   ├── state.py              # Shared RestaurantState model
│   │   └── workflow.py           # LangGraph workflow definition
│   ├── database/
│   │   └── mongodb.py            # MongoDB client + CRUD + RAG
│   ├── rag/
│   │   ├── restaurant_data.py    # Menu, FAQs, policies data
│   │   └── retriever.py          # RAG retrieval logic
│   ├── api/
│   │   └── routes.py             # FastAPI endpoints
│   ├── models/
│   │   └── schemas.py            # Pydantic models
│   ├── prompts/
│   │   └── templates.py          # LLM prompt templates
│   ├── utils/
│   │   └── llm.py                # OpenRouter LLM client
│   ├── config.py                 # Centralized configuration
│   └── main.py                   # FastAPI entry point
├── tests/
│   └── test_all.py               # Comprehensive test suite
├── streamlit_app.py              # Streamlit dashboard
├── requirements.txt              # Dependencies
├── .env                          # Environment variables
└── README.md                     # This file
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd Resturent-Os
pip install -r requirements.txt
```

### 2. Configure Environment

Edit the `.env` file with your credentials:

```env
MONGODB_URI=mongodb+srv://...
OPENROUTER_API_KEY=sk-or-v1-...
DISCORD_BOT_TOKEN=your_token    # Optional
DISCORD_CHANNEL_ID=123456789    # Optional — numeric channel ID
```

### 3. Start FastAPI Server

```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 4. Start Streamlit Dashboard

```bash
streamlit run streamlit_app.py
```

### 5. Run Tests

```bash
python -m pytest tests/ -v
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Process a chat message through the workflow |
| `POST` | `/api/ticket` | Create a ticket (alias for /chat) |
| `GET` | `/api/ticket/{id}` | Get ticket details by ID |
| `GET` | `/api/tickets` | List recent tickets |
| `GET` | `/api/health` | Health check |

### Example: POST /api/chat

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want 2 chicken biryani and 1 soft drink",
    "channel": "website",
    "customer_name": "Ali",
    "customer_phone": "+92300-1234567",
    "customer_address": "Block 5, Clifton, Karachi"
  }'
```

---

## 🤖 Agent Details

### Channel Agent
- Creates unique ticket ID (TKT-XXXXXXXX)
- Stores channel source (website/whatsapp/discord)
- Initializes customer info in state

### Order Agent
- Uses LLM to detect intent (order/inquiry/complaint)
- Extracts items, quantities, special instructions
- Creates structured `ExtractedOrder`

### Knowledge Agent
- Queries MongoDB for relevant menu items, FAQs, policies
- Uses text search for RAG retrieval
- Injects context into state for downstream agents

### Validation Agent
- Validates items exist on the menu
- Checks quantities (1-50 per item)
- Calculates prices and delivery fees
- Fuzzy matches item names

### Voice Confirmation Agent
- Generates natural language confirmation via LLM
- Falls back to template if LLM fails
- Includes order summary, total, and ticket ID

---

## 🎮 Discord Bot

The Discord bot listens for messages and processes orders:

- **Direct message**: Just type your order naturally
- **!menu** — View the full restaurant menu
- **!hours** — Check operating hours
- **!help_order** — Show ordering instructions

---

## 🗄️ MongoDB Collections

| Collection | Purpose |
|---|---|
| `tickets` | Full ticket documents with all agent outputs |
| `orders` | Validated order details |
| `customers` | Customer information |
| `logs` | Agent execution logs |
| `knowledge` | Restaurant knowledge base (menu, FAQs, policies) |

---

## 📋 Menu Highlights

| Category | Items | Price Range (PKR) |
|---|---|---|
| Biryani | Chicken, Mutton, Vegetable | 300 - 550 |
| Burgers | Beef, Chicken, Zinger | 350 - 450 |
| Pizza | Margherita, Pepperoni, BBQ Chicken | 800 - 950 |
| Karahi | Chicken, Mutton | 1200 - 1800 |
| BBQ | Seekh Kebab, Chicken Tikka | 120 - 600 |
| Sides | Fries, Garlic Bread, Caesar Salad, Wings | 200 - 500 |
| Beverages | Soft Drink, Fresh Juice, Iced Tea, Water | 50 - 200 |
| Desserts | Chocolate Cake, Ice Cream, Gulab Jamun | 180 - 350 |

---

## 🧪 Testing

Tests cover all modules with mocked LLM calls:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test class
python -m pytest tests/test_all.py::TestValidationAgent -v
```

---

## 📜 License

MIT License — Built as an MVP demonstration of multi-agent AI systems.
