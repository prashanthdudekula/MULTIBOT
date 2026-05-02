import { useState, useEffect, useRef } from 'react';
import './index.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const MERCHANT_ID = "m_001";
  const TRIGGER_ID = `tr_perf_${Date.now()}`;
  const CONV_ID = `conv_${MERCHANT_ID}_${TRIGGER_ID}`;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    const initVera = async () => {
      try {
        const nowIso = new Date().toISOString();
        
        await fetch('/v1/context', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            scope: 'category',
            context_id: 'dentists',
            version: Math.floor(Date.now() / 1000),
            payload: { slug: "dentists", voice: { tone: "professional" } },
            delivered_at: nowIso
          })
        });

        await fetch('/v1/context', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            scope: 'merchant',
            context_id: MERCHANT_ID,
            version: Math.floor(Date.now() / 1000),
            payload: { category_slug: "dentists", identity: { name: "Dr. Smith" }, language_pref: "en" },
            delivered_at: nowIso
          })
        });

        await fetch('/v1/context', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            scope: 'trigger',
            context_id: TRIGGER_ID,
            version: Math.floor(Date.now() / 1000),
            payload: {
              kind: "perf_spike",
              merchant_id: MERCHANT_ID,
              payload: { delta_pct: 45, metric: "profile views", reason: "weekend surge" }
            },
            delivered_at: nowIso
          })
        });

        setIsLoading(true);
        const res = await fetch('/v1/tick', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            now: nowIso,
            available_triggers: [TRIGGER_ID]
          })
        });
        
        const data = await res.json();
        if (data.actions && data.actions.length > 0) {
          setMessages([{ role: 'vera', text: data.actions[0].body }]);
        }
      } catch (err) {
        console.error("Failed to init Vera:", err);
      } finally {
        setIsLoading(false);
      }
    };

    initVera();
  }, []);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userText = input.trim();
    setMessages(prev => [...prev, { role: 'user', text: userText }]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await fetch('/v1/reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: CONV_ID,
          merchant_id: MERCHANT_ID,
          message: userText,
          turn_number: messages.length + 1,
          from_role: 'merchant',
          received_at: new Date().toISOString()
        })
      });
      
      const data = await res.json();
      if (data.action === "send") {
        setMessages(prev => [...prev, { role: 'vera', text: data.body }]);
      } else if (data.action === "end") {
        setMessages(prev => [...prev, { role: 'vera', text: "[Conversation ended by Vera]" }]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Ambient Animated Orbs */}
      <div className="ambient-bg">
        <div className="orb-1"></div>
        <div className="orb-2"></div>
      </div>

      <div className="app-wrapper">
        
        {/* Sidebar Information */}
        <aside className="info-sidebar">
          <div>
            <h1 className="hero-title">Meet <span className="gradient-text">Vera</span></h1>
            <p className="hero-subtitle">The intelligent growth engine for MagicPin merchants, powered by Groq Llama-3.3.</p>
          </div>

          <div className="info-card">
            <span className="card-number">01. Context Aware</span>
            <h3>Dynamic Framing</h3>
            <p>Vera adapts her tone perfectly depending on the category and merchant performance signals.</p>
          </div>

          <div className="info-card">
            <span className="card-number">02. Data Driven</span>
            <h3>Performance Spikes</h3>
            <p>She analyzes weekend surges and dips to suggest actionable campaigns instantly.</p>
          </div>

          <div className="info-card">
            <span className="card-number">03. Deterministic</span>
            <h3>Anti-Spam Logic</h3>
            <p>Built with strict engagement validators. Vera never loops, hallucinates clinical advice, or spams merchants.</p>
          </div>
        </aside>

        {/* Main Glassmorphic Chat */}
        <main className="chat-glass-container">
          <header className="chat-header">
            <div className="chat-header-left">
              <div className="avatar">V</div>
              <h2>Vera Assistant</h2>
            </div>
            <div className="status-badge">
              <div className="status-dot"></div>
              <span>System Online</span>
            </div>
          </header>

          <div className="chat-messages">
            {messages.length === 0 && !isLoading && (
              <div style={{ textAlign: 'center', color: 'var(--text-secondary)', marginTop: '2rem' }}>
                Establishing neural link...
              </div>
            )}
            
            {messages.map((msg, idx) => (
              <div key={idx} className={`message-wrapper ${msg.role === 'vera' ? 'message-vera-wrapper' : 'message-user-wrapper'}`}>
                <div className={`message-bubble ${msg.role === 'vera' ? 'message-vera' : 'message-user'}`}>
                  {msg.text}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="message-wrapper message-vera-wrapper">
                <div className="typing-indicator">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form className="chat-input-area" onSubmit={handleSend}>
            <div className="input-wrapper">
              <input 
                type="text" 
                className="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Message Vera..."
                disabled={isLoading}
              />
            </div>
            <button type="submit" className="send-btn" disabled={isLoading || !input.trim()}>
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </form>
        </main>
        
      </div>
    </>
  );
}

export default App;
