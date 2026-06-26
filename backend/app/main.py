from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import triage

from app.services.rag_service import (
    INDEX_DIR,
    build_index,
    load_index,
    get_embedding_model,
    get_reranker,
    get_qdrant,
    COLLECTION_NAME,
)


@asynccontextmanager
async def lifespan(app: FastAPI):

    print("SehatSaathi backend starting...")

    qdrant = get_qdrant()

    collections = [
        c.name
        for c in qdrant.get_collections().collections
    ]

    if COLLECTION_NAME not in collections:
        print("Qdrant collection not found.")
        print("Building RAG index...")
        build_index()
    else:
        print("Existing Qdrant collection found.")
        load_index()

    print("Pre-loading embedding model...")
    get_embedding_model()

    print("Pre-loading reranker...")
    get_reranker()

    print("All models loaded. Server ready.")

    yield


# ← this was missing entirely
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