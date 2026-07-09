# SehatSaathi

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](docker-compose.yml)

A concise AI-powered medical triage assistant. SehatSaathi uses a retrieval-augmented-generation (RAG) pipeline plus a safety layer to provide urgency guidance (home_care, visit_phc, critical) based on curated medical guidelines and optional web fallback.

---

<!-- Hero -->
## 
<p align="center">
	<img alt="SehatSaathi" src="https://img.shields.io/badge/SehatSaathi-Healthcare%20Assistant-orange?logo=healthicons&logoColor=white" />
	<br/>
	<em>An explainable, retrieval-first medical triage assistant</em>
</p>

---

**Highlights**
- Python FastAPI backend serving a triage API
- Retrieval from curated medical guidelines (BM25 / dense + reranker)
- Safety override and output guardrails
- Groq LLM integration for structured JSON responses
- Optional Qdrant vector store for indexing medical guideline chunks
- Simple React + Vite frontend

---

**Architecture (overview)**

```mermaid
flowchart LR
	User[User (Web / Voice)] -->|POST /api/triage| Frontend[Frontend (React + Vite)]
	Frontend --> Backend[Backend (FastAPI)]
	Backend --> RAG[RAG Retriever]
	RAG --> Qdrant[Qdrant / BM25 Index]
	Backend --> LLM[Groq LLM]
	Backend --> Safety[Safety Layer]
	Backend --> WebFallback[Web Search Fallback]
	LLM -->|JSON reply| Backend
	Backend -->|response| Frontend
```

This diagram highlights the retrieval-first flow: the backend rewrites the query, retrieves context from local guideline indexes (or web fallback), runs a constrained LLM call, and applies output safety before returning a structured JSON reply.

---

**Screenshots / Visuals**

Add screenshots to `assets/` and reference them here for a polished README. Example placeholders:

![Screenshot 1](assets/screenshot-1.png)
![Screenshot 2](assets/screenshot-2.png)

To add your own screenshots:

1. Create an `assets/` folder in the repo root.
2. Add `screenshot-1.png` and `screenshot-2.png` (or update filenames below).
3. Commit the images. The README will render them on GitHub.

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

