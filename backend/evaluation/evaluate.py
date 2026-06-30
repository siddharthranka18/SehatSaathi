"""
SehatSaathi Evaluation Runner

Runs all test cases against the API, collects metrics,
generates confusion matrix, charts, and an HTML report.
"""

import json
import time
import base64
from pathlib import Path

import requests

from metrics import EvaluationMetrics
from confusion import build_confusion_matrix

try:
    from charts import generate_all as generate_charts
    HAS_CHARTS = True
except ImportError:
    HAS_CHARTS = False


BASE_DIR = Path(__file__).resolve().parent

TEST_FILE = BASE_DIR / "test_cases.json"
REPORT_FILE = BASE_DIR / "report.json"
REPORT_HTML = BASE_DIR / "report.html"

API = "http://127.0.0.1:8000/api/triage"


def embed_image_base64(path):
    """Read an image file and return base64 data URI."""
    try:
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/png;base64,{data}"
    except Exception:
        return ""


def generate_report_html(report, confusion_data, chart_paths):
    """Generate a self-contained HTML dashboard."""
    chart_images = {}
    for name, path in chart_paths.items():
        chart_images[name] = embed_image_base64(path)

    cm = confusion_data["matrix"]
    labels = confusion_data["labels"]

    # Build confusion matrix HTML table
    cm_rows = ""
    for expected in labels:
        cells = ""
        for predicted in labels:
            val = cm[expected][predicted]
            bg = "#2d4a3e" if expected == predicted else "#1B3A4B"
            cells += f'<td style="background:{bg};padding:10px;text-align:center;font-weight:600">{val}</td>'
        cm_rows += f'<tr><td style="padding:10px;font-weight:600;color:#C8A45A">{expected}</td>{cells}</tr>'

    cm_header = "".join(f'<th style="padding:10px;color:#7A9BB0">{l}</th>' for l in labels)

    # Build metrics rows
    metric_rows = ""
    for key, val in report.items():
        metric_rows += f"""
        <tr>
            <td style="padding:8px 12px;color:#C8A45A;font-weight:500">{key}</td>
            <td style="padding:8px 12px;color:#F5F4F0">{val}</td>
        </tr>"""

    # Chart images HTML
    charts_html = ""
    for name, data_uri in chart_images.items():
        if data_uri:
            charts_html += f"""
            <div style="flex:1;min-width:340px;max-width:48%">
                <img src="{data_uri}" style="width:100%;border-radius:8px;border:1px solid #1F4257" alt="{name} chart">
            </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SehatSaathi Evaluation Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: #0f2027;
            color: #F5F4F0;
            min-height: 100vh;
            padding: 32px;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        h1 {{
            font-size: 28px;
            font-weight: 700;
            color: #C8A45A;
            margin-bottom: 8px;
        }}
        .subtitle {{
            color: #7A9BB0;
            font-size: 14px;
            margin-bottom: 32px;
        }}
        .section {{
            background: #1B3A4B;
            border: 1px solid #1F4257;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 600;
            color: #C8A45A;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid #1F4257;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            text-align: left;
            padding: 8px 12px;
            color: #7A9BB0;
            font-size: 13px;
            border-bottom: 1px solid #1F4257;
        }}
        td {{
            border-bottom: 1px solid rgba(31,66,87,0.5);
        }}
        .charts-grid {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>SehatSaathi Evaluation Report</h1>
        <p class="subtitle">Automated evaluation of triage accuracy, latency, and retrieval performance</p>

        <!-- Metrics Summary -->
        <div class="section">
            <div class="section-title">Metrics Summary</div>
            <table>
                <thead>
                    <tr><th>Metric</th><th>Value</th></tr>
                </thead>
                <tbody>
                    {metric_rows}
                </tbody>
            </table>
        </div>

        <!-- Confusion Matrix -->
        <div class="section">
            <div class="section-title">Confusion Matrix</div>
            <table>
                <thead>
                    <tr>
                        <th style="padding:10px">Expected ↓ / Predicted →</th>
                        {cm_header}
                    </tr>
                </thead>
                <tbody>
                    {cm_rows}
                </tbody>
            </table>
        </div>

        <!-- Charts -->
        <div class="section">
            <div class="section-title">Charts</div>
            <div class="charts-grid">
                {charts_html if charts_html else '<p style="color:#7A9BB0">Charts not generated (matplotlib not available)</p>'}
            </div>
        </div>
    </div>
</body>
</html>"""

    with open(REPORT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Saved {REPORT_HTML}")


def main():
    metrics = EvaluationMetrics()

    with open(TEST_FILE, encoding="utf-8") as f:
        tests = json.load(f)

    print()
    print("=" * 70)
    print(f"  Running SehatSaathi Evaluation — {len(tests)} test cases")
    print("=" * 70)
    print()
    print(f"{'Question':40} | {'Predicted':12} | {'Expected':12} | {'Time':>6}")
    print("-" * 78)

    for test in tests:
        payload = {
            "conversation": [
                {
                    "role": "user",
                    "content": test["question"]
                }
            ]
        }

        start = time.perf_counter()

        try:
            response = requests.post(API, json=payload, timeout=60)
            latency = time.perf_counter() - start
            json_ok = response.status_code == 200
        except Exception as e:
            latency = time.perf_counter() - start
            json_ok = False
            print(f"  ERROR: {e}")

        if json_ok:
            result = response.json()
            predicted = result.get("urgency", "ERROR")
            source = result.get("source", "")
            confidence = result.get("confidence", 0)
            pipeline_timings = result.get("pipeline_timings", {})
            rag_timings = result.get("rag_timings", {})
        else:
            predicted = "ERROR"
            source = "ERROR"
            confidence = 0
            pipeline_timings = {}
            rag_timings = {}

        metrics.add_result(
            expected=test["expected_urgency"],
            predicted=predicted,
            latency=latency,
            source=source,
            confidence=confidence,
            json_ok=json_ok,
            pipeline_timings=pipeline_timings,
            rag_timings=rag_timings,
        )

        match = "✓" if predicted == test["expected_urgency"] else "✗"
        print(
            f"  {match} {test['question'][:37]:37}"
            f" | {predicted:12}"
            f" | {test['expected_urgency']:12}"
            f" | {latency:.2f}s"
        )

    # Generate report
    report = metrics.report()

    print()
    print("=" * 70)
    print("  Evaluation Summary")
    print("=" * 70)
    print()

    for k, v in report.items():
        print(f"  {k:28}: {v}")

    # Save report.json
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
    print(f"\n  Saved {REPORT_FILE}")

    # Confusion matrix
    confusion_data = build_confusion_matrix(metrics.pairs)
    print()
    print("  Confusion Matrix:")
    print()
    for line in confusion_data["formatted"].split("\n"):
        print(f"    {line}")

    # Generate charts
    chart_paths = {}
    if HAS_CHARTS:
        print("\n  Generating charts...")
        chart_paths = generate_charts(
            pairs=metrics.pairs,
            latencies=metrics.latencies,
            confidences=metrics.confidences,
            rag_count=metrics.rag_used,
            web_count=metrics.web_used,
        )
        for name, path in chart_paths.items():
            print(f"    Saved {name}: {path}")

    # Generate HTML report
    generate_report_html(report, confusion_data, chart_paths)

    print()
    print("  Evaluation complete!")


if __name__ == "__main__":
    main()