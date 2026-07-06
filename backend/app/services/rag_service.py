"""
Production RAG Service

Features:
- Qdrant Vector DB
- HNSW vector search
- Hybrid retrieval (Dense + BM25)
- Reciprocal Rank Fusion
- Parent document retrieval
- Cross encoder reranking
"""

import os
import json
import uuid
import glob
import threading

from pathlib import Path
from dotenv import load_dotenv

import numpy as np

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct
)

from rank_bm25 import BM25Okapi


print("RAG IMPORT COMPLETE - NO ML LOADED")


# =============================
# PATHS
# =============================

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")


GUIDELINES_DIR = (
    BASE_DIR /
    "data" /
    "guidelines"
)


INDEX_DIR = (
    BASE_DIR /
    "data" /
    "rag_index"
)


COLLECTION_NAME = "medical_guidelines"


EMBEDDING_MODEL_NAME = (
    "all-MiniLM-L6-v2"
)


RERANKER_MODEL_NAME = (
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


CONFIDENCE_THRESHOLD = -2

# Opt-in only: FAST_DEV=1 skips ML models and uses BM25-only retrieval.
def is_fast_dev() -> bool:
    return os.getenv("FAST_DEV", "").lower() in ("1", "true", "yes")


_model_lock = threading.Lock()
_models_ready = False
_models_warming = False



# =============================
# GLOBALS
# =============================


_embedding_model = None
_reranker_model = None
_qdrant = None
_bm25 = None

chunks = []
parent_docs = {}
chunk_lookup = {}



# =============================
# QDRANT
# =============================


def get_qdrant():

    global _qdrant

    if _qdrant is None:

        host = os.getenv(
            "QDRANT_HOST",
            "localhost"
        )

        print(
            "Connecting Qdrant:",
            host
        )

        if host == "local":
            # Use in-memory Qdrant for local dev (no Docker, no file lock issues)
            # Index is rebuilt from store.json via load_index()/build_index()
            print("Using in-memory Qdrant (local dev mode)")
            _qdrant = QdrantClient(":memory:")
        else:
            _qdrant = QdrantClient(
                host=host,
                port=6333
            )

    return _qdrant





# =============================
# MODELS
# =============================


def get_embedding_model():

    global _embedding_model

    if _embedding_model is not None:
        return _embedding_model

    with _model_lock:
        if _embedding_model is None:
            print("Loading embedding model")
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            print("Embedding loaded")

    return _embedding_model





def get_reranker():

    global _reranker_model

    if _reranker_model is not None:
        return _reranker_model

    with _model_lock:
        if _reranker_model is None:
            print("Loading reranker")
            from sentence_transformers import CrossEncoder
            _reranker_model = CrossEncoder(RERANKER_MODEL_NAME)
            print("Reranker loaded")

    return _reranker_model


def models_ready() -> bool:
    if is_fast_dev():
        return True
    return _embedding_model is not None and _reranker_model is not None


def warmup_models():
    """Load ML models in a background thread so startup stays fast."""
    global _models_ready, _models_warming

    if is_fast_dev():
        print("FAST_DEV=1: skipping ML model warmup.")
        _models_ready = True
        return

    with _model_lock:
        if _models_ready or _models_warming:
            return

    # Brief pause so the event loop can finish binding before heavy imports.
    threading.Event().wait(0.5)

    with _model_lock:
        if _models_ready or _models_warming:
            return
        _models_warming = True

    try:
        print("Background: loading embedding model...")
        get_embedding_model()
        print("Background: loading reranker...")
        get_reranker()
        _models_ready = True
        print("Background: full RAG pipeline ready (hybrid + reranker).")
    except Exception as exc:
        print(f"Background model warmup failed: {exc}")
    finally:
        with _model_lock:
            _models_warming = False





# =============================
# CHUNKING
# =============================


def create_parent_child_chunks(
        text,
        source
):

    result=[]

    sections=[
        s.strip()
        for s in text.split("\n\n")
        if s.strip()
    ]


    for section in sections:

        parent_id=str(uuid.uuid4())


        parent_docs[parent_id]={

            "text":section,

            "source":source

        }


        sentences=section.split(".")


        for sentence in sentences:


            sentence=sentence.strip()


            if len(sentence)<30:

                continue


            result.append({

                "text":sentence,

                "parent_id":parent_id,

                "source":source

            })


    return result





# =============================
# BUILD INDEX
# =============================


def build_index():

    global chunks
    global _bm25


    qdrant=get_qdrant()


    existing=[
        c.name
        for c in qdrant.get_collections().collections
    ]


    if COLLECTION_NAME in existing:

        qdrant.delete_collection(
            COLLECTION_NAME
        )


    qdrant.create_collection(

        collection_name=COLLECTION_NAME,

        vectors_config=VectorParams(

            size=384,

            distance=Distance.COSINE

        )

    )



    all_chunks=[]



    for file in glob.glob(
        str(GUIDELINES_DIR/"*.txt")
    ):

        with open(
            file,
            encoding="utf-8"
        ) as f:

            text=f.read()


        all_chunks.extend(

            create_parent_child_chunks(

                text,

                os.path.basename(file)

            )

        )



    if not all_chunks:

        raise RuntimeError(
            "No guideline documents found"
        )



    texts=[
        c["text"]
        for c in all_chunks
    ]



    embeddings=get_embedding_model().encode(

        texts,

        normalize_embeddings=True

    )



    points=[]


    for chunk,vector in zip(
        all_chunks,
        embeddings
    ):


        points.append(

            PointStruct(

                id=str(uuid.uuid4()),

                vector=vector.tolist(),

                payload=chunk

            )

        )



    qdrant.upsert(

        collection_name=COLLECTION_NAME,

        points=points

    )


    _bm25=BM25Okapi(

        [
            t.lower().split()
            for t in texts
        ]

    )



    INDEX_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    with open(
        INDEX_DIR/"store.json",
        "w",
        encoding="utf-8"
    ) as f:


        json.dump(

            {

            "chunks": all_chunks,

            "parents": parent_docs,

            "vectors": embeddings.tolist()

            },

            f

        )


    print(
        f"Indexed {len(all_chunks)} chunks"
    )





# =============================
# LOAD
# =============================


def load_index():

    global chunks
    global parent_docs
    global chunk_lookup
    global _bm25


    if chunks:

        return


    with open(
        INDEX_DIR/"store.json",
        encoding="utf-8"
    ) as f:

        data=json.load(f)


    chunks=data["chunks"]

    parent_docs=data["parents"]


    chunk_lookup={

        c["text"]:c

        for c in chunks

    }


    _bm25=BM25Okapi(

        [
            c["text"].lower().split()
            for c in chunks
        ]


    )




def _load_store_metadata(data):
    global chunks, parent_docs, chunk_lookup, _bm25

    chunks = data["chunks"]
    parent_docs = data["parents"]
    chunk_lookup = {c["text"]: c for c in chunks}
    _bm25 = BM25Okapi([c["text"].lower().split() for c in chunks])


def _collection_populated(qdrant) -> bool:
    existing = [c.name for c in qdrant.get_collections().collections]
    if COLLECTION_NAME not in existing:
        return False
    info = qdrant.get_collection(COLLECTION_NAME)
    return info.points_count > 0


def _upsert_store_vectors(qdrant, data):
    texts = [c["text"] for c in chunks]
    saved_vectors = data.get("vectors")

    existing = [c.name for c in qdrant.get_collections().collections]
    if COLLECTION_NAME in existing:
        qdrant.delete_collection(COLLECTION_NAME)
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

    if saved_vectors:
        print(f"Using cached vectors ({len(saved_vectors)}). Skipping re-encoding.")
        vectors = saved_vectors
    else:
        print(f"No cached vectors found. Re-encoding {len(texts)} chunks...")
        vectors = get_embedding_model().encode(texts, normalize_embeddings=True).tolist()

    points = [
        PointStruct(id=str(uuid.uuid4()), vector=vec, payload=chunk)
        for chunk, vec in zip(chunks, vectors)
    ]
    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Qdrant ready with {len(points)} vectors.")


def startup():
    """
    Fast index setup at boot — cached vectors, no ML models loaded.
    Full hybrid RAG (dense + BM25 + RRF + reranker) loads in background.
    """
    print("Loading RAG index...")

    store_path = INDEX_DIR / "store.json"
    if not store_path.exists():
        print("store.json not found — running full build_index() instead.")
        build_index()
        return

    with open(store_path, encoding="utf-8") as f:
        data = json.load(f)

    _load_store_metadata(data)
    qdrant = get_qdrant()
    host = os.getenv("QDRANT_HOST", "localhost")

    if host != "local" and _collection_populated(qdrant):
        info = qdrant.get_collection(COLLECTION_NAME)
        print(f"Remote Qdrant ready ({info.points_count} vectors). Skipping re-upsert.")
        return

    if host == "local":
        print("Populating in-memory Qdrant from store.json...")
    else:
        print("Remote Qdrant empty — seeding from store.json...")

    _upsert_store_vectors(qdrant, data)


def load_into_memory():
    """Backward-compatible alias for startup()."""
    startup()



# =============================
# RRF
# =============================


def rrf(results):

    scores={}


    for ranking in results:

        for i,item in enumerate(ranking):

            scores[item]=(

                scores.get(item,0)

                +

                1/(60+i)

            )


    return sorted(

        scores,

        key=scores.get,

        reverse=True

    )





def _retrieve_bm25_only(query, top_k, timings, total_start):
    """Fast local dev path — no embedding model or reranker required."""
    import time
    import numpy as np

    t0 = time.perf_counter()
    bm25_scores = _bm25.get_scores(query.lower().split())
    ranked_indices = np.argsort(bm25_scores)[::-1]
    sparse = [chunks[i]["text"] for i in ranked_indices[:10]]
    timings["embedding"] = 0.0
    timings["dense"] = 0.0
    timings["bm25"] = round(time.perf_counter() - t0, 4)
    timings["rrf"] = 0.0

    t0 = time.perf_counter()
    parents = []
    parent_scores = {}
    for idx in ranked_indices[:20]:
        chunk = chunks[idx]
        parent_text = parent_docs[chunk["parent_id"]]["text"]
        score = float(bm25_scores[idx])
        if parent_text not in parent_scores or score > parent_scores[parent_text]:
            parent_scores[parent_text] = score
        if parent_text not in parents:
            parents.append(parent_text)
    timings["parent"] = round(time.perf_counter() - t0, 4)

    if not parents:
        timings["reranker"] = 0.0
        timings["total"] = round(time.perf_counter() - total_start, 4)
        return {
            "chunks": [],
            "top_score": 0,
            "confident": False,
            "retrieved_sources": [],
            "dense_hits": 0,
            "bm25_hits": len(sparse),
            "parent_hits": 0,
            "retrieved_chunks": 0,
            "dense_scores": [],
            "reranker_scores": [],
            "retrieval_stats": {
                "query": query,
                "candidate_chunks": len(sparse),
                "parent_documents": 0,
                "reranked_documents": 0,
                "returned_documents": 0,
            },
            "timings": timings,
        }

    ranked = sorted(parent_scores.items(), key=lambda x: x[1], reverse=True)
    top_score = float(ranked[0][1])
    timings["reranker"] = 0.0
    timings["total"] = round(time.perf_counter() - total_start, 4)

    top_sources = []
    for parent, _ in ranked[:top_k]:
        for doc in parent_docs.values():
            if doc["text"] == parent:
                top_sources.append(doc["source"])
                break
    top_sources = list(dict.fromkeys(top_sources))
    reranker_scores = [float(score) for _, score in ranked[:top_k]]

    return {
        "chunks": [text for text, _ in ranked[:top_k]],
        "top_score": top_score,
        "confident": top_score > 0,
        "retrieved_sources": top_sources,
        "dense_hits": 0,
        "bm25_hits": len(sparse),
        "parent_hits": len(parents),
        "retrieved_chunks": len(ranked[:top_k]),
        "dense_scores": [],
        "reranker_scores": [],          # BM25 scores ≠ reranker scores — keep honest
        "retrieval_method": "BM25 Only (FAST_DEV=1)",  # explicit — never pretend it was Hybrid
        "retrieval_stats": {
            "query": query,
            "candidate_chunks": len(sparse),
            "parent_documents": len(parents),
            "reranked_documents": len(ranked),
            "returned_documents": len(ranked[:top_k]),
        },
        "timings": timings,
    }





# =============================
# RETRIEVE
# =============================


def retrieve_context(query, top_k=3):
    import time
    import numpy as np

    timings = {}
    total_start = time.perf_counter()

    load_index()

    if is_fast_dev():
        return _retrieve_bm25_only(query, top_k, timings, total_start)

    # --- Embedding ---
    t0 = time.perf_counter()
    vector = get_embedding_model().encode(
        query,
        normalize_embeddings=True
    )
    timings["embedding"] = round(time.perf_counter() - t0, 4)

    # --- Dense retrieval ---
    t0 = time.perf_counter()
    dense = get_qdrant().query_points(
        collection_name=COLLECTION_NAME,
        query=vector.tolist(),
        limit=10
    )
    
    # Track explicit dense payload strings and raw scores concurrently
    dense_results = []
    dense_scores = []
    for point in dense.points:
        dense_results.append(point.payload["text"])
        dense_scores.append(float(point.score))
        
    timings["dense"] = round(time.perf_counter() - t0, 4)

    # --- BM25 retrieval ---
    t0 = time.perf_counter()
    bm25_scores = _bm25.get_scores(
        query.lower().split()
    )
    sparse = [
        chunks[i]["text"]
        for i in np.argsort(bm25_scores)[::-1][:10]
    ]
    timings["bm25"] = round(time.perf_counter() - t0, 4)

    # --- RRF ---
    t0 = time.perf_counter()
    fused = rrf([dense_results, sparse])
    timings["rrf"] = round(time.perf_counter() - t0, 4)

    # --- Parent retrieval ---
    t0 = time.perf_counter()
    parents = []

    for text in fused:
        c = chunk_lookup.get(text)
        if c:
            parents.append(
                parent_docs[c["parent_id"]]["text"]
            )

    parents = list(set(parents))
    timings["parent"] = round(time.perf_counter() - t0, 4)

    # Guard condition if no parent documents are retrieved
    if not parents:
        timings["reranker"] = 0.0
        timings["total"] = round(
            time.perf_counter() - total_start, 4
        )
        return {
            "chunks": [],
            "top_score": 0,
            "confident": False,
            "retrieved_sources": [],
            "dense_hits": len(dense_results),
            "bm25_hits": len(sparse),
            "parent_hits": 0,
            "retrieved_chunks": 0,
            "dense_scores": [],
            "reranker_scores": [],
            "retrieval_stats": {
                "query": query,
                "candidate_chunks": len(fused),
                "parent_documents": 0,
                "reranked_documents": 0,
                "returned_documents": 0
            },
            "timings": timings,
        }

    # --- Cross-encoder reranking ---
    t0 = time.perf_counter()
    scores = get_reranker().predict(
        [(query, p) for p in parents]
    )

    ranked = sorted(
        zip(parents, scores),
        key=lambda x: x[1],
        reverse=True
    )
    timings["reranker"] = round(time.perf_counter() - t0, 4)

    timings["total"] = round(
        time.perf_counter() - total_start, 4
    )
    print("Ranked length:", len(ranked))
    print("Ranked sample:", ranked[:3])
    top_score = float(ranked[0][1])

    # 1. Map reranked parent documents back to their source files safely
    top_sources = []
    for parent, _ in ranked[:top_k]:
        for pid, doc in parent_docs.items():
            if doc["text"] == parent:
                top_sources.append(doc["source"])
                break
    top_sources = list(dict.fromkeys(top_sources))

    # 2. Package cross-encoder evaluation scores array safely
    print(">>> BEFORE creating reranker_scores")

    reranker_scores = []

    for _, score in ranked[:top_k]:
        reranker_scores.append(float(score))

    print(">>> AFTER creating reranker_scores")
    print(">>> VALUE:", reranker_scores)

    # Debug print block now executes after resolving dependent list assignments
    print("\n========== RAG DEBUG ==========")
    print("Query:", query)
    print("Dense hits:", len(dense_results))
    print("BM25 hits:", len(sparse))
    print("Parent docs:", len(parents))
    print("Returned docs:", len(ranked[:top_k]))
    print("Dense scores:", dense_scores[:5])
    print("Reranker scores:", reranker_scores)
    print("Top score:", top_score)
    print("Threshold:", CONFIDENCE_THRESHOLD)
    print("Confident:", top_score > CONFIDENCE_THRESHOLD)
    print("Sources:", top_sources)
    print("===============================\n")

    print("RAG SCORE:", top_score)

    # 4. Return unified contextual execution payload dictionary
    return {
        "chunks": [
            x[0] for x in ranked[:top_k]
        ],
        "top_score": top_score,
        "confident": top_score > CONFIDENCE_THRESHOLD,
        "retrieved_sources": top_sources,
        "dense_hits": len(dense_results),
        "bm25_hits": len(sparse),
        "parent_hits": len(parents),
        "retrieved_chunks": len(ranked[:top_k]),
        "dense_scores": dense_scores,
        "reranker_scores": reranker_scores,
        "retrieval_stats": {
            "query": query,
            "candidate_chunks": len(fused),
            "parent_documents": len(parents),
            "reranked_documents": len(ranked),
            "returned_documents": len(ranked[:top_k])
        },
        "timings": timings
    }



if __name__=="__main__":

    build_index()