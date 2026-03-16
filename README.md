# 🤖 Multi-Agent Customer Support System

An intelligent customer support system powered by **LangGraph**, **Groq AI**, **ChromaDB**, and **Redis** that automatically routes queries to specialized agents and escalates complex issues to human support.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![React](https://img.shields.io/badge/react-18.3+-61dafb.svg)

---

## 🎯 Problem Statement

Traditional customer support systems struggle with:
- **Manual routing** of tickets to appropriate departments
- **Lack of context** across conversations
- **Slow response times** for common queries
- **Inefficient escalation** processes
- **No intelligent knowledge retrieval**

This system solves these problems using a **multi-agent architecture** where specialized AI agents handle different categories of support queries with automatic routing, memory, and intelligent escalation.

---

## ✨ Features

### 🔀 **Intelligent Query Routing**
- Automatic classification of queries into categories: Billing, Technical, Returns, or General
- LLM-powered router agent that understands natural language intent
- Real-time pipeline visualization showing agent flow

### 🧠 **Persistent Memory**
- Redis-based session memory maintains conversation context
- Agents remember previous interactions within a session
- Fallback to in-memory storage when Redis is unavailable

### 💳 **Billing Agent**
- SQLite database lookup for customer records
- Handles: invoices, subscriptions, payment issues, plan changes
- Provides specific account information when email is detected

### ⚙️ **Technical Agent**
- ChromaDB vector database with 15 pre-seeded FAQ documents
- Semantic search for relevant knowledge base articles
- Handles: software errors, setup, API issues, performance problems

### 📦 **Returns Agent**
- Order lookup via SQLite database
- Decision tree logic for return eligibility (30-day policy)
- Handles: returns, refunds, exchanges, order cancellations

### 💬 **General Agent**
- Friendly conversational agent for greetings and general queries
- Guides users to appropriate specialized agents

### 🚨 **Automatic Escalation**
- Escalates to human support after 2 failed resolution attempts
- Generates unique ticket IDs with priority levels
- Tracks escalation context for human agents

### 🎨 **Modern React UI**
- Real-time agent pipeline visualization
- Beautiful gradient-based design with agent-specific colors
- SSE (Server-Sent Events) for live updates
- Session management and chat history

---

## 🏗️ Architecture

```
User Query
    ↓
Memory Node (Load session context from Redis)
    ↓
Router Agent (Classify query using LLM)
    ↓
┌───────────┬──────────────┬─────────────┬──────────────┐
│  Billing  │  Technical   │   Returns   │   General    │
│   Agent   │    Agent     │    Agent    │    Agent     │
│           │              │             │              │
│ SQLite DB │  ChromaDB    │  SQLite DB  │  Friendly    │
│  Lookup   │  Vector      │  Decision   │  Responses   │
│           │  Search      │  Tree       │              │
└─────┬─────┴──────┬───────┴──────┬──────┴──────┬───────┘
      │            │              │             │
      └────────────┴──────────────┴─────────────┘
                   ↓
          Resolved? (Check attempts)
                   ↓
              ┌────┴────┐
              │   No    │   Yes → Return Response
              ↓         │
      Escalation Node   │
      (Create Ticket)   │
              └─────────┘
```

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **LangGraph** - Agent orchestration and workflow
- **Groq API** - Fast LLM inference (FREE tier available)
- **ChromaDB** - Vector database for knowledge base
- **Redis** - Session memory and caching
- **SQLite** - Relational database for customers/orders
- **Sentence Transformers** - Local embeddings (all-MiniLM-L6-v2)

### Frontend
- **React 18** - UI framework
- **Server-Sent Events (SSE)** - Real-time updates
- **CSS3** - Modern styling with gradients and animations

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Node.js 16+**
- **Redis** (optional - system uses in-memory fallback)
- **Groq API Key** (FREE at https://console.groq.com/)

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/multi-agent-support-system.git
cd multi-agent-support-system
```

#### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env  # Windows
# OR
cp .env.example .env    # macOS/Linux

# Edit .env and add your Groq API key
# GROQ_API_KEY=your_actual_api_key_here
```

**Get FREE Groq API Key:**
1. Visit https://console.groq.com/
2. Sign up (free)
3. Go to API Keys section
4. Create new API key
5. Copy and paste into `.env` file

#### 3. Frontend Setup
```bash
cd ../frontend

# Install dependencies
npm install
```

#### 4. Start Redis (Optional)
```bash
# Windows (if installed):
redis-server

# macOS:
brew services start redis

# Linux:
sudo systemctl start redis

# If Redis is not available, the system will use in-memory storage
```

#### 5. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
# Backend runs on http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
# Frontend runs on http://localhost:3000
```

#### 6. Access the Application
- **Frontend UI:** http://localhost:3000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## 📖 Usage Guide

### Testing the System

The system comes pre-seeded with sample data. Try these queries:

#### Billing Queries
```
"I have a question about my invoice for alice.johnson@email.com"
"Can I upgrade my plan?"
"My payment failed"
```

#### Technical Queries
```
"ProSuite keeps crashing on launch"
"How do I set up CloudSync?"
"Error: Cannot connect to server"
```

#### Returns Queries
```
"I want to return order ORD-10005"
"Can I get a refund for ORD-10001?"
"How do I cancel my order?"
```

#### General Queries
```
"Hello, I need help"
"What services do you offer?"
"How do I reset my password?"
```

### Sample Data

**Sample Customer Emails:**
- alice.johnson@email.com (Pro plan, active)
- bob.martinez@email.com (Basic plan, active)
- david.lee@email.com (Pro plan, overdue)

**Sample Order IDs:**
- ORD-10000 to ORD-10019

### Viewing Sample Data
Visit http://localhost:8000/sessions/sample-data to see all available test data.

---

## 🔑 API Endpoints

### Chat
```http
POST /chat
Content-Type: application/json

{
  "session_id": "uuid-here",
  "message": "Your query here"
}
```

### Session History
```http
GET /sessions/{session_id}/history
```

### Clear Session
```http
DELETE /sessions/{session_id}
```

### Knowledge Base Search
```http
GET /knowledge-base/search?query=your+query&limit=3
```

### Health Check
```http
GET /health
```

Full API documentation available at http://localhost:8000/docs

---

## 🧪 Testing the Agent Pipeline

### Test Escalation Flow
1. Ask a complex billing question
2. Agent will attempt to resolve
3. If you respond with "This doesn't help" or similar
4. After 2 attempts, system automatically escalates
5. You'll receive a ticket ID (e.g., TKT-ABC12345)

### Test Knowledge Base
1. Ask: "ProSuite crashes on launch"
2. Technical agent searches ChromaDB
3. Returns relevant FAQ articles
4. Provides step-by-step solution

### Test Database Lookup
1. Ask: "Check invoice for alice.johnson@email.com"
2. Billing agent queries SQLite
3. Returns specific account details
4. Provides personalized response

---

## 📁 Project Structure

```
multi-agent-support-system/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── agents.py            # LangGraph agent definitions
│   ├── database.py          # SQLite models and queries
│   ├── knowledge_base.py    # ChromaDB setup and queries
│   ├── memory.py            # Redis session management
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment variables template
│   ├── support.db           # SQLite database (auto-created)
│   └── chroma_db/           # ChromaDB storage (auto-created)
├── frontend/
│   ├── public/
│   │   └── index.html       # HTML template
│   ├── src/
│   │   ├── App.js           # Main React component
│   │   ├── App.css          # Styles
│   │   └── index.js         # React entry point
│   ├── package.json         # Node dependencies
│   └── node_modules/        # Dependencies (auto-created)
├── README.md                # This file
├── .gitignore              # Git ignore rules
└── LICENSE                 # MIT License
```

---

## 🔧 Configuration

### Environment Variables (backend/.env)

```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional (defaults shown)
REDIS_URL=redis://localhost:6379
DATABASE_URL=sqlite:///./support.db
CHROMA_PERSIST_DIR=./chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_MODEL=llama-3.3-70b-versatile
```

### Groq Models Available (FREE)
- `llama-3.3-70b-versatile` (default, best performance)
- `llama-3.1-8b-instant` (faster, lower quality)
- `mixtral-8x7b-32768` (alternative)

All models are **100% FREE** with generous rate limits.

---

## 🎨 Features in Detail

### Agent Pipeline Visualization
The UI shows real-time progress through the agent pipeline:
- **Memory Node** 🧠 - Loading session context
- **Router Agent** 🔀 - Classifying query
- **Specialized Agents** 💳⚙️📦💬 - Processing request
- **Escalation** 🚨 - Creating support ticket

### Session Management
- Each conversation has a unique session ID
- Sessions persist for 1 hour in Redis
- Create new sessions with "New Session" button
- View session ID in the sidebar

### Escalation System
- Tracks resolution attempts per category
- Escalates after 2 failed attempts
- Generates unique ticket IDs
- Assigns priority based on category
- Stores context for human agents

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # macOS/Linux

# Verify Groq API key is set
cat backend/.env  # Should show your API key
```

### Frontend won't connect
```bash
# Ensure backend is running first
# Check backend health
curl http://localhost:8000/health

# Clear browser cache and reload
```

### Redis connection failed
```bash
# System will automatically use in-memory fallback
# Check Redis status
redis-cli ping  # Should return PONG

# Restart Redis if needed
redis-server
```

### ChromaDB errors
```bash
# Delete and recreate ChromaDB
rm -rf backend/chroma_db
# Restart backend - it will auto-seed
```

---

## 🚀 Deployment

### Docker Deployment (Coming Soon)
```bash
docker-compose up -d
```

### Manual Deployment
1. Set up Python environment on server
2. Install Redis
3. Configure environment variables
4. Build React frontend: `npm run build`
5. Serve with nginx or similar
6. Run backend with gunicorn: `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker`

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments

- **Groq** for free, fast LLM inference
- **LangGraph** for agent orchestration
- **ChromaDB** for vector database
- **FastAPI** for the excellent web framework
- **React** for the UI framework

---

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review API documentation at `/docs`

---

## 🎯 Future Enhancements

- [ ] Voice input support
- [ ] Multi-language support
- [ ] Analytics dashboard
- [ ] Email notifications for escalations
- [ ] Slack/Teams integration
- [ ] Custom agent training
- [ ] Advanced reporting

---

**Built with ❤️ using LangGraph, Groq, ChromaDB, and Redis**

**⭐ Star this repo if you find it useful!**
