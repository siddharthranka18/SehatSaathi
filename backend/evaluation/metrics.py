"""
Evaluation Metrics Collector for SehatSaathi

Accumulates model evaluation results across accuracy categories, latencies, 
confidence trends, and granular retrieval framework statistics.
"""

from collections import defaultdict
from statistics import mean


class EvaluationMetrics:
    def __init__(self):
        self.pairs = []
        self.latencies = []
        self.confidences = []
        
        self.correct = 0
        self.total = 0
        
        self.rag_used = 0
        self.web_used = 0
        
        self.total_times = []

        # 1. Advanced Evaluation Metric Containers Setup
        # Retrieval statistics
        self.dense_hits = []
        self.bm25_hits = []
        self.parent_hits = []
        self.retrieved_chunks = []

        # Conversation statistics
        self.turn_counts = []

        # Confidence statistics
        self.rag_confidence_count = 0
        self.web_fallback_count = 0

        # Sources used
        self.guideline_sources = defaultdict(int)

    # 2. Synchronized add_result signature matching evaluate.py parameters
    def add_result(
        self,
        expected,
        predicted,
        latency,
        source,
        confidence,
        json_ok=True,
        pipeline_timings=None,
        rag_timings=None,
        dense_hits=0,
        bm25_hits=0,
        parent_hits=0,
        retrieved_chunks=0,
        retrieved_sources=None,
        rag_confident=False,
        conversation_turns=0,
    ):
        self.total += 1
        if expected == predicted:
            self.correct += 1
            
        if source == "medical_guideline_rag":
            self.rag_used += 1
        elif source == "web_fallback":
            self.web_used += 1

        self.pairs.append((expected, predicted))
        self.latencies.append(latency)
        self.confidences.append(confidence)

        # 3. Dynamic Telemetry Metric Append Matrix
        self.dense_hits.append(dense_hits)
        self.bm25_hits.append(bm25_hits)
        self.parent_hits.append(parent_hits)
        self.retrieved_chunks.append(retrieved_chunks)

        self.turn_counts.append(conversation_turns)

        if rag_confident:
            self.rag_confidence_count += 1
        else:
            self.web_fallback_count += 1

        if retrieved_sources:
            for src in retrieved_sources:
                self.guideline_sources[src] += 1

    def average_latency(self):
        return round(mean(self.latencies), 3) if self.latencies else 0

    # 4. Math calculation modules for processing RAG execution matrices
    def average_dense_hits(self):
        return round(mean(self.dense_hits), 2) if self.dense_hits else 0

    def average_bm25_hits(self):
        return round(mean(self.bm25_hits), 2) if self.bm25_hits else 0

    def average_parent_hits(self):
        return round(mean(self.parent_hits), 2) if self.parent_hits else 0

    def average_chunks(self):
        return round(mean(self.retrieved_chunks), 2) if self.retrieved_chunks else 0

    def average_turns(self):
        return round(mean(self.turn_counts), 2) if self.turn_counts else 0

    def report(self):
        accuracy = round((self.correct / self.total) * 100, 2) if self.total else 0
        
        # Base classification performance matrix tracking configuration
        base_report = {
            "accuracy": accuracy,
            "total_cases": self.total,
            "rag_cases": self.rag_used,
            "web_cases": self.web_used,
            "mean_latency_seconds": self.average_latency(),
        }

        # 5. Injection of comprehensive operational evaluation elements
        base_report.update({
            "average_dense_hits": self.average_dense_hits(),
            "average_bm25_hits": self.average_bm25_hits(),
            "average_parent_hits": self.average_parent_hits(),
            "average_retrieved_chunks": self.average_chunks(),
            "average_conversation_turns": self.average_turns(),
            
            "rag_confident_cases": self.rag_confidence_count,
            "web_fallback_cases": self.web_fallback_count,
            
            "guideline_usage": dict(self.guideline_sources),
        })

        return base_report