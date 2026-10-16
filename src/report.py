import json

from .config import RESULTS, ROOT

REPORT = ROOT / "REPORT.md"
START, END = "<!-- AUTO:START -->", "<!-- AUTO:END -->"

TEMPLATE = f"""# Report: model x prompt version x sampling

{START}
{END}

## Error analysis

_Write 3-5 characteristic errors here: what was returned instead of what, and why._

## Production choice

_One paragraph: the chosen model, prompt version and sampling, and the conditions under which you would change the decision._
"""


def _table() -> str:
    rows = []
    for path in sorted(RESULTS.glob("*/metrics.json")):
        m = json.loads(path.read_text(encoding="utf-8"))
        rows.append(
            f"| [{m['run_id']}](results/{m['run_id']}/report.md) | {m['model']} | {m['input_mode']} | {m['prompt_version']} "
            f"| {m['temperature']} / {m['top_p']} | {m['documents']} | {m['field_accuracy_pct']:.1f} "
            f"| {m['valid_pct']:.0f} ({m['valid_first_try_pct']:.0f}) | {m['latency_p50_s']:.1f} / {m['latency_p95_s']:.1f} "
            f"| {m['cost_per_1000_docs_usd']:.2f} |"
        )
    header = [
        "| run | model | input | prompt | temp / top_p | docs | field acc % | valid % (first try) | latency p50 / p95 s | $ per 1000 docs |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    return "\n".join(header + rows) if rows else "_No scored runs yet. Run `python main.py run` or `grid`._"


def build_report():
    """Rewrite only the auto-generated block; hand-written sections are kept."""
    text = REPORT.read_text(encoding="utf-8") if REPORT.exists() else TEMPLATE
    if START not in text or END not in text:
        text = TEMPLATE
    head, rest = text.split(START, 1)
    tail = rest.split(END, 1)[1]
    REPORT.write_text(f"{head}{START}\n{_table()}\n{END}{tail}", encoding="utf-8")
    return REPORT
