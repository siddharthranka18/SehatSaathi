const SOURCE_MAP = {
  medical_guideline_rag: { label: 'Verified Medical Guideline', color: '#0D7377' },
  web_fallback: { label: 'Live Web Search (unverified)', color: '#F4A261' },
  safety_override: { label: 'Safety Rule', color: '#c62828' },
  output_guardrail: { label: 'Safety Guardrail', color: '#c62828' },
}

export default function ChatBubble({ role, content, source }) {
  const isUser = role === 'user'
  const src = SOURCE_MAP[source]

  return (
    <div style={{
      display: 'flex',
      alignItems: 'flex-end',
      gap: 10,
      flexDirection: isUser ? 'row-reverse' : 'row',
      margin: '2px 0',
    }}>

      {/* Avatar */}
      <div style={{
        width: 32,
        height: 32,
        borderRadius: '50%',
        background: isUser ? '#F4A261' : '#0D7377',
        color: '#ffffff',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 13,
        fontWeight: 700,
        flexShrink: 0,
        fontFamily: 'Nunito, sans-serif',
        boxShadow: isUser ? '0 2px 8px rgba(244,162,97,0.35)' : '0 2px 8px rgba(13,115,119,0.25)',
      }}>
        {isUser ? 'U' : 'S'}
      </div>

      {/* Bubble */}
      <div style={{
        maxWidth: '72%',
        padding: '11px 15px',
        borderRadius: 18,
        borderBottomLeftRadius: isUser ? 18 : 4,
        borderBottomRightRadius: isUser ? 4 : 18,
        background: isUser ? '#0D7377' : '#ffffff',
        border: isUser ? '1.5px solid #0D7377' : '1px solid #dde9e9',
        color: isUser ? '#ffffff' : '#1a2e2e',
        fontSize: 14,
        lineHeight: 1.6,
        fontFamily: 'Inter, sans-serif',
        WebkitFontSmoothing: 'antialiased',
        wordBreak: 'break-word',
      }}>
        <span style={{ color: isUser ? '#ffffff' : '#1a2e2e' }}>{content}</span>

        {/* Source indicator — only on AI messages */}
        {!isUser && src && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 5,
            marginTop: 7,
            paddingTop: 7,
            borderTop: '1px solid #eef3f3',
          }}>
            <span style={{
              width: 7,
              height: 7,
              borderRadius: '50%',
              background: src.color,
              display: 'inline-block',
              flexShrink: 0,
            }} />
            <span style={{
              fontSize: 10,
              color: '#7a9f9f',
              fontFamily: 'Inter, sans-serif',
              letterSpacing: '0.02em',
            }}>
              {src.label}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}