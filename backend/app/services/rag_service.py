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


CONFIDENCE_THRESHOLD = 0.35



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

    if _embedding_model is None:

        print("Loading embedding model")

        from sentence_transformers import (
            SentenceTransformer
        )

        _embedding_model = SentenceTransformer(
            EMBEDDING_MODEL_NAME
        )

        print("Embedding loaded")

    return _embedding_model





def get_reranker():

    global _reranker_model

    if _reranker_model is None:

        print("Loading reranker")

        from sentence_transformers import (
            CrossEncoder
        )

        _reranker_model = CrossEncoder(
            RERANKER_MODEL_NAME
        )

    return _reranker_model





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

            "chunks":all_chunks,

            "parents":parent_docs

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





# =============================
# RETRIEVE
# =============================


def retrieve_context(query, top_k=3):

    import time

    timings = {}
    total_start = time.perf_counter()

    load_index()

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
    dense_results = [
        p.payload["text"]
        for p in dense.points
    ]
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
    retrieved_sources_set = set()

    for text in fused:
        c = chunk_lookup.get(text)
        if c:
            parents.append(
                parent_docs[c["parent_id"]]["text"]
            )
            retrieved_sources_set.add(c.get("source", ""))

    parents = list(set(parents))
    timings["parent"] = round(time.perf_counter() - t0, 4)

    retrieved_sources = sorted(
        [s for s in retrieved_sources_set if s]
    )

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

    top_score = float(ranked[0][1])

    print("RAG SCORE:", top_score)

    return {
        "chunks": [
            x[0] for x in ranked[:top_k]
        ],
        "top_score": top_score,
        "confident": top_score > CONFIDENCE_THRESHOLD,
        "retrieved_sources": retrieved_sources,
        "dense_hits": len(dense_results),
        "bm25_hits": len(sparse),
        "parent_hits": len(parents),
        "retrieved_chunks": len(ranked[:top_k]),
        "timings": timings,
    }





if __name__=="__main__":

    build_index()