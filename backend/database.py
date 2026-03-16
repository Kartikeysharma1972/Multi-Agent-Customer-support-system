"""
Database models and seed data for the Multi-Agent Customer Support System.
Uses SQLite via SQLAlchemy.
"""

import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path("support.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            plan TEXT NOT NULL,
            billing_status TEXT NOT NULL,
            last_invoice_date TEXT,
            last_invoice_amount REAL,
            next_billing_date TEXT,
            payment_method TEXT,
            account_created TEXT
        )
    """)

    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            customer_email TEXT NOT NULL,
            product TEXT NOT NULL,
            status TEXT NOT NULL,
            purchase_date TEXT NOT NULL,
            return_eligible INTEGER NOT NULL,
            return_deadline TEXT,
            amount REAL NOT NULL,
            tracking_number TEXT
        )
    """)

    # Escalation tickets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT UNIQUE NOT NULL,
            session_id TEXT NOT NULL,
            issue_type TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            priority TEXT DEFAULT 'medium',
            created_at TEXT NOT NULL,
            resolved_at TEXT,
            agent_notes TEXT
        )
    """)

    # Chat history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            agent_type TEXT,
            timestamp TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def seed_customers():
    """Seed 20 fake customer records."""
    customers = [
        ("Alice Johnson", "alice.johnson@email.com", "Pro", "active", 99.99),
        ("Bob Martinez", "bob.martinez@email.com", "Basic", "active", 29.99),
        ("Carol White", "carol.white@email.com", "Enterprise", "active", 299.99),
        ("David Lee", "david.lee@email.com", "Pro", "overdue", 99.99),
        ("Emma Davis", "emma.davis@email.com", "Basic", "active", 29.99),
        ("Frank Wilson", "frank.wilson@email.com", "Pro", "cancelled", 99.99),
        ("Grace Taylor", "grace.taylor@email.com", "Enterprise", "active", 299.99),
        ("Henry Brown", "henry.brown@email.com", "Basic", "active", 29.99),
        ("Isabella Anderson", "isabella.a@email.com", "Pro", "active", 99.99),
        ("James Thomas", "james.thomas@email.com", "Basic", "suspended", 29.99),
        ("Kate Jackson", "kate.jackson@email.com", "Enterprise", "active", 299.99),
        ("Liam Harris", "liam.harris@email.com", "Pro", "active", 99.99),
        ("Mia Lewis", "mia.lewis@email.com", "Basic", "active", 29.99),
        ("Noah Robinson", "noah.robinson@email.com", "Pro", "overdue", 99.99),
        ("Olivia Walker", "olivia.walker@email.com", "Enterprise", "active", 299.99),
        ("Paul Hall", "paul.hall@email.com", "Basic", "active", 29.99),
        ("Quinn Allen", "quinn.allen@email.com", "Pro", "active", 99.99),
        ("Rachel Young", "rachel.young@email.com", "Basic", "cancelled", 29.99),
        ("Sam King", "sam.king@email.com", "Enterprise", "active", 299.99),
        ("Tina Scott", "tina.scott@email.com", "Pro", "active", 99.99),
    ]

    payment_methods = ["Visa *4242", "Mastercard *8888", "PayPal", "Amex *3737", "Bank Transfer"]

    conn = get_connection()
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    base_date = datetime.now()

    for i, (name, email, plan, billing_status, amount) in enumerate(customers):
        last_invoice = base_date - timedelta(days=random.randint(1, 30))
        next_billing = base_date + timedelta(days=random.randint(1, 30))
        account_created = base_date - timedelta(days=random.randint(30, 730))

        cursor.execute("""
            INSERT INTO customers 
            (name, email, plan, billing_status, last_invoice_date, last_invoice_amount, 
             next_billing_date, payment_method, account_created)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, email, plan, billing_status,
            last_invoice.strftime("%Y-%m-%d"),
            amount,
            next_billing.strftime("%Y-%m-%d"),
            random.choice(payment_methods),
            account_created.strftime("%Y-%m-%d")
        ))

    conn.commit()
    conn.close()
    print("[+] Seeded 20 customer records")


def seed_orders():
    """Seed 20 fake order records."""
    products = [
        "ProSuite Software License",
        "CloudSync Annual Plan",
        "DataVault Storage 1TB",
        "TeamCollab Business Pack",
        "SecureVPN Premium",
        "AnalyticsPro Dashboard",
        "AutoBackup Enterprise",
        "DevTools IDE Plugin",
        "ReportBuilder Suite",
        "APIManager Professional",
    ]

    statuses = ["delivered", "shipped", "processing", "cancelled", "returned"]

    emails = [
        "alice.johnson@email.com", "bob.martinez@email.com", "carol.white@email.com",
        "david.lee@email.com", "emma.davis@email.com", "frank.wilson@email.com",
        "grace.taylor@email.com", "henry.brown@email.com", "isabella.a@email.com",
        "james.thomas@email.com", "kate.jackson@email.com", "liam.harris@email.com",
        "mia.lewis@email.com", "noah.robinson@email.com", "olivia.walker@email.com",
        "paul.hall@email.com", "quinn.allen@email.com", "rachel.young@email.com",
        "sam.king@email.com", "tina.scott@email.com",
    ]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM orders")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    base_date = datetime.now()

    for i in range(20):
        purchase_date = base_date - timedelta(days=random.randint(1, 90))
        days_since_purchase = (base_date - purchase_date).days
        return_eligible = 1 if days_since_purchase <= 30 else 0
        return_deadline = (purchase_date + timedelta(days=30)).strftime("%Y-%m-%d")

        cursor.execute("""
            INSERT INTO orders 
            (order_id, customer_email, product, status, purchase_date, 
             return_eligible, return_deadline, amount, tracking_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"ORD-{10000 + i}",
            emails[i],
            random.choice(products),
            random.choice(statuses),
            purchase_date.strftime("%Y-%m-%d"),
            return_eligible,
            return_deadline,
            round(random.uniform(29.99, 499.99), 2),
            f"TRK{random.randint(100000000, 999999999)}" if random.random() > 0.3 else None
        ))

    conn.commit()
    conn.close()
    print("[+] Seeded 20 order records")


def lookup_customer(email: str) -> dict | None:
    """Look up customer by email."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def lookup_order(order_id: str) -> dict | None:
    """Look up order by order ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def create_ticket(session_id: str, issue_type: str, description: str, priority: str = "medium") -> str:
    """Create an escalation ticket."""
    import uuid
    ticket_id = f"TKT-{str(uuid.uuid4())[:8].upper()}"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tickets (ticket_id, session_id, issue_type, description, priority, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (ticket_id, session_id, issue_type, description, priority, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return ticket_id


def get_ticket(ticket_id: str) -> dict | None:
    """Get ticket by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def save_message(session_id: str, role: str, content: str, agent_type: str = None):
    """Save a chat message."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_history (session_id, role, content, agent_type, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, role, content, agent_type, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_history(session_id: str) -> list:
    """Get full chat history for a session."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, content, agent_type, timestamp 
        FROM chat_history 
        WHERE session_id = ? 
        ORDER BY id ASC
    """, (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
