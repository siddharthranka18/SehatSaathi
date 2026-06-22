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
    body: 'Guided questions that lead to a clear urgency verdict — home care, visit PHC, or urgent.',
  },
  {
    title: 'Verified Sources',
    body: 'Every answer grounded in WHO and ICMR medical guidelines, not open-ended AI guessing.',
  },
  {
    title: 'Nearest PHC',
    body: 'When you need in-person care, it points you to the closest primary health centre.',
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
      <style>{STYLES}</style>
      <div className="land-root">

        {/* ── Hero ── */}
        <section className="land-hero">
          <div className="land-dots" aria-hidden="true" />

          <span className="land-badge">AI-Powered Health Triage</span>

          <h1 className="land-name">SehatSaathi</h1>

          <div className="land-quote-wrap">
            <span className="land-quote">
              {displayed}
              <span className="land-cursor" aria-hidden="true" />
            </span>
          </div>

          <p className="land-sub">Speak in your language — we understand</p>

          <div className="land-chips" role="list" aria-label="Supported languages">
            {CHIPS.map((label, i) => (
              <span
                key={i}
                role="listitem"
                className={`land-chip${quoteIdx === i ? ' active' : ''}`}
              >
                {label}
              </span>
            ))}
            <span role="listitem" className="land-chip">+ more</span>
          </div>

          <hr className="land-rule" aria-hidden="true" />

          <div className="land-trust">
            <span className="land-trust-item">Voice Support</span>
            <span className="land-trust-item">Verified Guidelines</span>
            <span className="land-trust-item">Private & Safe</span>
          </div>

          <button className="land-cta" onClick={onStart}>
            Start Consultation
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </button>
        </section>

        {/* ── Feature cards ── */}
        <section className="land-features" aria-label="What SehatSaathi does">
          {FEATURES.map(f => (
            <div className="land-feat" key={f.title}>
              <div className="land-feat-accent" aria-hidden="true" />
              <p className="land-feat-title">{f.title}</p>
              <p className="land-feat-body">{f.body}</p>
            </div>
          ))}
        </section>

        {/* ── Footer strip ── */}
        <footer className="land-footer">
          <span>SehatSaathi</span>
          <span>This is triage guidance, not a medical diagnosis.</span>
        </footer>

      </div>
    </>
  )
}

const STYLES = `
  .land-root {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: #F5F4F0;
    color: #0F1F2A;
    font-family: 'DM Sans', sans-serif;
    color-scheme: light !important;
  }

  /* ── Hero ── */
  .land-hero {
    background: #1B3A4B;
    padding: 72px 48px 64px;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    overflow: hidden;
    flex-shrink: 0;
  }

  .land-dots {
    position: absolute;
    inset: 0;
    background-image: radial-gradient(circle, rgba(245,244,240,0.07) 1px, transparent 1px);
    background-size: 28px 28px;
    pointer-events: none;
    z-index: 0;
  }

  .land-badge {
    position: relative;
    z-index: 1;
    display: inline-block;
    background: rgba(200,164,90,0.1);
    border: 0.5px solid rgba(200,164,90,0.35);
    border-radius: 20px;
    padding: 5px 16px;
    color: #C8A45A;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 28px;
  }

  .land-name {
    position: relative;
    z-index: 1;
    font-family: 'DM Serif Display', serif;
    color: #F5F4F0;
    font-size: clamp(40px, 9vw, 70px);
    font-weight: 400;
    line-height: 1.05;
    letter-spacing: -0.5px;
    margin: 0 0 22px;
  }

  .land-quote-wrap {
    position: relative;
    z-index: 1;
    min-height: clamp(26px, 4vw, 34px);
    margin-bottom: 12px;
    padding: 0 12px;
    width: 100%;
    max-width: 580px;
  }

  .land-quote {
    color: #C8A45A;
    font-size: clamp(13px, 2.5vw, 17px);
    font-weight: 300;
    letter-spacing: 0.01em;
    font-style: italic;
  }

  .land-cursor {
    display: inline-block;
    width: 1.5px;
    height: 1em;
    background: #C8A45A;
    margin-left: 2px;
    vertical-align: -0.1em;
    animation: land-blink 1s step-end infinite;
  }

  @keyframes land-blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
  }

  .land-sub {
    position: relative;
    z-index: 1;
    color: #7A9BB0;
    font-size: clamp(11px, 1.8vw, 13px);
    font-weight: 400;
    letter-spacing: 0.06em;
    margin-bottom: 28px;
  }

  .land-chips {
    position: relative;
    z-index: 1;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
    margin-bottom: 40px;
    padding: 0 8px;
  }

  .land-chip {
    border: 0.5px solid rgba(245,244,240,0.15);
    border-radius: 20px;
    padding: 4px 14px;
    color: rgba(245,244,240,0.38);
    font-size: 12px;
    font-family: 'DM Sans', sans-serif;
    transition: all 0.35s ease;
    white-space: nowrap;
  }

  .land-chip.active {
    border-color: rgba(200,164,90,0.55);
    color: #C8A45A;
    background: rgba(200,164,90,0.08);
  }

  .land-rule {
    position: relative;
    z-index: 1;
    width: 100%;
    max-width: 400px;
    border: none;
    border-top: 0.5px solid rgba(245,244,240,0.1);
    margin: 0 0 28px;
  }

  .land-trust {
    position: relative;
    z-index: 1;
    display: flex;
    gap: clamp(16px, 4vw, 40px);
    justify-content: center;
    flex-wrap: wrap;
    margin-bottom: 44px;
  }

  .land-trust-item {
    color: rgba(245,244,240,0.42);
    font-size: 12px;
    font-family: 'DM Sans', sans-serif;
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
  }

  .land-trust-item::before {
    content: '';
    display: inline-block;
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #C8A45A;
    flex-shrink: 0;
  }

  .land-cta {
    position: relative;
    z-index: 1;
    background: #C8A45A;
    color: #1B3A4B;
    border: none;
    border-radius: 3px;
    padding: 15px 44px;
    font-size: 14px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    cursor: pointer;
    letter-spacing: 0.04em;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    transition: background 0.2s ease, transform 0.1s ease;
  }

  .land-cta:hover { background: #D4B06A; }
  .land-cta:active { transform: scale(0.985); }

  /* ── Features ── */
  .land-features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1px;
    background: #E0DDD6;
    border-top: 1px solid #E0DDD6;
  }

  .land-feat {
    background: #F5F4F0;
    padding: clamp(24px, 4vw, 36px) clamp(20px, 4vw, 36px);
    position: relative;
    overflow: hidden;
  }

  .land-feat-accent {
    position: absolute;
    top: 0;
    left: 0;
    width: 2px;
    height: 100%;
    background: #C8A45A;
    opacity: 0.5;
  }

  .land-feat-title {
    font-size: 14px;
    font-weight: 500;
    color: #0F1F2A;
    margin-bottom: 8px;
    letter-spacing: 0.01em;
  }

  .land-feat-body {
    font-size: 13px;
    color: #6B7B8A;
    line-height: 1.65;
    font-weight: 400;
  }

  /* ── Footer ── */
  .land-footer {
    background: #132C3A;
    padding: 16px clamp(20px, 5vw, 48px);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: auto;
  }

  .land-footer span:first-child {
    font-family: 'DM Serif Display', serif;
    color: #F5F4F0;
    font-size: 14px;
  }

  .land-footer span:last-child {
    color: rgba(245,244,240,0.35);
    font-size: 11px;
    font-weight: 400;
    letter-spacing: 0.03em;
  }

  /* ── Responsive ── */
  @media (max-width: 640px) {
    .land-hero {
      padding: 52px 20px 48px;
    }
    .land-cta {
      width: 100%;
      max-width: 320px;
      justify-content: center;
      padding: 15px 24px;
    }
    .land-trust {
      gap: 14px;
    }
    .land-features {
      grid-template-columns: 1fr;
    }
    .land-footer {
      flex-direction: column;
      text-align: center;
    }
  }

  @media (max-width: 380px) {
    .land-badge {
      font-size: 10px;
      padding: 4px 12px;
    }
    .land-chips {
      gap: 6px;
    }
    .land-chip {
      font-size: 11px;
      padding: 3px 10px;
    }
  }
`