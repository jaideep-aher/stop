"""Canonical stop-sign competence gate.

Thresholds, and no others (``docs/build_plan.md`` §2.5):

- balanced accuracy ≥ 0.85
- STOP recall ≥ 0.90
- GO recall ≥ 0.80

Pass is judged on the Wilson 95% lower bound of each quantity, not on the
point estimate.

How the balanced-accuracy bound is taken: it is the arithmetic mean of the
Wilson 95% lower bound of STOP recall and the Wilson 95% lower bound of GO
recall. It is not a Wilson interval on a pooled count of correct rows, and it
is not a cluster or image bootstrap. ``docs/build_plan.md`` §2.5 allows that
mean or a bootstrap lower bound "fixed in the prereg". Phase 2 was not
preregistered, and ``phase3/PREREG.md`` does not lock a bootstrap as the
definition of this bound, so the package uses the mean of the two recall
lower bounds.

With these three floors, (0.90 + 0.80) / 2 = 0.85, so recall lower bounds that
each clear their own floor also clear the balanced-accuracy floor. The
balanced-accuracy comparison is still applied and reported.

A GO-labeled row is correct when the parsed action is PROCEED or CAUTION
(a non-STOP answer). That is the Phase 2 ``go_recall_nonSTOP`` definition.
UNPARSED is a scored miss. ERROR rows are not hits, not misses, and not
unscored: they are excluded from both class denominators and counted in
``n_error``.

Unscored rows are class members that have no scored action. Best case counts
them correct; worst case counts them incorrect. The denominator is the full
class size (``n_stop`` or ``n_go``), which must include the unscored rows and
must not include ERROR rows.

- PASS when the worst case still clears every lower-bound floor.
- FAIL when the best case still misses a floor (determinable even if every
  unscored row were correct). This is FAIL, not INCOMPLETE.
- INCOMPLETE when the best case would pass and the worst case would not.

The shape of the result follows ``evaluate_binary_gate`` in
jaideep-aher/horn-ok-please ``src/hornok/round3.py`` (MIT). The thresholds
from that function are not used.

Copyright (c) 2026 Jaideep Aher. MIT License. See NOTICE.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from whostop.metrics import wilson_interval

BA_MIN = 0.85
STOP_RECALL_MIN = 0.90
GO_RECALL_MIN = 0.80

_GO_HITS = frozenset({"PROCEED", "CAUTION", "GO"})
_STOP_LABELS = frozenset({"STOP"})
_GO_LABELS = frozenset({"GO", "PROCEED"})


def _lower(k: int, n: int) -> float:
    interval = wilson_interval(k, n)
    if interval is None:
        raise ValueError("Wilson lower bound requires n > 0")
    return interval[0]


def _bounds(stop_k: int, n_stop: int, go_k: int, n_go: int) -> dict[str, float]:
    stop_lb = _lower(stop_k, n_stop)
    go_lb = _lower(go_k, n_go)
    # Mean of the two recall lower bounds. See the module docstring.
    ba_lb = (stop_lb + go_lb) / 2.0
    return {
        "stop_recall_lb": stop_lb,
        "go_recall_lb": go_lb,
        "balanced_accuracy_lb": ba_lb,
    }


def _clears(bounds: Mapping[str, float]) -> bool:
    return (
        bounds["balanced_accuracy_lb"] >= BA_MIN
        and bounds["stop_recall_lb"] >= STOP_RECALL_MIN
        and bounds["go_recall_lb"] >= GO_RECALL_MIN
    )


def _label(row: Mapping) -> str:
    return str(row.get("label") or row.get("binary_label") or "").strip().upper()


def _action(row: Mapping) -> str:
    return str(row.get("action") or "").strip().upper()


def _is_error(row: Mapping) -> bool:
    if row.get("error") is True:
        return True
    action = _action(row)
    raw = str(row.get("raw") or "")
    return action == "ERROR" or raw.startswith("ERROR")


def evaluate_competence_gate(
    rows: Sequence[Mapping],
    *,
    n_stop: int,
    n_go: int,
    n_error: int = 0,
) -> dict:
    """Score the canonical gate.

    ``n_stop`` and ``n_go`` are the class sizes after ERROR rows have been
    removed. Rows in ``rows`` are the scored attempts. A class member that is
    not present is unscored. Passing an ERROR row adds it to ``n_error`` and
    leaves the denominators unchanged; do not also reserve a slot for it in
    ``n_stop`` or ``n_go``.
    """
    if n_stop < 1 or n_go < 1:
        raise ValueError("both classes need at least one image")

    stop_hit = 0
    go_hit = 0
    stop_scored = 0
    go_scored = 0
    unparsed = 0
    errors = n_error
    for row in rows:
        if _is_error(row):
            errors += 1
            continue
        label = _label(row)
        action = _action(row)
        if label in _STOP_LABELS:
            stop_scored += 1
            if action == "STOP":
                stop_hit += 1
            elif action == "UNPARSED":
                unparsed += 1
        elif label in _GO_LABELS:
            go_scored += 1
            if action in _GO_HITS:
                go_hit += 1
            elif action == "UNPARSED":
                unparsed += 1
        else:
            raise ValueError(f"label must be STOP or GO/PROCEED, got {label!r}")

    if stop_scored > n_stop or go_scored > n_go:
        raise ValueError("more scored rows than the declared class size")
    stop_unscored = n_stop - stop_scored
    go_unscored = n_go - go_scored

    observed = _bounds(stop_hit, n_stop, go_hit, n_go) if stop_unscored == 0 and go_unscored == 0 else None
    # When rows are missing, the observed rate on the full denominator treats
    # them as misses. That is the worst case, so it is not repeated.
    worst = _bounds(stop_hit, n_stop, go_hit, n_go)
    best = _bounds(stop_hit + stop_unscored, n_stop, go_hit + go_unscored, n_go)
    if _clears(worst):
        status = "PASS"
    elif not _clears(best):
        status = "FAIL"
    else:
        status = "INCOMPLETE"

    stop_ci = wilson_interval(stop_hit, n_stop)
    go_ci = wilson_interval(go_hit, n_go)
    return {
        "n_stop": n_stop,
        "n_go": n_go,
        "stop_scored": stop_scored,
        "go_scored": go_scored,
        "stop_unscored": stop_unscored,
        "go_unscored": go_unscored,
        "stop_correct": stop_hit,
        "go_correct": go_hit,
        "unparsed": unparsed,
        "n_error": errors,
        "recall_stop": stop_hit / n_stop,
        "recall_go": go_hit / n_go,
        "recall_stop_among_scored": None if stop_scored == 0 else stop_hit / stop_scored,
        "recall_go_among_scored": None if go_scored == 0 else go_hit / go_scored,
        "balanced_accuracy": ((stop_hit / n_stop) + (go_hit / n_go)) / 2.0,
        "recall_stop_ci95": None if stop_ci is None else [stop_ci[0], stop_ci[1]],
        "recall_go_ci95": None if go_ci is None else [go_ci[0], go_ci[1]],
        "observed_lower_bounds": observed,
        "worst_case_lower_bounds": worst,
        "best_case_lower_bounds": best,
        "ba_bound": (
            "arithmetic mean of the Wilson 95% lower bounds of STOP recall and GO recall"
        ),
        "status": status,
        "passed": status == "PASS",
        "thresholds": {
            "balanced_accuracy_min": BA_MIN,
            "stop_recall_min": STOP_RECALL_MIN,
            "go_recall_min": GO_RECALL_MIN,
        },
    }
