"""Read `output/report-v*.md` into one table. Public API: `parse_report`, `format_runs`.

The committed report stores the numbers themselves. It does not link to the eval files, which are not
committed. Rows are ordered by file name, which is the prompt version and then the UTC stamp.
"""

import re
from pathlib import Path

_METRIC = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$")
_STAMP = re.compile(r"report-(v\d+)-(\d{8})T(\d{6})Z\.md$")
_PLAIN = re.compile(r"report-(v\d+)\.md$")
_ANSWERS = re.compile(r"^Answers: (\d+) tokens, \$([0-9.]+), \$([0-9.]+) per 1000 questions\.$")
_FLAKY = re.compile(r"flaky (.+)\.$")
_HEADING = "## Eval runs"


def sort_names(names: list[str]) -> list[str]:
    """Unstamped reports first, then by UTC stamp. The same names always come out in this order."""
    def key(name: str) -> tuple:
        stamped = _STAMP.search(name)
        if stamped:
            return (1, stamped.group(2) + stamped.group(3), name)
        return (0, "", name)
    return sorted(names, key=key)


def label_for(name: str) -> str:
    """`report-v3-20261117T155837Z.md` -> `v3 2026-11-17 15:58`. An unstamped file is just `v2`."""
    stamped = _STAMP.search(name)
    if stamped:
        day, clock = stamped.group(2), stamped.group(3)
        return f"{stamped.group(1)} {day[:4]}-{day[4:6]}-{day[6:8]} {clock[:2]}:{clock[2:4]}"
    plain = _PLAIN.search(name)
    return plain.group(1) if plain else name


def parse_report(name: str, text: str) -> dict:
    """The metric table, cost line, flaky ids, and gate lines from one report."""
    metrics: dict[str, str] = {}
    answers = ""
    flaky = "none"
    gate: list[str] = []
    in_gate = False
    for raw in text.splitlines():
        line = raw.strip()
        if line == "## Gate":
            in_gate = True
            continue
        if in_gate:
            if line.startswith("## "):
                in_gate = False
            elif line and line != "Passed.":
                gate.append(line)
            continue
        if line.startswith("| metric") or line.startswith("|---") or line.startswith("| ---"):
            continue
        metric = _METRIC.match(line)
        if metric and metric.group(1) != "metric":
            metrics[metric.group(1)] = metric.group(2)
        cost = _ANSWERS.match(line)
        if cost:
            answers = cost.group(3)
        found = _FLAKY.search(line)
        if found:
            flaky = found.group(1)
    return {
        "run": label_for(name),
        "recall": metrics.get("recall@5", "n/a"),
        "pass": metrics.get("pass", "n/a"),
        "facts": metrics.get("facts", "n/a"),
        "cited": metrics.get("cited", "n/a"),
        "abstain": metrics.get("abstain", "n/a"),
        "false_abstain": metrics.get("false_abstain", "n/a"),
        "judge": metrics.get("judge", "n/a"),
        "grounded": metrics.get("grounded", "n/a"),
        "answer_per_1000": answers or "n/a",
        "flaky": flaky,
        "gate": "; ".join(gate) if gate else "pass",
    }


def format_runs(rows: list[dict]) -> str:
    """The `## Eval runs` section. `rows` must already be in file-name order."""
    columns = (
        "run", "recall", "pass", "facts", "cited", "abstain", "false abstain",
        "judge", "grounded", "answer $ / 1000", "flaky", "gate",
    )
    keys = (
        "run", "recall", "pass", "facts", "cited", "abstain", "false_abstain",
        "judge", "grounded", "answer_per_1000", "flaky", "gate",
    )
    header = "| " + " | ".join(columns) + " |"
    rule = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(str(row[key]) for key in keys) + " |" for row in rows]
    return "\n".join(["## Eval runs", "", "One row per rag-eval report. Unstamped runs first, then by time.", "", header, rule, *body, ""])


def load_reports(directory: Path) -> list[dict]:
    paths = list(directory.glob("report-v*.md"))
    names = sort_names([path.name for path in paths])
    by_name = {path.name: path for path in paths}
    return [parse_report(name, by_name[name].read_text(encoding="utf-8")) for name in names]


def splice(report: str, section: str) -> str:
    """Replace an existing eval-runs section, or append one. The k-sweep section stays put."""
    start = report.find(f"\n{_HEADING}\n")
    if start == -1:
        return report.rstrip() + "\n\n" + section
    end = report.find("\n## ", start + 1)
    if end == -1:
        return report[:start].rstrip() + "\n\n" + section
    return report[:start].rstrip() + "\n\n" + section + report[end + 1:]
