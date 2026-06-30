"""
Confusion Matrix Builder

Builds a confusion matrix from (expected, predicted) pairs
for the three triage urgency labels.
"""

LABELS = ["home_care", "visit_phc", "critical"]


def build_confusion_matrix(pairs):
    """
    Build a confusion matrix from a list of (expected, predicted) tuples.

    Returns a dict with:
        - matrix: dict of {expected: {predicted: count}}
        - labels: list of label names
        - formatted: printable string
    """
    matrix = {e: {p: 0 for p in LABELS} for e in LABELS}

    for expected, predicted in pairs:
        if expected in LABELS and predicted in LABELS:
            matrix[expected][predicted] += 1

    # Build formatted string
    header = f"{'':>12}" + "".join(f"{l:>12}" for l in LABELS)
    lines = [header]

    for expected in LABELS:
        row = f"{expected:>12}"
        for predicted in LABELS:
            row += f"{matrix[expected][predicted]:>12}"
        lines.append(row)

    formatted = "\n".join(lines)

    return {
        "matrix": matrix,
        "labels": LABELS,
        "formatted": formatted,
    }
