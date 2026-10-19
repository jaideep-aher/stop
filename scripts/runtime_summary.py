#!/usr/bin/env python3
"""Median request latency from committed pilot, Phase 2, and Phase 3 results.

Reads ``latency_s`` from ``pilot/run/results_*.jsonl``,
``phase2/run/results_*.jsonl``, and ``phase3/run/results_*.jsonl``. Prints
the median seconds per request for each model and the sum of ``latency_s``
divided by 3600. That sum is wall-clock request time, not true CPU-hours:
several model processes ran at once, and ``latency_s`` is the wait for one
request.
"""

from __future__ import annotations

import glob
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLOBS = (
    "pilot/run/results_*.jsonl",
    "phase2/run/results_*.jsonl",
    "phase3/run/results_*.jsonl",
)


def main() -> int:
    files = []
    for pattern in GLOBS:
        files.extend(sorted(glob.glob(os.path.join(ROOT, pattern))))
    if not files:
        print("No committed pilot, Phase 2, or Phase 3 result files found.")
        return 1

    by_model: dict[str, list[float]] = {}
    missing: list[str] = []
    for path in files:
        latencies: list[float] = []
        rows = 0
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                rows += 1
                if "latency_s" not in row:
                    continue
                latencies.append(float(row["latency_s"]))
                by_model.setdefault(str(row.get("model", "unknown")), []).append(float(row["latency_s"]))
        if rows and len(latencies) != rows:
            missing.append(os.path.relpath(path, ROOT))

    print(
        "source: committed pilot/run/results_*.jsonl, "
        "phase2/run/results_*.jsonl, and phase3/run/results_*.jsonl"
    )
    if missing and not by_model:
        print("Committed result files have no latency_s field.")
        for name in missing:
            print(name)
        return 0
    if missing:
        print("files_missing_latency_s:")
        for name in missing:
            print(name)

    print("model\tn_requests\tmedian_s_per_request")
    total = 0.0
    for model in sorted(by_model):
        samples = by_model[model]
        total += sum(samples)
        median = statistics.median(samples)
        print(f"{model}\t{len(samples)}\t{median:.4f}")
    hours = total / 3600.0
    print(f"sum_latency_s\t{total:.4f}")
    print(
        f"wall_clock_request_time_hours\t{hours:.4f}\t"
        "wall-clock request time, not true CPU-hours"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
