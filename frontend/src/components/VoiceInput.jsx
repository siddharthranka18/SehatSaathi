import { useState, useEffect, useRef } from 'react'

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

export default function VoiceInput({ onTranscript, disabled, language = 'en' }) {
  const [listening, setListening] = useState(false)
  const recognitionRef = useRef(null)

  const LANG_MAP = {
    en: 'en-IN',
    hi: 'hi-IN',
    ta: 'ta-IN',
    bn: 'bn-IN',
  }

  useEffect(() => {
    return () => {
      if (recognitionRef.current) recognitionRef.current.stop()
    }
  }, [])

  function startListening() {
    if (!SpeechRecognition) {
      alert('Voice input is not supported in this browser. Please use Chrome.')
      return
    }

    const recognition = new SpeechRecognition()
    recognitionRef.current = recognition

    recognition.lang = LANG_MAP[language] || 'en-IN'
    recognition.interimResults = false
    recognition.maxAlternatives = 1
    recognition.continuous = false

    recognition.onstart = () => setListening(true)

    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript
      onTranscript(transcript)
    }

    recognition.onerror = (e) => {
      console.error('Speech recognition error:', e.error)
      setListening(false)
    }

    recognition.onend = () => setListening(false)

    recognition.start()
  }

  function stopListening() {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
      setListening(false)
    }
  }

  return (
    <button
      onClick={listening ? stopListening : startListening}
      disabled={disabled}
      aria-label={listening ? 'Stop listening' : 'Start voice input'}
      title={listening ? 'Tap to stop' : 'Tap to speak'}
      style={{
        width: 44,
        height: 44,
        borderRadius: '50%',
        border: listening ? '2px solid #E57373' : '1px solid #1F4257',
        background: listening ? 'rgba(229,115,115,0.1)' : '#16303F',
        cursor: disabled ? 'default' : 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
        opacity: disabled ? 0.4 : 1,
        transition: 'all 0.2s ease',
        position: 'relative',
      }}
    >
      {/* Pulse ring when listening */}
      {listening && (
        <span style={{
          position: 'absolute',
          inset: -4,
          borderRadius: '50%',
          border: '2px solid rgba(229,115,115,0.4)',
          animation: 'voice-pulse 1.2s ease-out infinite',
        }} />
      )}
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke={listening ? '#E57373' : '#7A9BB0'}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <rect x="9" y="2" width="6" height="11" rx="3" />
        <path d="M5 10a7 7 0 0 0 14 0" />
        <line x1="12" y1="19" x2="12" y2="22" />
        <line x1="9" y1="22" x2="15" y2="22" />
      </svg>
    </button>
  )
}