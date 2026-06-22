import { useState, useRef, useEffect } from 'react'
import ChatBubble from '../components/ChatBubble.jsx'
import TriageCard from '../components/TriageCard.jsx'

export default function Home({onBack}) {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hi, I am SehatSaathi. Please tell me what symptom you are experiencing.', source: null, urgency: null, is_final: false },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  async function handleSend() {
    if (!input.trim() || loading) return
    const userMsg = { role: 'user', content: input, source: null, urgency: null, is_final: false }
    const updated = [...messages, userMsg]
    setMessages(updated)
    setInput('')
    setLoading(true)
    try {
      const res = await fetch('/api/triage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation: updated.map(m => ({ role: m.role, content: m.content })), language: 'en' }),
      })
      const data = await res.json()
      setMessages([...updated, { role: 'assistant', content: data.reply, source: data.source, urgency: data.urgency, is_final: data.is_final }])
    } catch {
      setMessages([...updated, { role: 'assistant', content: 'Something went wrong. Please try again.', source: null, urgency: null, is_final: false }])
    }
    setLoading(false)
  }

return (
  <div style={{ width: '100%', height: '100vh', display: 'flex', flexDirection: 'column', background: '#FDF6EC' }}>
    
 {/* replace your existing header div with this */}
<div style={{ background: '#1B3A4B', padding: '14px 20px', display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
  <button
    onClick={onBack}
    style={{ background: 'transparent', border: 'none', color: 'rgba(245,244,240,0.6)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontFamily: 'DM Sans, sans-serif', padding: 0 }}
    aria-label="Back to home"
  >
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
    </svg>
    Back
  </button>
  <span style={{ fontFamily: 'DM Serif Display, serif', color: '#F5F4F0', fontSize: 18, fontWeight: 400 }}>SehatSaathi</span>
  <span style={{ fontFamily: 'DM Sans, sans-serif', color: '#7A9BB0', fontSize: 12, marginLeft: 'auto', letterSpacing: '0.05em' }}>AI Health Triage</span>
</div>

    {/* Chat area - centred column, full height */}
    <div style={{ flex: 1, overflowY: 'auto', background: '#FDF6EC', padding: '20px 0' }}>
      <div style={{ maxWidth: 680, margin: '0 auto', padding: '0 20px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {messages.map((m, i) => (
          <div key={i}>
            <ChatBubble role={m.role} content={m.content} source={m.source} />
            {m.is_final && <TriageCard urgency={m.urgency} source={m.source} />}
          </div>
        ))}
        {loading && (
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#0D7377', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 700, flexShrink: 0 }}>S</div>
            <div style={{ background: '#ffffff', border: '1px solid #dde9e9', borderRadius: 18, borderBottomLeftRadius: 4, padding: '12px 16px', display: 'flex', gap: 5, alignItems: 'center' }}>
              {[0, 0.2, 0.4].map((d, i) => (
                <span key={i} style={{ width: 7, height: 7, background: '#6b9e9e', borderRadius: '50%', display: 'inline-block', animation: `bounce 1.2s ${d}s infinite ease-in-out` }} />
              ))}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>

    {/* Input bar - full width, centred content */}
    <div style={{ background: '#ffffff', borderTop: '1px solid #dde9e9', padding: '14px 20px', flexShrink: 0 }}>
      <div style={{ maxWidth: 680, margin: '0 auto', display: 'flex', gap: 10 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="Describe your symptom…"
          style={{ flex: 1, border: '1.5px solid #c5d8d8', borderRadius: 28, padding: '11px 20px', fontSize: 14, background: '#FDF6EC', color: '#1a2e2e', fontFamily: 'Inter, sans-serif', outline: 'none' }}
        />
        <button
          onClick={handleSend}
          disabled={loading}
          style={{ background: '#0D7377', border: 'none', borderRadius: '50%', width: 44, height: 44, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: loading ? 'default' : 'pointer', opacity: loading ? 0.5 : 1, flexShrink: 0 }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </div>
    </div>

    <style>{`
      @keyframes bounce { 0%,80%,100%{transform:translateY(0)} 40%{transform:translateY(-6px)} }
      * { color-scheme: light !important; }
      ::-webkit-scrollbar { width: 5px; }
      ::-webkit-scrollbar-track { background: transparent; }
      ::-webkit-scrollbar-thumb { background: #c5d8d8; border-radius: 4px; }
    `}</style>
  </div>
)
}