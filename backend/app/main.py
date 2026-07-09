import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import triage
from app.services.rag_service import (
    load_into_memory,
    get_embedding_model,
    get_reranker,
    is_fast_dev,
)


def _warmup_models():
    """Runs in a background thread — only when FAST_DEV is NOT set."""
    try:
        print("Background warmup: loading embedding model...")
        get_embedding_model()
        print("Background warmup: loading reranker...")
        get_reranker()
        print("Background warmup complete. All requests will now be fast.")
    except Exception as exc:
        import traceback
        print(f"[WARMUP ERROR] {type(exc).__name__}: {exc}")
        traceback.print_exc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("SehatSaathi backend starting...")
    load_into_memory()
    if is_fast_dev():
        print("FAST_DEV=1: ML models skipped. BM25-only mode active. Server ready.")
    else:
        print("Server ready. Warming up ML models in background...")
        # NOTE: daemon=False (default) — lets thread finish even if main thread is idle.
        # daemon=True would allow Windows to kill the thread mid-import (torch DLL load),
        # causing a silent crash with no traceback.
        threading.Thread(target=_warmup_models).start()
    yield

app = FastAPI(
    title="SehatSaathi API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(triage.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "SehatSaathi API running"}


@app.get("/health")
def health():
    return {"status": "ok"}
