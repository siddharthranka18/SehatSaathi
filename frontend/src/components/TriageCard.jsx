const META = {
  home_care: { label: 'Home Care', sub: 'Manageable at home', color: '#4CAF82', bg: 'rgba(76,175,130,0.08)', border: 'rgba(76,175,130,0.3)' },
  visit_phc: { label: 'Visit PHC', sub: 'Within 24–48 hours', color: '#C8A45A', bg: 'rgba(200,164,90,0.08)', border: 'rgba(200,164,90,0.3)' },
  critical: { label: 'Critical', sub: 'Seek help immediately', color: '#E57373', bg: 'rgba(229,115,115,0.08)', border: 'rgba(229,115,115,0.3)' },
}

export default function TriageCard({ urgency, source, confidence, retrievedSources, latency }) {
  if (!urgency || urgency === 'unclear') return null
  const m = META[urgency]
  if (!m) return null

  return (
    <div style={{
      marginLeft: 42, marginTop: 6,
      background: m.bg,
      border: `1px solid ${m.border}`,
      borderLeft: `3px solid ${m.color}`,
      borderRadius: 8,
      padding: '12px 16px',
    }}>
      <div style={{ fontFamily: 'DM Sans, sans-serif', fontWeight: 500, fontSize: 14, color: m.color }}>{m.label}</div>
      <div style={{ fontFamily: 'DM Sans, sans-serif', fontSize: 12, color: '#7A9BB0', marginTop: 2 }}>{m.sub}</div>

      {/* Confidence */}
      {confidence > 0 && (
        <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 11, color: '#7A9BB0' }}>Confidence</span>
          <span style={{
            fontSize: 13, fontWeight: 600,
            color: confidence > 0.7 ? '#4CAF82' : confidence > 0.4 ? '#C8A45A' : '#E57373',
          }}>
            {confidence.toFixed(2)}
          </span>
          <div style={{
            flex: 1, height: 4, background: 'rgba(122,155,176,0.15)', borderRadius: 2, overflow: 'hidden',
          }}>
            <div style={{
              width: `${Math.min(confidence * 100, 100)}%`,
              height: '100%',
              background: confidence > 0.7 ? '#4CAF82' : confidence > 0.4 ? '#C8A45A' : '#E57373',
              borderRadius: 2,
              transition: 'width 0.5s ease',
            }} />
          </div>
        </div>
      )}

      {/* Retrieved Sources */}
      {retrievedSources && retrievedSources.length > 0 && (
        <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 11, color: '#7A9BB0' }}>Retrieved from</span>
          {retrievedSources.map((src, i) => (
            <span key={i} style={{
              fontSize: 11, fontWeight: 500,
              color: '#C8A45A',
              background: 'rgba(200,164,90,0.1)',
              border: '1px solid rgba(200,164,90,0.25)',
              borderRadius: 4,
              padding: '2px 6px',
            }}>
              {src.replace('.txt', '')}
            </span>
          ))}
        </div>
      )}

      {/* Latency */}
      {latency > 0 && (
        <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 11, color: '#7A9BB0' }}>Latency</span>
          <span style={{ fontSize: 12, fontWeight: 500, color: '#5C9BD4' }}>
            {latency.toFixed(1)} sec
          </span>
        </div>
      )}
    </div>
  )
}