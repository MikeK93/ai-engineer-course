"""Pass or fail a run. Public API: `gate`, `FLOORS`.

Absolute floors apply on every run. When a baseline is present, a metric that drops by more than
0.05 fails, and `false_abstain` fails when it rises by more than 0.05. A case that passed in the
baseline and fails now is a regression. Cases that already failed, and metrics that held, stay quiet.
"""

TOLERANCE = 0.05
LOWER_IS_BETTER = frozenset({"false_abstain"})
FLOORS = {"recall@5": 0.8, "pass": 0.7, "abstain": 1.0, "grounded": 0.85}


def gate(metrics: dict, *, baseline: dict | None = None, passed: set[str] | None = None) -> list[str]:
    """Failure lines. An empty list is a pass."""
    failures: list[str] = []
    for key, floor in FLOORS.items():
        value = metrics.get(key)
        if isinstance(value, (int, float)) and value < floor:
            failures.append(f"floor: {key} {value:.2f} < {floor:.2f}")
    if not baseline:
        return failures
    before = baseline.get("metrics", baseline)
    for key, old in before.items():
        new = metrics.get(key)
        if not isinstance(old, (int, float)) or not isinstance(new, (int, float)):
            continue
        if key in LOWER_IS_BETTER:
            if new > old + TOLERANCE:
                failures.append(f"baseline: {key} {new:.2f} rose above {old:.2f}")
        elif new < old - TOLERANCE:
            failures.append(f"baseline: {key} {new:.2f} fell below {old:.2f}")
    passed = passed or set()
    for case_id in baseline.get("passed", []):
        if case_id not in passed:
            failures.append(f"regression: {case_id}")
    return failures
