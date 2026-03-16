"""
Multi-Agent Customer Support System — LangGraph Pipeline

Architecture:
  Memory Node → Router Agent → [Billing | Technical | Returns | General] Agent
                                         ↓ (if unresolved after 2 attempts)
                                    Escalation Node
"""

import os
import json
import re
from typing import TypedDict, Annotated, Literal
from datetime import datetime

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END

import database as db
import knowledge_base as kb
import memory as mem

LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


def get_llm():
    return ChatGroq(
        model=LLM_MODEL,
        api_key=GROQ_API_KEY,
        temperature=0.3,
        max_tokens=1024,
    )


# ─────────────────────────────────────────────
# State Definition
# ─────────────────────────────────────────────

class AgentState(TypedDict):
    session_id: str
    user_message: str
    chat_history: list
    category: str
    current_agent: str
    agent_response: str
    resolved: bool
    attempt_count: int
    escalation_ticket: str | None
    nodes_fired: list
    tool_results: dict


# ─────────────────────────────────────────────
# Node 1: Memory Node
# ─────────────────────────────────────────────

def memory_node(state: AgentState) -> AgentState:
    """Load conversation history from Redis."""
    session_id = state["session_id"]
    history = mem.load_session_context(session_id)
    state["chat_history"] = history
    state["nodes_fired"] = state.get("nodes_fired", []) + ["memory"]
    state["tool_results"] = state.get("tool_results", {})
    state["escalation_ticket"] = state.get("escalation_ticket")
    return state


# ─────────────────────────────────────────────
# Node 2: Router Agent
# ─────────────────────────────────────────────

def router_node(state: AgentState) -> AgentState:
    """Classify the query and route to the correct sub-agent."""
    llm = get_llm()

    system_prompt = """You are a customer support router. Classify the user's message into exactly one category.

Categories:
- billing: Payment issues, invoice questions, subscription changes, charges, refunds of charges, plan upgrades/downgrades
- technical: Software errors, setup help, feature questions, app crashes, API issues, performance problems
- returns: Return requests, refund for products, exchange requests, order cancellation
- general: Greetings, account info, general questions not fitting other categories

Respond with ONLY a JSON object like: {"category": "billing", "confidence": 0.95, "reasoning": "User asking about invoice"}
No other text."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Classify this message: {state['user_message']}")
    ]

    response = llm.invoke(messages)
    
    try:
        # Extract JSON from response
        text = response.content.strip()
        # Handle markdown code blocks
        if "```" in text:
            text = re.sub(r"```(?:json)?\n?", "", text).strip()
        result = json.loads(text)
        category = result.get("category", "general")
    except Exception:
        category = "general"

    valid_categories = {"billing", "technical", "returns", "general"}
    if category not in valid_categories:
        category = "general"

    state["category"] = category
    state["current_agent"] = f"{category}_agent"
    state["nodes_fired"] = state.get("nodes_fired", []) + ["router"]
    state["resolved"] = False
    state["attempt_count"] = mem.get_session_metadata(state["session_id"]).get("attempt_count", {}).get(category, 0)
    return state


# ─────────────────────────────────────────────
# Node 3a: Billing Agent
# ─────────────────────────────────────────────

def billing_agent_node(state: AgentState) -> AgentState:
    """Handle billing and subscription queries with SQLite lookup."""
    llm = get_llm()
    session_id = state["session_id"]
    user_msg = state["user_message"]

    # Attempt to extract email from message or history for DB lookup
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, user_msg)

    # Check history for email too
    for msg in state.get("chat_history", []):
        if isinstance(msg, dict):
            found = re.findall(email_pattern, msg.get("content", ""))
            emails.extend(found)

    customer_data = None
    if emails:
        customer_data = db.lookup_customer(emails[0])

    tool_context = ""
    if customer_data:
        tool_context = f"""
Customer Record Found:
- Name: {customer_data['name']}
- Email: {customer_data['email']}
- Plan: {customer_data['plan']}
- Billing Status: {customer_data['billing_status']}
- Last Invoice: ${customer_data['last_invoice_amount']} on {customer_data['last_invoice_date']}
- Next Billing: {customer_data['next_billing_date']}
- Payment Method: {customer_data['payment_method']}
"""
        state["tool_results"]["customer"] = customer_data
    else:
        tool_context = "No customer record found via email. Responding based on general billing policies."

    # Build history context
    history_msgs = []
    for msg in state.get("chat_history", [])[-6:]:
        if isinstance(msg, dict):
            if msg["role"] == "user":
                history_msgs.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                history_msgs.append(AIMessage(content=msg["content"]))

    system_prompt = f"""You are the Billing Agent for ProSuite customer support.
You handle: payment issues, invoice questions, subscription plans, billing disputes, plan changes.

{tool_context}

Be helpful, professional, and specific. If you have customer data, reference it directly.
If you cannot resolve the issue or need information you don't have, say "I need to escalate this."
Keep responses concise (2-4 sentences). Today's date: {datetime.now().strftime('%B %d, %Y')}."""

    messages = [SystemMessage(content=system_prompt)] + history_msgs + [HumanMessage(content=user_msg)]

    response = llm.invoke(messages)
    answer = response.content

    # Determine if resolved
    escalation_triggers = ["escalate", "cannot resolve", "human agent", "cannot help"]
    resolved = not any(trigger in answer.lower() for trigger in escalation_triggers)

    attempts = mem.increment_attempt_count(session_id, "billing")

    state["agent_response"] = answer
    state["resolved"] = resolved
    state["attempt_count"] = attempts
    state["nodes_fired"] = state.get("nodes_fired", []) + ["billing_agent"]
    return state


# ─────────────────────────────────────────────
# Node 3b: Technical Agent
# ─────────────────────────────────────────────

def technical_agent_node(state: AgentState) -> AgentState:
    """Handle technical queries using ChromaDB knowledge base."""
    llm = get_llm()
    session_id = state["session_id"]
    user_msg = state["user_message"]

    # Query knowledge base
    kb_results = kb.query_knowledge_base(user_msg, n_results=3)
    
    kb_context = ""
    if kb_results:
        kb_context = "Relevant knowledge base articles:\n\n"
        for i, doc in enumerate(kb_results, 1):
            kb_context += f"{i}. [{doc['title']}]\n{doc['content']}\n\n"
        state["tool_results"]["kb_results"] = [{"title": d["title"], "score": d["relevance_score"]} for d in kb_results]
    else:
        kb_context = "No specific knowledge base articles found for this query."

    history_msgs = []
    for msg in state.get("chat_history", [])[-6:]:
        if isinstance(msg, dict):
            if msg["role"] == "user":
                history_msgs.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                history_msgs.append(AIMessage(content=msg["content"]))

    system_prompt = f"""You are the Technical Support Agent for ProSuite.
You handle: software errors, installation issues, feature questions, API problems, performance.

{kb_context}

Use the knowledge base information to give accurate, step-by-step answers.
If the issue is complex or not covered in the knowledge base, say "I need to escalate this."
Be technical but clear. Number your steps. Today's date: {datetime.now().strftime('%B %d, %Y')}."""

    messages = [SystemMessage(content=system_prompt)] + history_msgs + [HumanMessage(content=user_msg)]

    response = llm.invoke(messages)
    answer = response.content

    escalation_triggers = ["escalate", "cannot resolve", "not covered", "need more information"]
    resolved = not any(trigger in answer.lower() for trigger in escalation_triggers)

    attempts = mem.increment_attempt_count(session_id, "technical")

    state["agent_response"] = answer
    state["resolved"] = resolved
    state["attempt_count"] = attempts
    state["nodes_fired"] = state.get("nodes_fired", []) + ["technical_agent"]
    return state


# ─────────────────────────────────────────────
# Node 3c: Returns Agent
# ─────────────────────────────────────────────

def returns_agent_node(state: AgentState) -> AgentState:
    """Handle return and refund requests with decision tree logic."""
    llm = get_llm()
    session_id = state["session_id"]
    user_msg = state["user_message"]

    # Try to find order ID in message
    order_pattern = r'ORD-\d+'
    order_ids = re.findall(order_pattern, user_msg.upper())
    
    # Also check history
    for msg in state.get("chat_history", []):
        if isinstance(msg, dict):
            found = re.findall(order_pattern, msg.get("content", "").upper())
            order_ids.extend(found)

    order_data = None
    if order_ids:
        order_data = db.lookup_order(order_ids[0])

    # Decision tree logic
    tool_context = ""
    return_decision = None

    if order_data:
        state["tool_results"]["order"] = order_data
        days_since = (datetime.now() - datetime.strptime(order_data["purchase_date"], "%Y-%m-%d")).days
        
        if order_data["status"] == "returned":
            return_decision = "ALREADY_RETURNED"
        elif order_data["status"] == "cancelled":
            return_decision = "ORDER_CANCELLED"
        elif not order_data["return_eligible"]:
            return_decision = "NOT_ELIGIBLE"
        else:
            return_decision = "ELIGIBLE"

        tool_context = f"""
Order Record Found:
- Order ID: {order_data['order_id']}
- Product: {order_data['product']}
- Status: {order_data['status']}
- Purchase Date: {order_data['purchase_date']} ({days_since} days ago)
- Return Eligible: {'Yes' if order_data['return_eligible'] else 'No'}
- Return Deadline: {order_data['return_deadline']}
- Amount: ${order_data['amount']}
- Return Decision: {return_decision}
"""
    else:
        tool_context = "No order found. Ask customer for their order ID (format: ORD-XXXXX)."

    history_msgs = []
    for msg in state.get("chat_history", [])[-6:]:
        if isinstance(msg, dict):
            if msg["role"] == "user":
                history_msgs.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                history_msgs.append(AIMessage(content=msg["content"]))

    system_prompt = f"""You are the Returns & Refunds Agent for ProSuite.
You handle: return requests, refunds, exchanges, order issues.

Return Policy: 30-day return window. Full refund to original payment method within 5-7 business days.

{tool_context}

If order is ELIGIBLE: confirm return, explain refund process (5-7 business days).
If NOT_ELIGIBLE: explain policy sympathetically, offer alternatives.
If ALREADY_RETURNED: inform customer.
If no order ID: ask for it politely.
If issue is complex, say "I need to escalate this." Today: {datetime.now().strftime('%B %d, %Y')}."""

    messages = [SystemMessage(content=system_prompt)] + history_msgs + [HumanMessage(content=user_msg)]

    response = llm.invoke(messages)
    answer = response.content

    escalation_triggers = ["escalate", "cannot resolve", "cannot process", "special case"]
    resolved = not any(trigger in answer.lower() for trigger in escalation_triggers)

    attempts = mem.increment_attempt_count(session_id, "returns")

    state["agent_response"] = answer
    state["resolved"] = resolved
    state["attempt_count"] = attempts
    state["nodes_fired"] = state.get("nodes_fired", []) + ["returns_agent"]
    return state


# ─────────────────────────────────────────────
# Node 3d: General Agent
# ─────────────────────────────────────────────

def general_agent_node(state: AgentState) -> AgentState:
    """Handle general queries and greetings."""
    llm = get_llm()
    session_id = state["session_id"]
    user_msg = state["user_message"]

    history_msgs = []
    for msg in state.get("chat_history", [])[-6:]:
        if isinstance(msg, dict):
            if msg["role"] == "user":
                history_msgs.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                history_msgs.append(AIMessage(content=msg["content"]))

    system_prompt = f"""You are a friendly customer support assistant for ProSuite.
For general questions, greet warmly and offer to help with:
- Billing questions (invoices, subscriptions, payments)
- Technical support (software issues, setup, features)
- Returns and refunds (return requests, order status)

Be warm, professional, and brief. Today: {datetime.now().strftime('%B %d, %Y')}."""

    messages = [SystemMessage(content=system_prompt)] + history_msgs + [HumanMessage(content=user_msg)]

    response = llm.invoke(messages)

    mem.increment_attempt_count(session_id, "general")

    state["agent_response"] = response.content
    state["resolved"] = True
    state["nodes_fired"] = state.get("nodes_fired", []) + ["general_agent"]
    return state


# ─────────────────────────────────────────────
# Node 4: Escalation Node
# ─────────────────────────────────────────────

def escalation_node(state: AgentState) -> AgentState:
    """Escalate to human support — generates a ticket."""
    session_id = state["session_id"]
    category = state.get("category", "general")
    user_msg = state["user_message"]

    # Determine priority based on category
    priority_map = {"billing": "high", "technical": "medium", "returns": "high", "general": "low"}
    priority = priority_map.get(category, "medium")

    description = f"Automated escalation after {state.get('attempt_count', 2)} failed resolution attempts.\n"
    description += f"Category: {category}\n"
    description += f"Last user message: {user_msg}\n"
    if state.get("tool_results"):
        description += f"Context data: {json.dumps(state['tool_results'], indent=2)}"

    ticket_id = db.create_ticket(
        session_id=session_id,
        issue_type=category,
        description=description,
        priority=priority
    )

    escalation_message = (
        f"I've escalated your case to our human support team. "
        f"Your ticket ID is **{ticket_id}** (priority: {priority}). "
        f"A specialist will contact you within 24 hours. "
        f"You can track your ticket status using this ID."
    )

    state["agent_response"] = escalation_message
    state["escalation_ticket"] = ticket_id
    state["resolved"] = True
    state["nodes_fired"] = state.get("nodes_fired", []) + ["escalation"]
    return state


# ─────────────────────────────────────────────
# Routing Logic
# ─────────────────────────────────────────────

def route_after_router(state: AgentState) -> str:
    category = state.get("category", "general")
    return f"{category}_agent"


def route_after_agent(state: AgentState) -> str:
    """Decide whether to escalate after an agent responds."""
    if not state.get("resolved") and state.get("attempt_count", 0) >= 2:
        return "escalation"
    return END


# ─────────────────────────────────────────────
# Build LangGraph
# ─────────────────────────────────────────────

def build_graph():
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("memory", memory_node)
    graph.add_node("router", router_node)
    graph.add_node("billing_agent", billing_agent_node)
    graph.add_node("technical_agent", technical_agent_node)
    graph.add_node("returns_agent", returns_agent_node)
    graph.add_node("general_agent", general_agent_node)
    graph.add_node("escalation", escalation_node)

    # Entry point
    graph.set_entry_point("memory")

    # Memory → Router
    graph.add_edge("memory", "router")

    # Router → Sub-agents (conditional)
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "billing_agent": "billing_agent",
            "technical_agent": "technical_agent",
            "returns_agent": "returns_agent",
            "general_agent": "general_agent",
        }
    )

    # Sub-agents → END or Escalation (conditional)
    for agent in ["billing_agent", "technical_agent", "returns_agent"]:
        graph.add_conditional_edges(
            agent,
            route_after_agent,
            {END: END, "escalation": "escalation"}
        )

    graph.add_edge("general_agent", END)
    graph.add_edge("escalation", END)

    return graph.compile()


# Singleton compiled graph
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


async def run_agent(session_id: str, user_message: str) -> dict:
    """Run the full agent pipeline for a message."""
    graph = get_graph()

    initial_state: AgentState = {
        "session_id": session_id,
        "user_message": user_message,
        "chat_history": [],
        "category": "",
        "current_agent": "",
        "agent_response": "",
        "resolved": False,
        "attempt_count": 0,
        "escalation_ticket": None,
        "nodes_fired": [],
        "tool_results": {},
    }

    result = await graph.ainvoke(initial_state)

    # Save to memory and DB
    mem.append_message(session_id, "user", user_message)
    mem.append_message(session_id, "assistant", result["agent_response"], result.get("current_agent"))
    db.save_message(session_id, "user", user_message)
    db.save_message(session_id, "assistant", result["agent_response"], result.get("current_agent"))

    return {
        "response": result["agent_response"],
        "category": result.get("category"),
        "agent": result.get("current_agent"),
        "nodes_fired": result.get("nodes_fired", []),
        "escalation_ticket": result.get("escalation_ticket"),
        "tool_results": result.get("tool_results", {}),
        "resolved": result.get("resolved", True),
    }
