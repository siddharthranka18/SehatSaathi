const SOURCE_MAP = {
  medical_guideline_rag: { label: 'Verified Medical Guideline', color: '#C8A45A' },
  web_fallback: { label: 'Live Web Search (unverified)', color: '#E57373' },
  safety_override: { label: 'Safety Rule', color: '#E57373' },
  output_guardrail: { label: 'Safety Guardrail', color: '#E57373' },
}

export default function ChatBubble({ role, content, source }) {
  const isUser = role === 'user'
  const src = SOURCE_MAP[source]

  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 10, flexDirection: isUser ? 'row-reverse' : 'row' }}>
      <div style={{ width: 32, height: 32, borderRadius: '50%', background: isUser ? '#1F4257' : '#C8A45A', color: isUser ? '#7A9BB0' : '#1B3A4B', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 500, flexShrink: 0, fontFamily: 'DM Sans, sans-serif' }}>
        {isUser ? 'U' : 'S'}
      </div>
      <div style={{ maxWidth: '72%', padding: '11px 15px', borderRadius: 16, borderBottomLeftRadius: isUser ? 16 : 3, borderBottomRightRadius: isUser ? 3 : 16, background: isUser ? '#1F4257' : '#16303F', borderLeft: isUser ? 'none' : '2px solid #C8A45A', color: '#F5F4F0', fontSize: 14, lineHeight: 1.6, fontFamily: 'DM Sans, sans-serif', wordBreak: 'break-word' }}>
        {content}
        {!isUser && src && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 8, paddingTop: 8, borderTop: '1px solid #1F4257' }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: src.color, display: 'inline-block', flexShrink: 0 }} />
            <span style={{ fontSize: 10, color: '#3D6478', fontFamily: 'DM Sans, sans-serif', letterSpacing: '0.03em' }}>{src.label}</span>
          </div>
        )}
      </div>
    </div>
  )
}