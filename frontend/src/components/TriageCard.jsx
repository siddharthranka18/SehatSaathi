const META = {
  home_care: { label: 'Home Care', sub: 'Manageable at home', color: '#4CAF82', bg: 'rgba(76,175,130,0.08)', border: 'rgba(76,175,130,0.3)' },
  visit_phc: { label: 'Visit PHC', sub: 'Within 24–48 hours', color: '#C8A45A', bg: 'rgba(200,164,90,0.08)', border: 'rgba(200,164,90,0.3)' },
  critical: { label: 'Critical', sub: 'Seek help immediately', color: '#E57373', bg: 'rgba(229,115,115,0.08)', border: 'rgba(229,115,115,0.3)' },
}

export default function TriageCard({ urgency, source }) {
  if (!urgency || urgency === 'unclear') return null
  const m = META[urgency]
  if (!m) return null

  return (
    <div style={{ marginLeft: 42, marginTop: 6, background: m.bg, border: `1px solid ${m.border}`, borderLeft: `3px solid ${m.color}`, borderRadius: 8, padding: '12px 16px' }}>
      <div style={{ fontFamily: 'DM Sans, sans-serif', fontWeight: 500, fontSize: 14, color: m.color }}>{m.label}</div>
      <div style={{ fontFamily: 'DM Sans, sans-serif', fontSize: 12, color: '#7A9BB0', marginTop: 2 }}>{m.sub}</div>
    </div>
  )
}