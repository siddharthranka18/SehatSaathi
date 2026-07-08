from pydantic import BaseModel, Field, ConfigDict
from typing import List, Literal, Dict, Any

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class TriageRequest(BaseModel):
    conversation: List[Message]
    language: str = "en"


class RetrievalStats(BaseModel):
    model_config = ConfigDict(extra='allow')

    query: str = Field(
        default="",
        description="Query used for retrieval"
    )

    candidate_chunks: int = Field(
        default=0,
        description="Number of candidate chunks considered"
    )

    parent_documents: int = Field(
        default=0,
        description="Number of parent documents after chunk-to-parent mapping"
    )

    reranked_documents: int = Field(
        default=0,
        description="Number of documents after reranking"
    )

    returned_documents: int = Field(
        default=0,
        description="Number of documents returned to the LLM"
    )


class TriageResponse(BaseModel):
    model_config = ConfigDict(extra='allow')
    
    reply: str
    urgency: str
    is_final: bool
    source: str

    # =========================
    # Evaluation Metrics
    # =========================

    confidence: float = Field(
        default=0.0,
        description="CrossEncoder confidence score"
    )

    retrieved_sources: List[str] = Field(
        default_factory=list,
        description="Guideline files used for retrieval"
    )

    pipeline_timings: Dict[str, float] = Field(
        default_factory=dict,
        description="Timing of each pipeline stage"
    )

    rag_timings: Dict[str, float] = Field(
        default_factory=dict,
        description="Detailed RAG timing breakdown"
    )

    dense_hits: int = Field(
        default=0,
        description="Number of dense retrieval candidates"
    )

    bm25_hits: int = Field(
        default=0,
        description="Number of BM25 retrieval candidates"
    )

    retrieved_chunks: int = Field(
        default=0,
        description="Number of parent chunks after fusion"
    )

    parent_hits: int = Field(
        default=0,
        description="Number of parent documents retrieved"
    )

    rewritten_query: str = Field(
        default="",
        description="LLM rewritten query used for retrieval"
    )

    rag_confident: bool = Field(
        default=False,
        description="Whether RAG confidence exceeded threshold"
    )

    retrieval_method: str = Field(
        default="",
        description="Hybrid RAG or Web Fallback"
    )

    context_length: int = Field(
        default=0,
        description="Number of characters passed to the LLM as context"
    )

    dense_scores: List[float] = Field(
        default_factory=list,
        description="Top dense retrieval similarity scores"
    )

    reranker_scores: List[float] = Field(
        default_factory=list,
        description="Top CrossEncoder reranker scores"
    )

    retrieval_stats: RetrievalStats = Field(
        default_factory=RetrievalStats,
        description="Detailed retrieval statistics"
    )

    conversation_turns: int = Field(
        default=0,
        description="Number of conversation turns"
    )
