import { useState, useRef, useEffect } from 'react'
import ChatBubble from '../components/ChatBubble.jsx'
import TriageCard from '../components/TriageCard.jsx'

const API_URL = '/api/triage'

export default function Home() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hi, I am SehatSaathi. Please tell me what symptom you are experiencing.' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [lastResult, setLastResult] = useState(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend() {
    if (!input.trim()) return
    const userMessage = { role: 'user', content: input }
    const updated = [...messages, userMessage]
    setMessages(updated)
    setInput('')
    setLoading(true)
    setLastResult(null)

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation: updated, language: 'en' }),
      })
      if (!res.ok) throw new Error(`Request failed: ${res.status}`)
      const data = await res.json()

      setMessages([...updated, { role: 'assistant', content: data.reply }])
      if (data.is_final) {
        setLastResult({ urgency: data.urgency, source: data.source })
      }
    } catch (err) {
      setMessages([...updated, { role: 'assistant', content: 'Something went wrong. Please try again.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', maxWidth: 480, margin: '0 auto' }}>
      <div style={{ padding: 12, borderBottom: '1px solid #e2e8f0', fontWeight: 600 }}>SehatSaathi</div>
      <div style={{ flex: 1, overflowY: 'auto', padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {messages.map((m, i) => <ChatBubble key={i} role={m.role} content={m.content} />)}
        {loading && <ChatBubble role="assistant" content="..." />}
        {lastResult && <TriageCard urgency={lastResult.urgency} source={lastResult.source} />}
        <div ref={bottomRef} />
      </div>
      <div style={{ display: 'flex', gap: 8, padding: 12, borderTop: '1px solid #e2e8f0' }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Describe your symptom..."
          style={{ flex: 1, padding: 8, borderRadius: 8, border: '1px solid #cbd5e1' }}
        />
        <button onClick={handleSend} disabled={loading} style={{ padding: '8px 16px', borderRadius: 8, border: 'none', background: '#2563eb', color: 'white' }}>
          Send
        </button>
      </div>
    </div>
  )
}