from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import triage
from app.services.rag_service import (
    INDEX_DIR,
    build_index,
    load_index,           # ← was load_storage, correct name is load_index
    get_embedding_model,
    get_reranker,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("SehatSaathi backend starting...")
    store_path = INDEX_DIR / "store.json"
    if store_path.exists():
        print("Loading existing RAG index...")
        load_index()
        print("Pre-loading embedding model...")
        get_embedding_model()
        print("Pre-loading reranker...")
        get_reranker()
    else:
        print("First run — building RAG index...")
        build_index()
        get_embedding_model()
        get_reranker()
    print("All models loaded. Server ready.")
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