"""
Production RAG pipeline for SehatSaathi

Offline:
    python -m app.services.rag_service

Runtime:
    retrieve_context(query)

Pipeline:

Documents
    ↓
Parent-child chunking
    ↓
Embeddings
    ↓
Qdrant(HNSW) + BM25

Query
    ↓
Dense Search + Sparse Search
    ↓
RRF Fusion
    ↓
Parent Retrieval
    ↓
Cross Encoder Reranking
    ↓
Medical Context
"""

import os
import json
import uuid
import glob
from pathlib import Path

import numpy as np

from rank_bm25 import BM25Okapi

from sentence_transformers import (
    SentenceTransformer,
    CrossEncoder
)

from qdrant_client import QdrantClient

from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)


# ==========================
# PATH CONFIG
# ==========================

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

GUIDELINES_DIR = BASE_DIR / "backend/data/guidelines"

INDEX_DIR = BASE_DIR / "backend/data/rag_index"


# ==========================
# MODELS
# ==========================


COLLECTION_NAME = "medical_guidelines"

CONFIDENCE_THRESHOLD = 0.35


embedding_model = None

reranker_model = None


# ==========================
# DATABASES
# ==========================


qdrant = QdrantClient(
    host="localhost",
    port=6333
)


bm25_index = None


# child chunks
chunks = []


# parent storage
parent_docs = {}



# ==========================
# MODEL LOADERS
# ==========================


def get_embedding_model():

    global embedding_model

    if embedding_model is None:

        embedding_model = SentenceTransformer(
          "all-MiniLM-L6-v2"
        )

    return embedding_model



def get_reranker():

    global reranker_model


    if reranker_model is None:

        reranker_model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )


    return reranker_model



# ==========================
# PARENT DOCUMENT CHUNKING
# ==========================


def create_parent_child_chunks(
        text:str,
        source:str
):

    """
    Parent Document Retrieval

    Parent:
        Full medical section

    Child:
        Smaller searchable units
    """


    results=[]


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



            results.append({

                "text":sentence,

                "parent_id":parent_id,

                "source":source

            })


    return results



# ==========================
# BUILD INDEX
# ==========================


def build_index():


    global chunks
    global bm25_index


    all_child_chunks=[]



    print("Building medical RAG index...")


    # recreate qdrant collection

    qdrant.recreate_collection(

        collection_name=COLLECTION_NAME,


        vectors_config=VectorParams(

            size=384,

            distance=Distance.COSINE

        )

    )


    model=get_embedding_model()


    points=[]



    files=glob.glob(
        str(GUIDELINES_DIR / "*.txt")
    )



    for filepath in files:


        with open(
            filepath,
            encoding="utf-8"
        ) as f:


            text=f.read()



        child_chunks=create_parent_child_chunks(

            text,

            os.path.basename(filepath)

        )



        all_child_chunks.extend(
            child_chunks
        )



    texts=[
        c["text"]
        for c in all_child_chunks
    ]



    embeddings=model.encode(

        texts,

        normalize_embeddings=True

    )



    for chunk,vector in zip(
            all_child_chunks,
            embeddings
    ):


        points.append(

            PointStruct(

                id=str(uuid.uuid4()),

                vector=vector.tolist(),


                payload={

                    "text":
                    chunk["text"],


                    "parent_id":
                    chunk["parent_id"],


                    "source":
                    chunk["source"]

                }

            )

        )



    qdrant.upsert(

        collection_name=COLLECTION_NAME,

        points=points

    )



    # BM25 sparse index


    tokenized=[

        t.lower().split()

        for t in texts

    ]



    bm25_index=BM25Okapi(
        tokenized
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


        json.dump({

            "chunks":
            all_child_chunks,


            "parents":
            parent_docs

        },f)



    print(
        f"Indexed {len(all_child_chunks)} child chunks"
    )



# ==========================
# LOAD LOCAL STORAGE
# ==========================


def load_storage():

    global chunks
    global parent_docs
    global bm25_index



    if chunks:
        return



    with open(
        INDEX_DIR/"store.json",
        encoding="utf-8"

    ) as f:


        data=json.load(f)



    chunks=data["chunks"]

    parent_docs=data["parents"]



    tokenized=[

        c["text"].lower().split()

        for c in chunks

    ]


    bm25_index=BM25Okapi(
        tokenized
    )



# ==========================
# RRF
# ==========================


def reciprocal_rank_fusion(
        lists,
        k=60
):


    scores={}



    for ranking in lists:


        for rank,item in enumerate(ranking):


            scores[item]=(

                scores.get(
                    item,
                    0
                )

                +

                1/(k+rank+1)

            )



    return sorted(

        scores,

        key=scores.get,

        reverse=True

    )



# ==========================
# RETRIEVAL
# ==========================


def retrieve_context(
        query:str,
        top_k:int=5
):


    """
    Runtime RAG retrieval

    Hybrid:
    Qdrant Vector Search
    +
    BM25

    Then:

    Parent Retrieval

    Then:

    Cross Encoder Rerank
    """



    load_storage()


    model=get_embedding_model()


    query_vector=model.encode(

        query,

        normalize_embeddings=True

    )



    # Dense retrieval

    dense_results=qdrant.search(

        collection_name=COLLECTION_NAME,

        query_vector=query_vector,

        limit=20

    )



    dense_ids=[

        r.payload["text"]

        for r in dense_results

    ]



    # Sparse BM25 retrieval


    bm25_scores=bm25_index.get_scores(

        query.lower().split()

    )



    bm25_indices=np.argsort(

        bm25_scores

    )[::-1][:20]



    sparse_results=[

        chunks[i]["text"]

        for i in bm25_indices

    ]



    # Fusion


    fused=reciprocal_rank_fusion(

        [

            dense_ids,

            sparse_results

        ]

    )



    # Parent retrieval


    parent_context=[]


    for child_text in fused[:10]:


        for c in chunks:


            if c["text"]==child_text:


                parent_context.append(

                    parent_docs[
                        c["parent_id"]
                    ]["text"]

                )


    # remove duplicates

    parent_context=list(
        set(parent_context)
    )



    # Cross Encoder rerank


    reranker=get_reranker()


    pairs=[

        (query,ctx)

        for ctx in parent_context

    ]



    scores=reranker.predict(
        pairs
    )



    ranked=sorted(

        zip(parent_context,scores),

        key=lambda x:x[1],

        reverse=True

    )



    final=[

        r[0]

        for r in ranked[:top_k]

    ]



    top_score=(

        float(ranked[0][1])

        if ranked

        else 0

    )



    return {


        "chunks":final,


        "top_score":top_score,


        "confident":

            top_score
            >
            CONFIDENCE_THRESHOLD

    }



# ==========================
# OFFLINE RUN
# ==========================


if __name__=="__main__":

    build_index()