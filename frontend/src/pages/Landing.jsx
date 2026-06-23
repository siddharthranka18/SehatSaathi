import { useState, useEffect, useRef } from 'react'

const QUOTES = [
  "Your trusted health companion, always.",
  "आपका विश्वसनीय स्वास्थ्य साथी, हमेशा।",
  "உங்கள் நம்பகமான உடல்நல தோழன்.",
  "আপনার বিশ্বস্ত স্বাস্থ্য সঙ্গী।",
]

const CHIPS = ['English', 'हिंदी', 'தமிழ்', 'বাংলা']

const FEATURES = [
  {
    title: 'Smart Triage',
    body: 'Guided questions that lead to a clear urgency verdict — home care, PHC, or urgent.',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C8A45A" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
      </svg>
    ),
  },
  {
    title: 'Verified Sources',
    body: 'Every answer grounded in WHO and ICMR medical guidelines, not open-ended AI guessing.',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C8A45A" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    ),
  },
  {
    title: 'Nearest PHC',
    body: 'Points you to the closest primary health centre when in-person care is needed.',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C8A45A" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
        <circle cx="12" cy="10" r="3" />
      </svg>
    ),
  },
]

export default function Landing({ onStart }) {
  const [quoteIdx, setQuoteIdx] = useState(0)
  const [displayed, setDisplayed] = useState('')
  const [charIdx, setCharIdx] = useState(0)
  const [erasing, setErasing] = useState(false)
  const timer = useRef(null)

  useEffect(() => {
    const q = QUOTES[quoteIdx]
    clearTimeout(timer.current)
    if (!erasing) {
      if (charIdx < q.length) {
        timer.current = setTimeout(() => {
          setDisplayed(q.slice(0, charIdx + 1))
          setCharIdx(c => c + 1)
        }, charIdx === 0 ? 150 : 55)
      } else {
        timer.current = setTimeout(() => setErasing(true), 2400)
      }
    } else {
      if (charIdx > 0) {
        timer.current = setTimeout(() => {
          setDisplayed(q.slice(0, charIdx - 1))
          setCharIdx(c => c - 1)
        }, 28)
      } else {
        timer.current = setTimeout(() => {
          setErasing(false)
          setQuoteIdx(i => (i + 1) % QUOTES.length)
        }, 400)
      }
    }
    return () => clearTimeout(timer.current)
  }, [charIdx, erasing, quoteIdx])

  return (
    <>
      <style>{CSS}</style>
      <div className="l-root">

        {/* Hero */}
        <section className="l-hero">
          <div className="l-dots" aria-hidden="true" />

          <span className="l-badge">AI-Powered Health Triage</span>

          <h1 className="l-name">SehatSaathi</h1>

          <div className="l-quote-wrap">
            <span className="l-quote">
              {displayed}
              <span className="l-cursor" aria-hidden="true" />
            </span>
          </div>

          <p className="l-sub">Speak in your language — we understand</p>

          <div className="l-chips">
            {CHIPS.map((label, i) => (
              <span key={i} className={`l-chip${quoteIdx === i ? ' l-chip-active' : ''}`}>
                {label}
              </span>
            ))}
            <span className="l-chip">+ more</span>
          </div>

          <hr className="l-rule" aria-hidden="true" />

          <div className="l-trust">
            <span className="l-trust-item">Voice Support</span>
            <span className="l-trust-item">Verified Guidelines</span>
            <span className="l-trust-item">Private & Safe</span>
          </div>

          <button className="l-cta" onClick={onStart}>
            Start Consultation
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </button>
        </section>

        {/* Feature cards */}
        <section className="l-features">
          {FEATURES.map(f => (
            <div className="l-feat" key={f.title}>
              <div className="l-feat-accent" aria-hidden="true" />
              <div className="l-feat-icon" aria-hidden="true">{f.icon}</div>
              <p className="l-feat-title">{f.title}</p>
              <p className="l-feat-body">{f.body}</p>
            </div>
          ))}
        </section>

        {/* Footer */}
        <footer className="l-footer">
          <span className="l-footer-name">SehatSaathi</span>
          <span className="l-footer-note">This is triage guidance, not a medical diagnosis.</span>
        </footer>

      </div>
    </>
  )
}

const CSS = `
 .l-root {
  min-height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  background: #1B3A4B;
  color: #F5F4F0;
  font-family: 'DM Sans', sans-serif;
  color-scheme: light !important;
  margin: 0;
  padding: 0;
}

  /* ── Hero ── */
  .l-hero {
    padding: clamp(48px, 8vw, 72px) clamp(20px, 6vw, 48px) clamp(44px, 7vw, 64px);
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    overflow: hidden;
    flex: 1;
  }

  .l-dots {
    position: absolute;
    inset: 0;
    background-image: radial-gradient(circle, rgba(245,244,240,0.055) 1px, transparent 1px);
    background-size: 28px 28px;
    pointer-events: none;
    z-index: 0;
  }

  .l-badge {
    position: relative;
    z-index: 1;
    display: inline-block;
    background: rgba(200,164,90,0.1);
    border: 0.5px solid rgba(200,164,90,0.3);
    border-radius: 20px;
    padding: 5px 16px;
    color: #C8A45A;
    font-size: 10.5px;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 24px;
  }

  .l-name {
    position: relative;
    z-index: 1;
    font-family: 'DM Serif Display', serif;
    color: #F5F4F0;
    font-size: clamp(38px, 9vw, 62px);
    font-weight: 400;
    line-height: 1.05;
    letter-spacing: -0.5px;
    margin: 0 0 20px;
  }

  .l-quote-wrap {
    position: relative;
    z-index: 1;
    min-height: clamp(24px, 4vw, 30px);
    margin-bottom: 10px;
    padding: 0 12px;
    width: 100%;
    max-width: 560px;
  }

  .l-quote {
    color: #C8A45A;
    font-size: clamp(13px, 2.5vw, 16px);
    font-weight: 300;
    font-style: italic;
    letter-spacing: 0.01em;
  }

  .l-cursor {
    display: inline-block;
    width: 1.5px;
    height: 1em;
    background: #C8A45A;
    margin-left: 2px;
    vertical-align: -0.1em;
    animation: l-blink 1s step-end infinite;
  }

  @keyframes l-blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
  }

  .l-sub {
    position: relative;
    z-index: 1;
    color: #7A9BB0;
    font-size: clamp(11px, 1.8vw, 12.5px);
    letter-spacing: 0.06em;
    margin-bottom: 26px;
  }

  .l-chips {
    position: relative;
    z-index: 1;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
    margin-bottom: 36px;
    padding: 0 8px;
  }

  .l-chip {
    border: 0.5px solid rgba(245,244,240,0.12);
    border-radius: 20px;
    padding: 4px 13px;
    color: rgba(245,244,240,0.3);
    font-size: 12px;
    font-family: 'DM Sans', sans-serif;
    transition: all 0.35s ease;
    white-space: nowrap;
  }

  .l-chip-active {
    border-color: rgba(200,164,90,0.5) !important;
    color: #C8A45A !important;
    background: rgba(200,164,90,0.08) !important;
  }

  .l-rule {
    position: relative;
    z-index: 1;
    width: 100%;
    max-width: 380px;
    border: none;
    border-top: 0.5px solid rgba(245,244,240,0.08);
    margin: 0 0 24px;
  }

  .l-trust {
    position: relative;
    z-index: 1;
    display: flex;
    gap: clamp(14px, 4vw, 36px);
    justify-content: center;
    flex-wrap: wrap;
    margin-bottom: 40px;
  }

  .l-trust-item {
    color: rgba(245,244,240,0.38);
    font-size: 12px;
    display: flex;
    align-items: center;
    gap: 7px;
    white-space: nowrap;
  }

  .l-trust-item::before {
    content: '';
    display: inline-block;
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #C8A45A;
    flex-shrink: 0;
  }

  .l-cta {
    position: relative;
    z-index: 1;
    background: #C8A45A;
    color: #1B3A4B;
    border: none;
    border-radius: 3px;
    padding: 14px 44px;
    font-size: 13.5px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    cursor: pointer;
    letter-spacing: 0.04em;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    transition: background 0.2s ease, transform 0.1s ease;
  }

  .l-cta:hover { background: #D4B06A; }
  .l-cta:active { transform: scale(0.985); }

  /* ── Features ── */
  .l-features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    border-top: 1px solid #1F4257;
  }

  .l-feat {
    background: #16303F;
    border-right: 1px solid #1F4257;
    padding: clamp(20px, 3vw, 28px) clamp(18px, 3vw, 28px) clamp(20px, 3vw, 28px) clamp(16px, 2.5vw, 26px);
    position: relative;
  }

  .l-feat:last-child { border-right: none; }

  .l-feat-accent {
    position: absolute;
    top: 0;
    left: 0;
    width: 2px;
    height: 100%;
    background: #C8A45A;
    opacity: 0.7;
    border-radius: 0;
  }

  .l-feat-icon {
    width: 32px;
    height: 32px;
    border-radius: 3px;
    background: rgba(200,164,90,0.1);
    border: 0.5px solid rgba(200,164,90,0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 14px;
  }

  .l-feat-title {
    font-size: 13px;
    font-weight: 500;
    color: #F5F4F0;
    margin-bottom: 7px;
    letter-spacing: 0.01em;
  }

  .l-feat-body {
    font-size: 12px;
    color: #7A9BB0;
    line-height: 1.65;
  }

  /* ── Footer ── */
  .l-footer {
    background: #132C3A;
    border-top: 1px solid #1F4257;
    padding: 14px clamp(20px, 5vw, 48px);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }

  .l-footer-name {
    font-family: 'DM Serif Display', serif;
    color: #F5F4F0;
    font-size: 13px;
  }

  .l-footer-note {
    color: #3D6478;
    font-size: 11px;
    letter-spacing: 0.03em;
  }

  /* ── Responsive ── */
  @media (max-width: 640px) {
    .l-cta {
      width: 100%;
      max-width: 300px;
      justify-content: center;
    }
    .l-features {
      grid-template-columns: 1fr;
    }
    .l-feat {
      border-right: none;
      border-bottom: 1px solid #1F4257;
    }
    .l-feat:last-child {
      border-bottom: none;
    }
    .l-footer {
      flex-direction: column;
      text-align: center;
    }
  }

  @media (max-width: 380px) {
    .l-badge { font-size: 9.5px; padding: 4px 12px; }
    .l-chip { font-size: 11px; padding: 3px 10px; }
    .l-trust { gap: 12px; }
  }
`