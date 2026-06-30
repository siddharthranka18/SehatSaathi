"""
Evaluation Metrics Module

Provides functions for accuracy, precision, recall, F1,
latency, confidence, and source usage stats.
"""

from statistics import mean
from collections import defaultdict


LABELS = ["home_care", "visit_phc", "critical"]


class EvaluationMetrics:

    def __init__(self):
        self.total = 0
        self.correct = 0
        self.rag_used = 0
        self.web_used = 0
        self.latencies = []
        self.confidences = []
        self.json_success = 0
        self.json_failed = 0
        self.pairs = []  # (expected, predicted)

        # Timing breakdowns
        self.embedding_times = []
        self.reranker_times = []
        self.llm_times = []
        self.retrieval_times = []  # rag total
        self.total_times = []     # pipeline total

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
    ):
        self.total += 1
        if expected == predicted:
            self.correct += 1

        self.latencies.append(latency)
        self.confidences.append(confidence)
        self.pairs.append((expected, predicted))

        if source == "medical_guideline_rag":
            self.rag_used += 1
        elif source == "web_fallback":
            self.web_used += 1

        if json_ok:
            self.json_success += 1
        else:
            self.json_failed += 1

        # Collect timing breakdowns
        if rag_timings:
            self.embedding_times.append(rag_timings.get("embedding", 0))
            self.reranker_times.append(rag_timings.get("reranker", 0))
        if pipeline_timings:
            self.llm_times.append(pipeline_timings.get("llm", 0))
            self.retrieval_times.append(pipeline_timings.get("rag", 0))
            self.total_times.append(pipeline_timings.get("total", 0))

    # ---- Core metric functions ----

    def accuracy(self):
        if self.total == 0:
            return 0.0
        return round(self.correct / self.total * 100, 2)

    def precision(self):
        """Macro-averaged precision across all labels."""
        precisions = []
        for label in LABELS:
            tp = sum(1 for e, p in self.pairs if p == label and e == label)
            fp = sum(1 for e, p in self.pairs if p == label and e != label)
            if tp + fp > 0:
                precisions.append(tp / (tp + fp))
        if not precisions:
            return 0.0
        return round(mean(precisions) * 100, 2)

    def recall(self):
        """Macro-averaged recall across all labels."""
        recalls = []
        for label in LABELS:
            tp = sum(1 for e, p in self.pairs if e == label and p == label)
            fn = sum(1 for e, p in self.pairs if e == label and p != label)
            if tp + fn > 0:
                recalls.append(tp / (tp + fn))
        if not recalls:
            return 0.0
        return round(mean(recalls) * 100, 2)

    def f1(self):
        """Macro-averaged F1 score."""
        p = self.precision()
        r = self.recall()
        if p + r == 0:
            return 0.0
        return round(2 * p * r / (p + r), 2)

    def average_latency(self):
        return round(mean(self.latencies), 3) if self.latencies else 0.0

    def average_confidence(self):
        return round(mean(self.confidences), 3) if self.confidences else 0.0

    def rag_usage(self):
        return self.rag_used

    def web_usage(self):
        return self.web_used

    def average_embedding_time(self):
        return round(mean(self.embedding_times), 4) if self.embedding_times else 0.0

    def average_reranking_time(self):
        return round(mean(self.reranker_times), 4) if self.reranker_times else 0.0

    def average_llm_time(self):
        return round(mean(self.llm_times), 4) if self.llm_times else 0.0

    def average_retrieval_time(self):
        return round(mean(self.retrieval_times), 4) if self.retrieval_times else 0.0

    def average_total_time(self):
        return round(mean(self.total_times), 4) if self.total_times else 0.0

    def report(self):
        return {
            "questions": self.total,
            "accuracy": self.accuracy(),
            "precision": self.precision(),
            "recall": self.recall(),
            "f1": self.f1(),
            "rag_usage": self.rag_usage(),
            "web_usage": self.web_usage(),
            "average_latency": self.average_latency(),
            "average_confidence": self.average_confidence(),
            "average_embedding_time": self.average_embedding_time(),
            "average_reranking_time": self.average_reranking_time(),
            "average_llm_time": self.average_llm_time(),
            "average_retrieval_time": self.average_retrieval_time(),
            "average_total_time": self.average_total_time(),
            "json_success": self.json_success,
            "json_failed": self.json_failed,
        }