import React, { useState, useEffect, useRef, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import './App.css';

// ─── Constants ───────────────────────────────
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const AGENT_COLORS = {
  billing_agent:   { bg: '#ecfdf5', border: '#10b981', text: '#047857', label: 'Billing Agent',   icon: '💳' },
  technical_agent: { bg: '#eff6ff', border: '#3b82f6', text: '#1d4ed8', label: 'Technical Agent', icon: '⚙️' },
  returns_agent:   { bg: '#f5f3ff', border: '#8b5cf6', text: '#6d28d9', label: 'Returns Agent',   icon: '📦' },
  general_agent:   { bg: '#fffbeb', border: '#f59e0b', text: '#b45309', label: 'General Agent',   icon: '💬' },
  escalation:      { bg: '#fef2f2', border: '#ef4444', text: '#dc2626', label: 'Escalated',       icon: '🚨' },
};

const NODE_LABELS = {
  memory:          { icon: '🧠', label: 'Memory Node',     color: '#6b7280' },
  router:          { icon: '🔀', label: 'Router Agent',    color: '#8b5cf6' },
  billing_agent:   { icon: '💳', label: 'Billing Agent',   color: '#10b981' },
  technical_agent: { icon: '⚙️', label: 'Technical Agent', color: '#3b82f6' },
  returns_agent:   { icon: '📦', label: 'Returns Agent',   color: '#8b5cf6' },
  general_agent:   { icon: '💬', label: 'General Agent',   color: '#f59e0b' },
  escalation:      { icon: '🚨', label: 'Escalation',      color: '#ef4444' },
};

const SAMPLE_PROMPTS = [
  "My invoice shows a wrong charge",
  "ProSuite keeps crashing on launch",
  "I want to return order ORD-10005",
  "How do I reset my password?",
  "What's included in the Pro plan?",
  "I can't connect to the server",
];

// ─── Hooks ───────────────────────────────────

function useSSE(sessionId) {
  const [events, setEvents] = useState([]);
  const esRef = useRef(null);

  const connect = useCallback(() => {
    if (esRef.current) esRef.current.close();
    const es = new EventSource(`${API_BASE}/stream/${sessionId}`);
    esRef.current = es;

    const handleEvent = (type) => (e) => {
      try {
        const data = JSON.parse(e.data);
        setEvents(prev => [...prev, { type, data, ts: Date.now() }]);
      } catch {}
    };

    ['node_start', 'node_complete', 'escalation', 'response_complete', 'error', 'heartbeat', 'connected']
      .forEach(t => es.addEventListener(t, handleEvent(t)));

    return () => es.close();
  }, [sessionId]);

  useEffect(() => {
    const cleanup = connect();
    return cleanup;
  }, [connect]);

  const clearEvents = () => setEvents([]);
  return { events, clearEvents };
}

// ─── Auth Components ─────────────────────────

function LoginPage({ onLogin, onSwitchToSignup }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError('Please fill in all fields.');
      return;
    }
    setError('');
    setLoading(true);

    try {
      const resp = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        setError(data.detail || 'Login failed.');
      } else {
        localStorage.setItem('user', JSON.stringify(data.user));
        onLogin(data.user);
      }
    } catch {
      setError('Unable to connect to server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <div className="auth-logo">
          <div className="auth-logo-icon">⬡</div>
          <span className="auth-logo-text">SupportAI</span>
        </div>
        <p className="auth-subtitle">Sign in to access the support dashboard</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && <div className="auth-error">{error}</div>}
          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              className="form-input"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoFocus
            />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              className="form-input"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <button className="auth-btn" type="submit" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="auth-switch">
          Don't have an account?{' '}
          <button className="auth-switch-link" onClick={onSwitchToSignup}>
            Create one
          </button>
        </div>
      </div>
    </div>
  );
}

function SignupPage({ onSignup, onSwitchToLogin }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !password || !confirm) {
      setError('Please fill in all fields.');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }
    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }
    setError('');
    setLoading(true);

    try {
      const resp = await fetch(`${API_BASE}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim(), email: email.trim(), password }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        setError(data.detail || 'Signup failed.');
      } else {
        localStorage.setItem('user', JSON.stringify(data.user));
        onSignup(data.user);
      }
    } catch {
      setError('Unable to connect to server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <div className="auth-logo">
          <div className="auth-logo-icon">⬡</div>
          <span className="auth-logo-text">SupportAI</span>
        </div>
        <p className="auth-subtitle">Create an account to get started</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && <div className="auth-error">{error}</div>}
          <div className="form-group">
            <label className="form-label">Full Name</label>
            <input
              className="form-input"
              type="text"
              placeholder="John Doe"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
          </div>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              className="form-input"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              className="form-input"
              type="password"
              placeholder="Min 6 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Confirm Password</label>
            <input
              className="form-input"
              type="password"
              placeholder="Re-enter your password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
            />
          </div>
          <button className="auth-btn" type="submit" disabled={loading}>
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <div className="auth-switch">
          Already have an account?{' '}
          <button className="auth-switch-link" onClick={onSwitchToLogin}>
            Sign in
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── UI Components ───────────────────────────

function ThinkingDots() {
  return (
    <div className="thinking-dots">
      <span></span><span></span><span></span>
    </div>
  );
}

function AgentBadge({ agentKey }) {
  const cfg = AGENT_COLORS[agentKey];
  if (!cfg) return null;
  return (
    <span className="agent-badge" style={{ background: cfg.bg, border: `1.5px solid ${cfg.border}`, color: cfg.text }}>
      {cfg.icon} {cfg.label}
    </span>
  );
}

function NodePill({ nodeKey, active }) {
  const cfg = NODE_LABELS[nodeKey] || { icon: '•', label: nodeKey, color: '#6b7280' };
  return (
    <div className={`node-pill ${active ? 'active' : ''}`} style={{ '--node-color': cfg.color }}>
      <span className="node-icon">{cfg.icon}</span>
      <span className="node-label">{cfg.label}</span>
      {active && <span className="node-pulse"></span>}
    </div>
  );
}

function PipelinePanel({ nodesFired, activeNode }) {
  const allNodes = ['memory', 'router', 'billing_agent', 'technical_agent', 'returns_agent', 'general_agent', 'escalation'];
  const firedSet = new Set(nodesFired);

  return (
    <div className="pipeline-panel">
      <div className="panel-header">
        <span className="panel-icon">⚡</span>
        <span>Agent Pipeline</span>
      </div>
      <div className="pipeline-flow">
        {allNodes.map((node, i) => (
          <React.Fragment key={node}>
            <NodePill
              nodeKey={node}
              active={firedSet.has(node) || activeNode === node}
            />
            {i < allNodes.length - 1 && i !== 2 && (
              <div className={`pipeline-arrow ${firedSet.has(node) ? 'fired' : ''}`}>›</div>
            )}
            {i === 2 && <div className="pipeline-branch">or</div>}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

function EscalationBanner({ ticketId, onDismiss }) {
  return (
    <div className="escalation-banner">
      <div className="escalation-icon">🚨</div>
      <div className="escalation-content">
        <div className="escalation-title">Issue Escalated to Human Support</div>
        <div className="escalation-ticket">
          Ticket ID: <strong>{ticketId}</strong>
          <span className="escalation-eta">• Response within 24 hours</span>
        </div>
      </div>
      <button className="escalation-dismiss" onClick={onDismiss}>✕</button>
    </div>
  );
}

function MessageBubble({ message, userInitial }) {
  const isUser = message.role === 'user';
  const agent = message.agent;

  const formatContent = (text) => {
    return text.split('\n').map((line, i) => (
      <React.Fragment key={i}>
        {line.replace(/\*\*(.*?)\*\*/g, (_, m) => m)}
        {i < text.split('\n').length - 1 && <br />}
      </React.Fragment>
    ));
  };

  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`}>
      {!isUser && (
        <div className="avatar assistant-avatar">
          {agent ? (AGENT_COLORS[agent]?.icon || '🤖') : '🤖'}
        </div>
      )}
      <div className="message-content">
        {!isUser && agent && (
          <div className="message-meta">
            <AgentBadge agentKey={agent} />
          </div>
        )}
        <div className={`bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}`}>
          {formatContent(message.content)}
        </div>
        <div className="message-time">
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
      {isUser && <div className="avatar user-avatar">{userInitial}</div>}
    </div>
  );
}

function Sidebar({ sessionId, currentAgent, onNewSession, sampleData, user, onLogout, isOpen, onClose }) {
  const agentCfg = currentAgent ? AGENT_COLORS[currentAgent] : null;

  return (
    <>
      <div className={`sidebar-overlay ${isOpen ? 'open' : ''}`} onClick={onClose}></div>
      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="logo">
            <div className="logo-icon">⬡</div>
            <span className="logo-text">SupportAI</span>
          </div>
          <div className="logo-sub">Multi-Agent Support System</div>
        </div>

        <div className="sidebar-section">
          <div className="section-label">Active Session</div>
          <div className="session-card">
            <div className="session-id">{sessionId.slice(0, 8)}...</div>
            <div className="session-status">
              <span className="status-dot"></span>
              <span>Active</span>
            </div>
          </div>
          <button className="new-session-btn" onClick={onNewSession}>
            + New Session
          </button>
        </div>

        <div className="sidebar-section">
          <div className="section-label">Current Agent</div>
          {agentCfg ? (
            <div className="agent-card" style={{ borderColor: agentCfg.border }}>
              <div className="agent-card-icon">{agentCfg.icon}</div>
              <div className="agent-card-name" style={{ color: agentCfg.text }}>{agentCfg.label}</div>
            </div>
          ) : (
            <div className="agent-card idle">
              <div className="agent-card-icon">💤</div>
              <div className="agent-card-name">Awaiting query</div>
            </div>
          )}
        </div>

        <div className="sidebar-section">
          <div className="section-label">Agent Roster</div>
          {Object.entries(AGENT_COLORS).slice(0, 4).map(([key, cfg]) => (
            <div key={key} className={`roster-item ${currentAgent === key ? 'active' : ''}`}>
              <span>{cfg.icon}</span>
              <span>{cfg.label}</span>
            </div>
          ))}
        </div>

        {sampleData && (
          <div className="sidebar-section">
            <div className="section-label">Sample Data</div>
            <div className="sample-hint">Try: <em>{sampleData.email}</em></div>
            <div className="sample-hint">Try: <em>{sampleData.orderId}</em></div>
          </div>
        )}

        <div className="sidebar-footer">
          <div className="user-section">
            <div className="user-avatar-sidebar">
              {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="user-info">
              <div className="user-name">{user?.name || 'User'}</div>
              <div className="user-email">{user?.email || ''}</div>
            </div>
            <button className="logout-btn" onClick={onLogout} title="Sign out">
              ↗
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}

// ─── Main App ────────────────────────────────

export default function App() {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [authPage, setAuthPage] = useState('login');
  const [sessionId, setSessionId] = useState(() => uuidv4());
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [currentAgent, setCurrentAgent] = useState(null);
  const [nodesFired, setNodesFired] = useState([]);
  const [activeNode, setActiveNode] = useState(null);
  const [escalationTicket, setEscalationTicket] = useState(null);
  const [sampleData, setSampleData] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);
  const { events, clearEvents } = useSSE(sessionId);

  const userInitial = user?.name ? user.name.charAt(0).toUpperCase() : 'U';

  // Load sample data for sidebar hints
  useEffect(() => {
    if (!user) return;
    fetch(`${API_BASE}/sessions/sample-data`)
      .then(r => r.json())
      .then(d => setSampleData({
        email: d.sample_customers?.[0]?.email,
        orderId: d.sample_orders?.[0]?.order_id,
      }))
      .catch(() => {});
  }, [user]);

  // Process SSE events
  useEffect(() => {
    events.forEach(ev => {
      if (ev.type === 'node_start') {
        setActiveNode(ev.data.node);
      } else if (ev.type === 'node_complete') {
        setNodesFired(prev => [...new Set([...prev, ev.data.node])]);
        setActiveNode(null);
      }
    });
  }, [events]);

  // Scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleSignup = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('user');
    setMessages([]);
    setSessionId(uuidv4());
    setCurrentAgent(null);
    setNodesFired([]);
    setEscalationTicket(null);
    setSidebarOpen(false);
  };

  const sendMessage = async (text) => {
    const userText = (text || input).trim();
    if (!userText || isThinking) return;

    setInput('');
    setIsThinking(true);
    setNodesFired([]);
    setActiveNode('memory');
    clearEvents();

    const userMsg = {
      role: 'user',
      content: userText,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);

    try {
      const resp = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, message: userText }),
      });

      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      const assistantMsg = {
        role: 'assistant',
        content: data.response,
        agent: data.agent,
        category: data.category,
        nodesFired: data.nodes_fired,
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, assistantMsg]);
      setCurrentAgent(data.agent);
      setNodesFired(data.nodes_fired || []);

      if (data.escalation_ticket) {
        setEscalationTicket(data.escalation_ticket);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Connection error: ${err.message}. Please ensure the backend is running.`,
        agent: null,
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setIsThinking(false);
      setActiveNode(null);
      inputRef.current?.focus();
    }
  };

  const handleNewSession = () => {
    setSessionId(uuidv4());
    setMessages([]);
    setCurrentAgent(null);
    setNodesFired([]);
    setEscalationTicket(null);
    setInput('');
    setSidebarOpen(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // ─── Auth screens ─────────────────────────
  if (!user) {
    if (authPage === 'login') {
      return (
        <LoginPage
          onLogin={handleLogin}
          onSwitchToSignup={() => setAuthPage('signup')}
        />
      );
    }
    return (
      <SignupPage
        onSignup={handleSignup}
        onSwitchToLogin={() => setAuthPage('login')}
      />
    );
  }

  // ─── Main app ─────────────────────────────
  const isEmpty = messages.length === 0;

  return (
    <div className="app">
      <Sidebar
        sessionId={sessionId}
        currentAgent={currentAgent}
        onNewSession={handleNewSession}
        sampleData={sampleData}
        user={user}
        onLogout={handleLogout}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="main">
        {/* Mobile header */}
        <div className="mobile-header">
          <div className="mobile-logo">
            <div className="mobile-logo-icon">⬡</div>
            <span className="mobile-logo-text">SupportAI</span>
          </div>
          <button className="mobile-menu-btn" onClick={() => setSidebarOpen(true)}>
            ☰
          </button>
        </div>

        {escalationTicket && (
          <EscalationBanner
            ticketId={escalationTicket}
            onDismiss={() => setEscalationTicket(null)}
          />
        )}

        <div className="chat-area">
          {isEmpty ? (
            <div className="empty-state">
              <div className="empty-icon-container">
                <div className="empty-icon">⬡</div>
              </div>
              <h2 className="empty-title">How can we help you today?</h2>
              <p className="empty-sub">
                Ask anything about billing, technical issues, returns, or general inquiries.
                Our AI agents will route your request to the right specialist.
              </p>
              <div className="prompt-grid">
                {SAMPLE_PROMPTS.map((p, i) => (
                  <button key={i} className="prompt-chip" onClick={() => sendMessage(p)}>
                    {p}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="messages">
              {messages.map((msg, i) => (
                <MessageBubble key={i} message={msg} userInitial={userInitial} />
              ))}
              {isThinking && (
                <div className="message-row assistant">
                  <div className="avatar assistant-avatar">🤖</div>
                  <div className="message-content">
                    <div className="bubble assistant-bubble thinking-bubble">
                      <ThinkingDots />
                      <span className="thinking-label">
                        {activeNode ? (NODE_LABELS[activeNode]?.label || 'Processing') : 'Thinking'}...
                      </span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          )}
        </div>

        <PipelinePanel nodesFired={nodesFired} activeNode={activeNode} />

        <div className="input-area">
          <div className="input-wrapper">
            <textarea
              ref={inputRef}
              className="chat-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Describe your issue... (Enter to send)"
              rows={1}
              disabled={isThinking}
            />
            <button
              className={`send-btn ${isThinking || !input.trim() ? 'disabled' : ''}`}
              onClick={() => sendMessage()}
              disabled={isThinking || !input.trim()}
            >
              {isThinking ? <ThinkingDots /> : '↑'}
            </button>
          </div>
          <div className="input-hint">
            Press Enter to send · Shift+Enter for new line
          </div>
        </div>
      </main>
    </div>
  );
}
