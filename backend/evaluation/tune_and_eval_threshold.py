import os
import sys
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Use BM25-only to avoid heavy model loads during tuning
os.environ['QDRANT_HOST'] = 'local'
os.environ['FAST_DEV'] = '1'

from app.services import rag_service

TEST_FILE = Path(__file__).resolve().parent / 'test_cases.json'


def collect_scores(tests):
    results = []
    for t in tests:
        q = t['question']
        start = time.perf_counter()
        res = rag_service.retrieve_context(q, top_k=3)
        latency = time.perf_counter() - start
        results.append({
            'question': q,
            'expected_source': t.get('expected_source'),
            'top_score': res.get('top_score', 0),
            'retrieved_sources': res.get('retrieved_sources', []),
            'latency': latency,
        })
    return results


def evaluate_threshold(results, threshold):
    total = 0
    correct = 0
    web_fallbacks = 0
    confidences = []
    latencies = []

    for r in results:
        expected = r.get('expected_source')
        if not expected:
            continue
        total += 1
        top_score = r['top_score']
        confidences.append(top_score)
        latencies.append(r['latency'])
        rag_used = top_score > threshold
        if not rag_used:
            web_fallbacks += 1
        else:
            if expected in r.get('retrieved_sources', []):
                correct += 1

    retrieval_accuracy = (correct / total * 100) if total else 0
    web_fallback_rate = (web_fallbacks / total * 100) if total else 0
    avg_confidence = (sum(confidences) / len(confidences)) if confidences else 0
    avg_latency = (sum(latencies) / len(latencies)) if latencies else 0

    return {
        'threshold': threshold,
        'retrieval_accuracy': retrieval_accuracy,
        'web_fallback_rate': web_fallback_rate,
        'avg_confidence': avg_confidence,
        'avg_latency': avg_latency,
    }


def find_best_threshold(results):
    scores = [r['top_score'] for r in results]
    if not scores:
        return rag_service.CONFIDENCE_THRESHOLD
    mn = min(scores)
    mx = max(scores)
    # Sweep thresholds across observed range
    best = None
    best_acc = -1
    candidates = [mn + i * (mx - mn) / 80 for i in range(81)]
    for t in candidates:
        ev = evaluate_threshold(results, t)
        # Prefer higher retrieval accuracy, tie-breaker lower web fallback rate
        score = (ev['retrieval_accuracy'], -ev['web_fallback_rate'])
        if score > (best_acc, 0):
            best_acc = score[0]
            best = ev
    return best


def main():
    with open(TEST_FILE, encoding='utf-8') as f:
        tests = json.load(f)

    print('Collecting retrieval scores...')
    results = collect_scores(tests)
    print('Collected', len(results), 'results')

    print('Finding best threshold...')
    best = find_best_threshold(results)

    if best:
        print('Best threshold found:', best)
        # Persist threshold
        rag_service.set_confidence_threshold(best['threshold'])
        print('Persisted threshold to', rag_service.INDEX_DIR / 'threshold.json')

    # Also print baseline metrics using current stored or default
    current = rag_service.get_confidence_threshold()
    baseline = evaluate_threshold(results, current)
    print('\nBaseline (current) metrics:', baseline)

    # Save a simple report
    report = {
        'tuning_result': best,
        'baseline': baseline,
        'samples': results,
    }
    out = Path(__file__).resolve().parent / 'tuning_report.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print('Saved tuning report to', out)


if __name__ == '__main__':
    main()
