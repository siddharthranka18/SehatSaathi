# SehatSaathi

A concise AI-powered medical triage assistant. SehatSaathi uses a retrieval-augmented-generation (RAG) pipeline plus a safety layer to provide urgency guidance (home_care, visit_phc, critical) based on curated medical guidelines and optional web fallback.

---

**Highlights**
- Python FastAPI backend serving a triage API
- Retrieval from curated medical guidelines (BM25 / dense + reranker)
- Safety override and output guardrails
- Groq LLM integration for structured JSON responses
- Optional Qdrant vector store for indexing medical guideline chunks
- Simple React + Vite frontend

---

**Repository Layout**
- `backend/` — FastAPI app, services, routers, models and ML/RAG logic
	- `backend/app/main.py` — application entry (FastAPI app, startup warmup)
	- `backend/app/routers/triage.py` — `/api/triage` endpoint
	- `backend/app/services/` — RAG, LLM, safety, query rewrite, web fallback, TTS, etc.
	- `backend/requirements.txt` — Python dependencies
- `data/guidelines/` — curated medical guideline text files used for retrieval
- `backend/data/rag_index/` and `backend/data/qdrant/` — local stored indexes and metadata
- `frontend/` — React + Vite single-page app (dev server on 5173)
- `docker-compose.yml` — quick start using Docker (qdrant, backend, frontend)

---

Quick Overview
- API base: `GET /` and `GET /health`
- Triage endpoint: `POST /api/triage` — accepts a conversation payload and returns a JSON object with `reply`, `urgency`, `is_final`, and pipeline metadata.

Example request shape (conversation-style messages):

```json
{
	"conversation": [
		{"role": "user", "content": "I have chest pain and shortness of breath"}
	]
}
```

Example (partial) response:

```json
{
	"reply": "This may be an emergency. Seek immediate care.",
	"urgency": "critical",
	"is_final": true
}
```

---

Getting started (local development)

Prerequisites
- Python 3.11
- Node 18+ / npm or yarn
- (Optional) Docker & Docker Compose

Backend (local)

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies and run the API:

```powershell
cd backend
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

3. Environment variables
- Copy or create a `.env` file at the repository root or `backend/` directory. Common variables:
	- `GROQ_API_KEY` — Groq (LLM) API key
	- `GROQ_MODEL` — model to use (e.g. `llama-3.3-70b-versatile`)
	- `QDRANT_HOST` — host for Qdrant if used (docker-compose sets `qdrant`)
	- `FAST_DEV=1` — skip heavy ML model loads and use BM25-only retrieval for fast dev cycles

Frontend (local)

```powershell
cd frontend
npm install
npm run dev
```

The frontend dev server expects the backend at `http://localhost:8000` by default. Update `VITE_API_URL` in the environment if needed.

---

Docker / Production

Quick start with Docker Compose (builds backend & frontend, runs Qdrant):

```powershell
docker compose up --build
```

The `docker-compose.yml` included launches:
- `qdrant` (vector store) on port `6333`
- `backend` on port `8000`
- `frontend` on port `5173`

See `docker-compose.yml` for volumes and env mappings.

---

Data & Indexing
- Curated clinical guideline text files are in `data/guidelines/` — these are the primary source used for retrieval.
- A sample local RAG index and threshold settings are under `backend/data/rag_index/` and `backend/data/qdrant/`.

Indexing / re-build utilities
- The repo includes helper scripts in `backend/` for (re)building and testing indexes. Review `backend/rebuild_store.py` and `backend/rebuild_and_test_rag.py` for details.

---

Design notes
- Retrieval-first architecture: queries are rewritten, run through a retrieval pass (BM25 + optional dense + reranker) and then combined with verified context to produce a constrained JSON response from the LLM.
- Safety: there are two safety layers — an early `safety_override` (detects urgent red flags in user text) and an output guardrail that prevents harmful or disallowed content in the final reply.
- Fast dev mode: setting `FAST_DEV=1` disables heavy ML model warmup and runs a BM25-only retrieval path for quicker testing.

---

Testing & evaluation
- Evaluation scripts and tuning utilities exist under `backend/evaluation/` (metrics, confusion, tuning reports).

---

Contributing
- Please open issues or PRs for bugs and improvements.
- For model, retrieval or safety changes, include tests or evaluation runs demonstrating behavior changes.

---

Contact
- Project maintained in this repository. For questions about running locally or Docker, open an issue.

