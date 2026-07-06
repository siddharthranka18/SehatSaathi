from pydantic import BaseModel, Field, ConfigDict
from typing import List, Literal, Dict, Any

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class TriageRequest(BaseModel):
    conversation: List[Message]
    language: str = "en"


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

    retrieval_stats: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed retrieval statistics"
    )

    conversation_turns: int = Field(
        default=0,
        description="Number of conversation turns"
    )
