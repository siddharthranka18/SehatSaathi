const META = {
  home_care: { label: 'Home Care ✓', bg: '#e8f5e9', border: '#81c784', color: '#2e7d32' },
  visit_phc: { label: 'Visit PHC within 24–48 hrs', bg: '#fff8e1', border: '#ffca28', color: '#f57f17' },
  critical: { label: 'Critical — Seek Help Now', bg: '#ffebee', border: '#e57373', color: '#c62828' },
}
const SOURCE_MAP = {
  medical_guideline_rag: 'Verified Medical Guideline',
  web_fallback: 'Live Web Search (unverified)',
  safety_override: 'Safety Rule',
}

export default function TriageCard({ urgency, source }) {
  if (!urgency || urgency === 'unclear') return null
  const m = META[urgency]
  if (!m) return null
  return (
    <div style={{ marginLeft: 36, background: m.bg, border: `1px solid ${m.border}`, borderRadius: 12, padding: '10px 14px' }}>
      <div style={{ fontFamily: 'Nunito, sans-serif', fontWeight: 700, fontSize: 14, color: m.color }}>{m.label}</div>
      {SOURCE_MAP[source] && <div style={{ fontSize: 11, color: '#6b8f8f', marginTop: 3 }}>Source: {SOURCE_MAP[source]}</div>}
    </div>
  )
}