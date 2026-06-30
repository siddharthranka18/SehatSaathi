"""
Chart Generator for Evaluation Reports

Generates PNG charts using matplotlib:
- Accuracy bar chart (per-class + overall)
- Source usage pie chart
- Latency histogram
- Confidence histogram
"""

import os
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("WARNING: matplotlib not installed. Charts will not be generated.")


OUTPUT_DIR = Path(__file__).resolve().parent

COLORS = {
    "home_care": "#4CAF82",
    "visit_phc": "#C8A45A",
    "critical": "#E57373",
    "overall": "#5C9BD4",
    "rag": "#4CAF82",
    "web": "#E57373",
    "other": "#7A9BB0",
}


def accuracy_bar_chart(pairs, output_path=None):
    """Per-class accuracy + overall accuracy bar chart."""
    if not HAS_MATPLOTLIB:
        return None

    labels = ["home_care", "visit_phc", "critical"]
    per_class = {}
    for label in labels:
        total = sum(1 for e, _ in pairs if e == label)
        correct = sum(1 for e, p in pairs if e == label and p == label)
        per_class[label] = (correct / total * 100) if total > 0 else 0

    overall = sum(1 for e, p in pairs if e == p) / len(pairs) * 100 if pairs else 0

    categories = labels + ["overall"]
    values = [per_class[l] for l in labels] + [overall]
    colors = [COLORS[c] for c in categories]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(categories, values, color=colors, edgecolor="white", linewidth=0.5)
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Triage Accuracy by Category")
    ax.set_ylim(0, 105)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f"{val:.1f}%", ha="center", va="bottom", fontsize=10)

    plt.tight_layout()
    path = output_path or str(OUTPUT_DIR / "chart_accuracy.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def source_pie_chart(rag_count, web_count, other_count=0, output_path=None):
    """Source usage pie chart."""
    if not HAS_MATPLOTLIB:
        return None

    sizes = []
    chart_labels = []
    colors = []

    if rag_count > 0:
        sizes.append(rag_count)
        chart_labels.append(f"RAG ({rag_count})")
        colors.append(COLORS["rag"])
    if web_count > 0:
        sizes.append(web_count)
        chart_labels.append(f"Web ({web_count})")
        colors.append(COLORS["web"])
    if other_count > 0:
        sizes.append(other_count)
        chart_labels.append(f"Other ({other_count})")
        colors.append(COLORS["other"])

    if not sizes:
        return None

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(sizes, labels=chart_labels, colors=colors, autopct="%1.1f%%",
           startangle=90, textprops={"fontsize": 11})
    ax.set_title("Source Usage Distribution")
    plt.tight_layout()
    path = output_path or str(OUTPUT_DIR / "chart_source.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def latency_histogram(latencies, output_path=None):
    """Latency distribution histogram."""
    if not HAS_MATPLOTLIB or not latencies:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(latencies, bins=20, color="#5C9BD4", edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Latency (seconds)")
    ax.set_ylabel("Count")
    ax.set_title("Response Latency Distribution")
    plt.tight_layout()
    path = output_path or str(OUTPUT_DIR / "chart_latency.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def confidence_histogram(confidences, output_path=None):
    """Confidence score distribution histogram."""
    if not HAS_MATPLOTLIB or not confidences:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(confidences, bins=20, color="#C8A45A", edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Confidence Score")
    ax.set_ylabel("Count")
    ax.set_title("RAG Confidence Distribution")
    plt.tight_layout()
    path = output_path or str(OUTPUT_DIR / "chart_confidence.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def generate_all(pairs, latencies, confidences, rag_count, web_count):
    """Generate all charts. Returns dict of chart name -> path."""
    results = {}

    path = accuracy_bar_chart(pairs)
    if path:
        results["accuracy"] = path

    path = source_pie_chart(rag_count, web_count)
    if path:
        results["source"] = path

    path = latency_histogram(latencies)
    if path:
        results["latency"] = path

    path = confidence_histogram(confidences)
    if path:
        results["confidence"] = path

    return results
