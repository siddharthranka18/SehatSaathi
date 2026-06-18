export default function ChatBubble({ role, content }) {
  const isUser = role === 'user'
  return (
    <div
      style={{
        alignSelf: isUser ? 'flex-end' : 'flex-start',
        background: isUser ? '#dbeafe' : '#f1f5f9',
        padding: '8px 12px',
        borderRadius: 12,
        maxWidth: '75%',
      }}
    >
      {content}
    </div>
  )
}