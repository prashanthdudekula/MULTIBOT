import { useState, useEffect, useRef } from 'react';
import './index.css';

const CATEGORY_ICONS = {
  dentists: '🦷',
  gyms: '💪',
  pharmacies: '💊',
  restaurants: '🍽️',
  salons: '💇',
};

const CATEGORY_COLORS = {
  dentists: '#4fc3f7',
  gyms: '#ff7043',
  pharmacies: '#66bb6a',
  restaurants: '#ffa726',
  salons: '#ab47bc',
};

function App() {
  const [merchants, setMerchants] = useState([]);
  const [selectedMerchant, setSelectedMerchant] = useState(null);
  const [filterCategory, setFilterCategory] = useState('all');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [convId, setConvId] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => { scrollToBottom(); }, [messages, isLoading]);

  // Fetch merchants on mount
  useEffect(() => {
    fetch('/v1/merchants')
      .then(r => r.json())
      .then(data => setMerchants(data.merchants || []))
      .catch(err => console.error("Failed to fetch merchants:", err));
  }, []);

  // Start conversation when merchant is selected
  const selectMerchant = async (merchant) => {
    setSelectedMerchant(merchant);
    setMessages([]);
    setIsLoading(true);

    const cid = `conv_${merchant.merchant_id}_${Date.now()}`;
    setConvId(cid);

    // Send a greeting to get Vera started
    try {
      const res = await fetch('/v1/reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: cid,
          merchant_id: merchant.merchant_id,
          message: `Hi, I'm ${merchant.owner} from ${merchant.name}. What can you help me with?`,
          turn_number: 1,
          from_role: 'merchant',
          received_at: new Date().toISOString(),
        }),
      });
      const data = await res.json();
      setMessages([
        { role: 'user', text: `Hi, I'm ${merchant.owner} from ${merchant.name}. What can you help me with?` },
        ...(data.action === 'send' ? [{ role: 'vera', text: data.body }] : []),
      ]);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !selectedMerchant) return;

    const userText = input.trim();
    setMessages(prev => [...prev, { role: 'user', text: userText }]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await fetch('/v1/reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: convId,
          merchant_id: selectedMerchant.merchant_id,
          message: userText,
          turn_number: messages.length + 1,
          from_role: 'merchant',
          received_at: new Date().toISOString(),
        }),
      });
      const data = await res.json();
      if (data.action === "send") {
        setMessages(prev => [...prev, { role: 'vera', text: data.body }]);
      } else if (data.action === "end") {
        setMessages(prev => [...prev, { role: 'vera', text: "Thanks for chatting! Feel free to reach out anytime. 👋" }]);
      } else if (data.action === "wait") {
        setMessages(prev => [...prev, { role: 'vera', text: "No worries, I'll check back later! ⏳" }]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const goBack = () => {
    setSelectedMerchant(null);
    setMessages([]);
    setConvId('');
  };

  const filteredMerchants = filterCategory === 'all'
    ? merchants
    : merchants.filter(m => m.category === filterCategory);

  const categories = ['all', ...new Set(merchants.map(m => m.category))];

  // ---- MERCHANT LIST VIEW ----
  if (!selectedMerchant) {
    return (
      <>
        <div className="ambient-bg">
          <div className="orb-1"></div>
          <div className="orb-2"></div>
        </div>
        <div className="app-wrapper select-view">
          <div className="select-container">
            <div className="select-header">
              <h1 className="hero-title">Meet <span className="gradient-text">Vera</span></h1>
              <p className="hero-subtitle">The intelligent growth engine for MagicPin merchants. Select a merchant below to start chatting.</p>
            </div>

            {/* Category Filter Pills */}
            <div className="category-pills">
              {categories.map(cat => (
                <button
                  key={cat}
                  className={`pill ${filterCategory === cat ? 'pill-active' : ''}`}
                  onClick={() => setFilterCategory(cat)}
                >
                  {cat === 'all' ? '🏪 All' : `${CATEGORY_ICONS[cat] || '📦'} ${cat.charAt(0).toUpperCase() + cat.slice(1)}`}
                </button>
              ))}
            </div>

            {/* Merchant Cards Grid */}
            <div className="merchant-grid">
              {filteredMerchants.map(m => (
                <div
                  key={m.merchant_id}
                  className="merchant-card"
                  onClick={() => selectMerchant(m)}
                  style={{ '--accent': CATEGORY_COLORS[m.category] || '#888' }}
                >
                  <div className="mc-header">
                    <span className="mc-icon">{CATEGORY_ICONS[m.category] || '📦'}</span>
                    <span className="mc-category" style={{ color: CATEGORY_COLORS[m.category] }}>
                      {m.category}
                    </span>
                  </div>
                  <h3 className="mc-name">{m.name}</h3>
                  <p className="mc-owner">Owner: {m.owner}</p>
                  <div className="mc-stats">
                    <span>👀 {m.performance.views_last_30d || 0} views</span>
                    <span>📈 CTR {((m.performance.ctr || 0) * 100).toFixed(1)}%</span>
                  </div>
                  {m.offers.length > 0 && (
                    <div className="mc-offers">
                      {m.offers.slice(0, 2).map((o, i) => (
                        <span key={i} className="mc-offer-tag">{o}</span>
                      ))}
                    </div>
                  )}
                  {m.signals.length > 0 && (
                    <div className="mc-signals">
                      {m.signals.slice(0, 2).map((s, i) => (
                        <span key={i} className="mc-signal">{s.replace(/_/g, ' ')}</span>
                      ))}
                    </div>
                  )}
                  <div className="mc-lang">{m.language === 'hi' ? '🇮🇳 Hindi' : '🌐 English'}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </>
    );
  }

  // ---- CHAT VIEW ----
  return (
    <>
      <div className="ambient-bg">
        <div className="orb-1"></div>
        <div className="orb-2"></div>
      </div>
      <div className="app-wrapper">

        {/* Sidebar with merchant info */}
        <aside className="info-sidebar">
          <div>
            <button className="back-btn" onClick={goBack}>← All Merchants</button>
            <h1 className="hero-title">
              <span className="gradient-text">{selectedMerchant.name}</span>
            </h1>
            <p className="hero-subtitle">
              {CATEGORY_ICONS[selectedMerchant.category]} {selectedMerchant.category.charAt(0).toUpperCase() + selectedMerchant.category.slice(1)} · Owner: {selectedMerchant.owner}
            </p>
          </div>

          <div className="info-card">
            <span className="card-number">Performance</span>
            <h3>📊 Stats</h3>
            <p>Views: {selectedMerchant.performance.views_last_30d || 'N/A'}</p>
            <p>CTR: {((selectedMerchant.performance.ctr || 0) * 100).toFixed(1)}%</p>
            {selectedMerchant.performance.bookings_last_30d && (
              <p>Bookings: {selectedMerchant.performance.bookings_last_30d}</p>
            )}
            {selectedMerchant.performance.orders_last_30d && (
              <p>Orders: {selectedMerchant.performance.orders_last_30d}</p>
            )}
          </div>

          {selectedMerchant.offers.length > 0 && (
            <div className="info-card">
              <span className="card-number">Active Offers</span>
              <h3>🏷️ Deals</h3>
              {selectedMerchant.offers.map((o, i) => (
                <p key={i}>• {o}</p>
              ))}
            </div>
          )}

          {selectedMerchant.signals.length > 0 && (
            <div className="info-card">
              <span className="card-number">Signals</span>
              <h3>📡 Insights</h3>
              {selectedMerchant.signals.map((s, i) => (
                <p key={i}>• {s.replace(/_/g, ' ')}</p>
              ))}
            </div>
          )}
        </aside>

        {/* Chat */}
        <main className="chat-glass-container">
          <header className="chat-header">
            <div className="chat-header-left">
              <div className="avatar">V</div>
              <h2>Vera — {selectedMerchant.name}</h2>
            </div>
            <div className="status-badge">
              <div className="status-dot"></div>
              <span>Online</span>
            </div>
          </header>

          <div className="chat-messages">
            {messages.length === 0 && !isLoading && (
              <div style={{ textAlign: 'center', color: 'var(--text-secondary)', marginTop: '2rem' }}>
                Starting conversation...
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
                placeholder={`Message Vera as ${selectedMerchant.owner}...`}
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
