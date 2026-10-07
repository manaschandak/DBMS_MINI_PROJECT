"""Classification metrics for the four risk levels, written without extra libraries.

Conventions (the same as scikit-learn's defaults):
- The labels used are every level that appears in the actual OR the predicted values.
- If a label has no cases for precision or recall, that value counts as 0.
- macro_f1 is the plain average of the F1 value of each label.

recall_high_critical (this project's definition):
  Of all cases whose ACTUAL outcome was HIGH or CRITICAL, the share that the model
  predicted as HIGH or CRITICAL. It answers "how many dangerous cases did we flag?".
  It is None when there are no HIGH or CRITICAL cases.
"""

LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
SERIOUS = ("HIGH", "CRITICAL")


def _f1_for_label(actual, predicted, label):
    pairs = list(zip(actual, predicted))
    tp = sum(1 for a, p in pairs if a == label and p == label)  # correctly predicted this label
    fp = sum(1 for a, p in pairs if a != label and p == label)  # predicted it, but it was not
    fn = sum(1 for a, p in pairs if a == label and p != label)  # it was this label, but we missed it
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def compute_metrics(actual, predicted):
    """actual and predicted are equal-length lists of level names. Returns a dict."""
    if len(actual) != len(predicted) or len(actual) == 0:
        raise ValueError("actual and predicted must be non-empty and the same length")

    n = len(actual)
    pairs = list(zip(actual, predicted))
    accuracy = sum(1 for a, p in pairs if a == p) / n

    labels = sorted(set(actual) | set(predicted), key=LEVELS.index)
    macro_f1 = sum(_f1_for_label(actual, predicted, label) for label in labels) / len(labels)

    serious_cases = [(a, p) for a, p in pairs if a in SERIOUS]
    if serious_cases:
        recall_high_critical = sum(1 for a, p in serious_cases if p in SERIOUS) / len(serious_cases)
        recall_high_critical = round(recall_high_critical, 3)
    else:
        recall_high_critical = None

    return {
        "sample_count": n,
        "accuracy": round(accuracy, 3),
        "macro_f1": round(macro_f1, 3),
        "recall_high_critical": recall_high_critical,
    }
