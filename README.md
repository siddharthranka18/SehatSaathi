<div align="center">

<img src="https://img.shields.io/badge/SehatSaathi-AI%20Health%20Triage-C8A45A?style=for-the-badge&logoColor=white" alt="SehatSaathi" />

<br />
<br />

**Voice-first AI health triage assistant for rural and elderly India**

*Describe your symptom. Get a clear answer. Know what to do next.*

<br />

[![Python](https://img.shields.io/badge/Python-3.11-1B3A4B?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-1B3A4B?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-1B3A4B?style=flat-square&logo=react&logoColor=white)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Ready-1B3A4B?style=flat-square&logo=docker&logoColor=white)](docker-compose.yml)
[![Groq](https://img.shields.io/badge/Groq-LLaMA%203.3-1B3A4B?style=flat-square&logoColor=white)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-C8A45A?style=flat-square)](LICENSE)

<br />

</div>

---

## The Problem

India's rural doctor-to-patient ratio is **1:11,000** — nearly 11× worse than the national average. When a rural or elderly patient experiences a symptom, they face three barriers at once: a multi-hour trip to the nearest clinic, no quick way to assess urgency, and no follow-up support once they do get care.

**SehatSaathi** is a voice-first AI companion that fills this gap — not by replacing doctors, but by giving patients a trusted, instant first response in their own language.

---

## What It Does

A patient describes their symptom by typing or speaking. SehatSaathi asks a few short, adaptive follow-up questions — the way a triage nurse would — then delivers a clear verdict:

| Verdict | Meaning |
|---|---|
| 🟢 **Home Care** | Manageable at home with guidance |
| 🟡 **Visit PHC** | See a doctor within 24–48 hours |
| 🔴 **Critical** | Seek urgent medical attention now |

Every answer is grounded in verified WHO and ICMR medical guidelines — not open-ended AI reasoning — and the source is shown to the user.

---

## Architecture

```
User (voice or text)
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│                    FastAPI Backend                        │
│                                                          │
│  Input ──► Hard Safety Rules ──► [STOP if red flag]      │
│                │                                         │
│                ▼                                         │
│         Query Rewriting (LLM)                            │
│                │                                         │
│                ▼                                         │
│    ┌───────────────────────────┐                         │
│    │     Hybrid RAG Pipeline   │                         │
│    │                           │                         │
│    │  Dense (Qdrant + HNSW)    │                         │
│    │         +                 │                         │
│    │  Sparse (BM25)            │                         │
│    │         │                 │                         │
│    │   RRF Fusion              │                         │
│    │         │                 │                         │
│    │  Parent Doc Retrieval     │                         │
│    │         │                 │                         │
│    │  Cross-Encoder Reranking  │                         │
│    └───────────────────────────┘                         │
│                │                                         │
│                ▼                                         │
│       Confidence Check                                   │
│        /              \                                  │
│  High confidence    Low confidence                       │
│  (Local KB)         (Web Fallback)                       │
│        \              /                                  │
│                ▼                                         │
│        Groq LLM Reasoning                                │
│         (LLaMA 3.3-70B)                                  │
│                │                                         │
│                ▼                                         │
│        Output Safety Check                               │
│                │                                         │
│                ▼                                         │
│     Structured JSON Response                             │
└──────────────────────────────────────────────────────────┘
        │
        ▼
React Frontend (chat UI + voice input + TTS)
```

---

## Pipeline Deep Dive

### 1 — Hard Safety Rules
Before any AI runs, a deterministic keyword checker scans for red-flag symptoms (chest pain, breathing difficulty, unconsciousness, severe bleeding). If matched, the system immediately returns `critical` — the LLM cannot override this.

### 2 — Query Rewriting
Colloquial, multilingual input like *"kal se pet mein dard hai thoda"* is rewritten to clean medical terminology (*"mild abdominal pain since yesterday"*) before retrieval. This significantly improves embedding match quality.

### 3 — Hybrid RAG Retrieval
Two retrievers run simultaneously:
- **Dense retrieval** — `paraphrase-MiniLM-L3-v2` embeddings stored in Qdrant (HNSW index) for semantic matching
- **Sparse retrieval** — BM25 for exact keyword matching (drug names, symptom codes)

Results are fused using **Reciprocal Rank Fusion (RRF)** — a rank-based combination method that avoids score normalization issues.

### 4 — Parent Document Retrieval
Documents are indexed as small sentence-level child chunks (for precise retrieval) but when a child matches, the full parent section is fetched to give the LLM broader context.

### 5 — Cross-Encoder Reranking
Top fused candidates are rescored by `cross-encoder/ms-marco-MiniLM-L-6-v2`, which evaluates (query, document) pairs jointly — far more accurate than the bi-encoder used for retrieval.

### 6 — Confidence-Gated Web Fallback
If the reranker's top score falls below a threshold, the system falls back to a live Groq web search rather than forcing low-quality local context. Web results are explicitly flagged to the LLM as unverified.

### 7 — Output Safety Guardrail
The LLM's response passes a second safety check before returning — scanning for diagnostic language or unsafe claims. If triggered, a safe redirect replaces the response.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | LLaMA 3.3-70B via Groq API |
| **Embeddings** | `paraphrase-MiniLM-L3-v2` (sentence-transformers) |
| **Vector DB** | Qdrant (local file mode or Docker container) |
| **Reranker** | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| **Sparse Retrieval** | BM25 (rank-bm25) |
| **Backend** | FastAPI + Uvicorn |
| **Frontend** | React 18 + Vite |
| **Voice I/O** | Web Speech API (STT) + SpeechSynthesis (TTS) |
| **Containerisation** | Docker + Docker Compose |

---

## Project Structure

```
SehatSaathi/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app + lifespan startup
│   │   ├── routers/
│   │   │   └── triage.py            # POST /api/triage
│   │   ├── services/
│   │   │   ├── llm_service.py       # Triage orchestration + pipeline timings
│   │   │   ├── rag_service.py       # Hybrid RAG + reranking + timings
│   │   │   ├── query_service.py     # Query rewriting
│   │   │   ├── safety_service.py    # Input + output safety checks
│   │   │   ├── web_search_service.py# Web search fallback
│   │   │   └── evaluation_service.py# Evaluation helpers
│   │   └── models/
│   │       └── schemas.py           # Pydantic request/response schemas
│   ├── data/
│   │   ├── guidelines/              # WHO, ICMR, AYUSH, First Aid text files
│   │   ├── rag_index/               # Serialised chunks + parent store
│   │   └── qdrant/                  # Local Qdrant vector files
│   ├── evaluation/
│   │   ├── test_cases.json          # Labelled test questions
│   │   ├── evaluate.py              # Accuracy, latency, precision, recall
│   │   ├── metrics.py               # Metric functions
│   │   ├── confusion.py             # Confusion matrix builder
│   │   ├── charts.py                # Accuracy, latency, confidence charts
│   │   └── report.html              # Evaluation dashboard
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Landing.jsx          # Hero + typewriter + feature cards
│   │   │   └── Home.jsx             # Chat interface + TTS toggle
│   │   └── components/
│   │       ├── ChatBubble.jsx       # Message bubble + source indicator
│   │       ├── TriageCard.jsx       # Urgency verdict card
│   │       └── VoiceInput.jsx       # Mic button + Web Speech API
│   ├── index.html
│   └── vite.config.js
├── docker-compose.yml
├── Dockerfile
└── .env                             # GROQ_API_KEY, GROQ_MODEL, QDRANT_HOST
```

---

## Quickstart

### Option A — Docker (recommended)

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/SehatSaathi.git
cd SehatSaathi

# 2. Create .env file
cp .env.example .env
# Add your GROQ_API_KEY to .env

# 3. Start everything
docker compose up --build
```

Open `http://localhost:5173` — the full app is running.

> **First run** takes 5–10 minutes to build images and download ML models (~200 MB). Every subsequent start is under 30 seconds.

### Option B — Local Development

**Backend:**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend** (separate terminal):
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

---

## Environment Variables

Create a `.env` file at the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
QDRANT_HOST=local
```

| Variable | Description | Default |
|---|---|---|
| `GROQ_API_KEY` | Groq API key — get one free at [console.groq.com](https://console.groq.com) | required |
| `GROQ_MODEL` | Groq model name | `llama-3.3-70b-versatile` |
| `QDRANT_HOST` | `local` for file-based Qdrant, `qdrant` inside Docker | `local` |

---

## API Reference

### `POST /api/triage`

Request:
```json
{
  "conversation": [
    {"role": "user", "content": "I have had a fever for 3 days"}
  ],
  "language": "en"
}
```

Response:
```json
{
  "reply": "How high is the fever and do you have any other symptoms?",
  "urgency": "unclear",
  "is_final": false,
  "source": "medical_guideline_rag",
  "confidence": 0.87,
  "retrieved_sources": ["who_triage.txt"],
  "pipeline_timings": {
    "safety": 0.0001,
    "rewrite": 0.31,
    "rag": 0.82,
    "llm": 2.94,
    "total": 4.07
  }
}
```

### `GET /`
Health check — returns `{"message": "SehatSaathi API running"}`.

---

## Voice Features

- **Speech-to-text** — browser Web Speech API; tap the mic, speak your symptom, it auto-sends
- **Text-to-speech** — AI replies are read aloud automatically; language detected from unicode range (Devanagari → `hi-IN`, Tamil → `ta-IN`, Bengali → `bn-IN`, default → `en-IN`)
- **Mute toggle** — speaker icon in the chat header
- **Chrome only** — Web Speech API is not supported in Firefox or Safari

---

## Medical Disclaimer

> SehatSaathi provides **triage guidance only** — it is not a diagnostic tool and does not replace professional medical advice. Always consult a qualified healthcare professional for diagnosis and treatment. In an emergency, call **112**.

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

<div align="center">
Built for the <strong>Stellan AI Buildathon</strong> · Made with care for rural India
</div>
