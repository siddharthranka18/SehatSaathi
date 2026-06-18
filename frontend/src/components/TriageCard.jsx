const URGENCY_STYLES = {
  home_care: { label: 'Home Care', color: '#16a34a', bg: '#dcfce7' },
  visit_phc: { label: 'Visit PHC (24-48 hrs)', color: '#b45309', bg: '#fef3c7' },
  critical: { label: 'Critical — Seek Help Now', color: '#dc2626', bg: '#fee2e2' },
}

const SOURCE_LABELS = {
  safety_override: 'Hard Safety Rule',
  medical_guideline_rag: 'Verified Medical Guideline',
  web_fallback: 'Live Web Search (unverified)',
  output_guardrail: 'Safety Guardrail',
}

export default function TriageCard({ urgency, source }) {
  if (!urgency || urgency === 'unclear') return null
  const style = URGENCY_STYLES[urgency] || { label: urgency, color: '#475569', bg: '#f1f5f9' }
  const sourceLabel = SOURCE_LABELS[source] || source

  return (
    <div style={{ border: `1px solid ${style.color}`, background: style.bg, borderRadius: 10, padding: '10px 14px', margin: '8px 0' }}>
      <div style={{ fontWeight: 700, color: style.color }}>{style.label}</div>
      {sourceLabel && <div style={{ fontSize: 12, color: '#475569', marginTop: 4 }}>Source: {sourceLabel}</div>}
    </div>
  )
}