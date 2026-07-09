import { useState, useRef, useEffect, useCallback } from 'react'
import ChatBubble from '../components/ChatBubble.jsx'
import TriageCard from '../components/TriageCard.jsx'
import VoiceInput from '../components/VoiceInput.jsx'

const SOURCE_MAP = {
  medical_guideline_rag: 'Verified Medical Guideline',
  web_fallback: 'Live Web Search (unverified)',
  safety_override: 'Safety Rule',
  output_guardrail: 'Safety Guardrail',
}

export default function Home({ onBack }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hi, I am SehatSaathi. Please tell me what symptom you are experiencing.',
      source: null,
      urgency: null,
      is_final: false,
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [ttsEnabled, setTtsEnabled] = useState(true)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // pre-load voices as soon as component mounts
useEffect(() => {
  const loadVoices = () => window.speechSynthesis.getVoices()
  loadVoices()
  window.speechSynthesis.onvoiceschanged = loadVoices
}, [])
const speak = useCallback((text) => {
  if (!ttsEnabled) return
  if (!window.speechSynthesis) return
  window.speechSynthesis.cancel()

  const utt = new SpeechSynthesisUtterance(text)
  utt.rate = 0.88
  utt.pitch = 1

  // detect language from the text itself
  const hindiPattern = /[\u0900-\u097F]/  // Devanagari unicode range
  const tamilPattern = /[\u0B80-\u0BFF]/  // Tamil unicode range
  const bengaliPattern = /[\u0980-\u09FF]/ // Bengali unicode range

  if (hindiPattern.test(text)) {
    utt.lang = 'hi-IN'
  } else if (tamilPattern.test(text)) {
    utt.lang = 'ta-IN'
  } else if (bengaliPattern.test(text)) {
    utt.lang = 'bn-IN'
  } else {
    utt.lang = 'en-IN'
  }

  // try to find a matching voice for the detected language
  const voices = window.speechSynthesis.getVoices()
  const matchingVoice = voices.find(v => v.lang === utt.lang)
    || voices.find(v => v.lang.startsWith(utt.lang.split('-')[0]))

  if (matchingVoice) {
    utt.voice = matchingVoice
  }

  window.speechSynthesis.speak(utt)
}, [ttsEnabled])

  // stop TTS when component unmounts or user goes back
  useEffect(() => {
    return () => window.speechSynthesis?.cancel()
  }, [])

  async function sendMessage(text) {
    if (!text.trim() || loading) return
    const userMsg = {
      role: 'user',
      content: text,
      source: null,
      urgency: null,
      is_final: false,
    }
    const updated = [...messages, userMsg]
    setMessages(updated)
    setInput('')
    setLoading(true)

    const fetchStart = performance.now()
    try {
      const res = await fetch('/api/triage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation: updated.map(m => ({ role: m.role, content: m.content })),
          language: 'en',
        }),
      })
      const data = await res.json()
      const clientLatency = (performance.now() - fetchStart) / 1000
      const aiMsg = {
        role: 'assistant',
        content: data.reply,
        source: data.source,
        urgency: data.urgency,
        is_final: data.is_final,
        confidence: data.confidence || 0,
        retrievedSources: data.retrieved_sources || [],
        latency: data.pipeline_timings?.total || clientLatency,
      }
      setMessages([...updated, aiMsg])
      speak(data.reply)
    } catch {
      const errMsg = {
        role: 'assistant',
        content: 'Something went wrong. Please try again.',
        source: null,
        urgency: null,
        is_final: false,
        confidence: 0,
        retrievedSources: [],
        latency: 0,
      }
      setMessages([...updated, errMsg])
    }
    setLoading(false)
  }

  function handleSend() {
    sendMessage(input)
  }

  // called by VoiceInput when transcript is ready — auto-sends
  function handleTranscript(transcript) {
    setInput(transcript)
    setTimeout(() => sendMessage(transcript), 300)
  }

  function handleNewConversation() {
    window.speechSynthesis?.cancel()
    setMessages([{
      role: 'assistant',
      content: 'Hi, I am SehatSaathi. Please tell me what symptom you are experiencing.',
      source: null,
      urgency: null,
      is_final: false,
    }])
    setInput('')
  }

  return (
    <>
      <style>{CSS}</style>
      <div className="h-root">

        {/* Header */}
        <div className="h-header">
          <button className="h-back" onClick={() => { window.speechSynthesis?.cancel(); onBack() }} aria-label="Back to home">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <line x1="19" y1="12" x2="5" y2="12" />
              <polyline points="12 19 5 12 12 5" />
            </svg>
            Back
          </button>

          <span className="h-title">SehatSaathi</span>

          <div className="h-header-actions">
            {/* TTS toggle */}
            <button
              className={`h-tts-btn${ttsEnabled ? ' active' : ''}`}
              onClick={() => { setTtsEnabled(v => !v); window.speechSynthesis?.cancel() }}
              aria-label={ttsEnabled ? 'Mute voice replies' : 'Enable voice replies'}
              title={ttsEnabled ? 'Voice on — tap to mute' : 'Voice off — tap to enable'}
            >
              {ttsEnabled ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                  <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
                  <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                  <line x1="23" y1="9" x2="17" y2="15" />
                  <line x1="17" y1="9" x2="23" y2="15" />
                </svg>
              )}
            </button>

            {/* New conversation */}
            <button
              className="h-new-btn"
              onClick={handleNewConversation}
              aria-label="Start new conversation"
              title="New conversation"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="1 4 1 10 7 10" />
                <path d="M3.51 15a9 9 0 1 0 .49-3.36" />
              </svg>
            </button>
          </div>
        </div>

        {/* Chat area */}
        <div className="h-chat">
          <div className="h-chat-inner">
            {messages.map((m, i) => (
              <div key={i}>
                <ChatBubble role={m.role} content={m.content} source={m.source} />
                {m.urgency && <TriageCard urgency={m.urgency} source={m.source} confidence={m.confidence} retrievedSources={m.retrievedSources} latency={m.latency} />}
              </div>
            ))}

            {loading && (
              <div className="h-typing-row">
                <div className="h-avatar-ai">S</div>
                <div className="h-typing-bubble">
                  <span /><span /><span />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </div>

        {/* Disclaimer */}
        <div className="h-disclaimer">
          Guidance only — not a medical diagnosis. For emergencies call 112.
        </div>

        {/* Input bar */}
        <div className="h-input-bar">
          <div className="h-input-wrap">
            <VoiceInput
              onTranscript={handleTranscript}
              disabled={loading}
              language="en"
            />
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              placeholder="Type or tap mic to speak…"
              disabled={loading}
              className="h-input"
              aria-label="Describe your symptom"
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="h-send-btn"
              aria-label="Send message"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
        </div>

      </div>
    </>
  )
}

const CSS = `
  .h-root {
    width: 100%;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: #1B3A4B;
    font-family: 'DM Sans', sans-serif;
    color-scheme: light !important;
  }

  /* Header */
  .h-header {
    background: #132C3A;
    border-bottom: 1px solid #1F4257;
    padding: 12px clamp(16px, 4vw, 28px);
    display: flex;
    align-items: center;
    gap: 12px;
    flex-shrink: 0;
  }

  .h-back {
    background: transparent;
    border: none;
    color: rgba(245,244,240,0.45);
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12.5px;
    font-family: 'DM Sans', sans-serif;
    padding: 0;
    transition: color 0.2s;
    white-space: nowrap;
  }

  .h-back:hover { color: #F5F4F0; }

  .h-title {
    font-family: 'DM Serif Display', serif;
    color: #F5F4F0;
    font-size: 18px;
    font-weight: 400;
    flex: 1;
    text-align: center;
  }

  .h-header-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .h-tts-btn, .h-new-btn {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    border: 1px solid #1F4257;
    background: transparent;
    color: rgba(245,244,240,0.4);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
  }

  .h-tts-btn:hover, .h-new-btn:hover {
    background: #16303F;
    color: #F5F4F0;
  }

  .h-tts-btn.active {
    border-color: rgba(200,164,90,0.5);
    color: #C8A45A;
  }

  /* Chat */
  .h-chat {
    flex: 1;
    overflow-y: auto;
    padding: 20px clamp(12px, 4vw, 24px);
    background: #1B3A4B;
  }

  .h-chat::-webkit-scrollbar { width: 4px; }
  .h-chat::-webkit-scrollbar-track { background: transparent; }
  .h-chat::-webkit-scrollbar-thumb { background: #1F4257; border-radius: 4px; }

  .h-chat-inner {
    max-width: 680px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  /* Typing indicator */
  .h-typing-row {
    display: flex;
    align-items: flex-end;
    gap: 10px;
  }

  .h-avatar-ai {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: #C8A45A;
    color: #1B3A4B;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 500;
    flex-shrink: 0;
  }

  .h-typing-bubble {
    background: #16303F;
    border: 1px solid #1F4257;
    border-radius: 16px;
    border-bottom-left-radius: 4px;
    padding: 12px 16px;
    display: flex;
    gap: 5px;
    align-items: center;
  }

  .h-typing-bubble span {
    width: 6px;
    height: 6px;
    background: #7A9BB0;
    border-radius: 50%;
    display: inline-block;
    animation: h-bounce 1.2s ease-in-out infinite;
  }

  .h-typing-bubble span:nth-child(2) { animation-delay: 0.2s; }
  .h-typing-bubble span:nth-child(3) { animation-delay: 0.4s; }

  @keyframes h-bounce {
    0%, 80%, 100% { transform: translateY(0); }
    40% { transform: translateY(-6px); }
  }

  /* Disclaimer */
  .h-disclaimer {
    text-align: center;
    color: #3D6478;
    font-size: 11px;
    padding: 6px 16px;
    background: #1B3A4B;
    letter-spacing: 0.03em;
    flex-shrink: 0;
  }

  /* Input bar */
  .h-input-bar {
    background: #132C3A;
    border-top: 1px solid #1F4257;
    padding: 12px clamp(12px, 4vw, 24px);
    flex-shrink: 0;
  }

  .h-input-wrap {
    max-width: 680px;
    margin: 0 auto;
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .h-input {
    flex: 1;
    background: #16303F;
    border: 1px solid #1F4257;
    border-radius: 24px;
    padding: 11px 18px;
    font-size: 14px;
    font-family: 'DM Sans', sans-serif;
    color: #F5F4F0;
    outline: none;
    transition: border-color 0.2s;
  }

  .h-input::placeholder { color: #3D6478; }
  .h-input:focus { border-color: rgba(200,164,90,0.4); }
  .h-input:disabled { opacity: 0.5; }

  .h-send-btn {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    border: none;
    background: #C8A45A;
    color: #1B3A4B;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: background 0.2s, transform 0.1s, opacity 0.2s;
  }

  .h-send-btn:hover:not(:disabled) { background: #D4B06A; }
  .h-send-btn:active:not(:disabled) { transform: scale(0.95); }
  .h-send-btn:disabled { opacity: 0.35; cursor: default; }

  /* Voice pulse ring */
  @keyframes voice-pulse {
    0% { transform: scale(1); opacity: 0.6; }
    100% { transform: scale(1.5); opacity: 0; }
  }

  /* Responsive */
  @media (max-width: 480px) {
    .h-title { font-size: 16px; }
    .h-input { font-size: 13px; padding: 10px 14px; }
  }
`