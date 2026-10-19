"""Score a committed results JSONL with the package parser.

``phase2/analysis/analyze_p2.py`` and ``pilot/run/analyze.py`` wrote the
metrics files in this repository. Those scripts are unchanged. Use this
module to apply the same leading-word parser, and
``whostop.gate.evaluate_competence_gate``, to a JSONL without calling a model.

Usage: ``python -m whostop.score phase2/run/results_qwen3vl2b_main_640.jsonl``
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from whostop.parse import parse_completion


def load_jsonl(path: Path | str) -> list[dict]:
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def score_record(record: dict, *, prompt: str = "") -> dict:
    """Attach ``action`` (STOP / CAUTION / PROCEED / UNPARSED / ERROR)."""
    raw = str(record.get("raw") or "")
    if raw.startswith("ERROR"):
        action = "ERROR"
    else:
        action = parse_completion(raw, prompt)
    return {**record, "action": action, "error": action == "ERROR"}


def tally(records: list[dict], *, prompt: str = "") -> Counter:
    counts: Counter = Counter()
    for record in records:
        counts[score_record(record, prompt=prompt)["action"]] += 1
    counts["n"] = len(records)
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Parse a results JSONL offline.")
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--prompt-id", default="", help="If set, keep only this prompt id.")
    args = parser.parse_args(argv)
    rows = load_jsonl(args.jsonl)
    if args.prompt_id:
        rows = [row for row in rows if row.get("prompt") == args.prompt_id]
    counts = tally(rows)
    for key in ("n", "STOP", "PROCEED", "CAUTION", "UNPARSED", "ERROR"):
        print(f"{key}\t{counts.get(key, 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
