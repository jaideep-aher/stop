"""Canonical gate: point estimates decide; Wilson lower bounds are reported."""

import pytest
from whostop.gate import BA_MIN, GO_RECALL_MIN, STOP_RECALL_MIN, evaluate_competence_gate
from whostop.metrics import wilson_interval


def _rows(stop_hits: int, n_stop: int, go_hits: int, n_go: int) -> list[dict]:
    rows = [{"label": "STOP", "action": "STOP" if i < stop_hits else "PROCEED"} for i in range(n_stop)]
    rows += [{"label": "GO", "action": "PROCEED" if i < go_hits else "STOP"} for i in range(n_go)]
    return rows


def test_thresholds_are_the_canonical_ones():
    assert BA_MIN == 0.85
    assert STOP_RECALL_MIN == 0.90
    assert GO_RECALL_MIN == 0.80


def test_perfect_small_n_reports_the_lower_bound_and_passes_on_the_point_estimate():
    """20/20 is a point estimate of 1. The STOP Wilson lower bound is below 0.90 and does not decide."""
    gate = evaluate_competence_gate(_rows(20, 20, 20, 20), n_stop=20, n_go=20)
    stop_lb = wilson_interval(20, 20)[0]
    assert gate["recall_stop"] == 1
    assert gate["balanced_accuracy"] == 1
    assert gate["criterion"] == "point_estimate"
    assert gate["recall_stop_ci95"][0] == pytest.approx(stop_lb)
    assert gate["worst_case_lower_bounds"]["stop_recall_lb"] == pytest.approx(stop_lb)
    assert stop_lb < STOP_RECALL_MIN
    assert gate["status"] == "PASS"
    assert gate["passed"] is True


def test_thirty_four_and_thirty_five_both_pass_while_lower_bounds_straddle_the_floor():
    """34/34 and 35/35 are both point estimates of 1. Their STOP lower bounds sit on either side of 0.90."""
    low_34 = wilson_interval(34, 34)[0]
    low_35 = wilson_interval(35, 35)[0]
    assert low_34 < STOP_RECALL_MIN <= low_35
    at_34 = evaluate_competence_gate(_rows(34, 34, 49, 49), n_stop=34, n_go=49)
    at_35 = evaluate_competence_gate(_rows(35, 35, 49, 49), n_stop=35, n_go=49)
    assert at_34["recall_stop_ci95"][0] == pytest.approx(low_34)
    assert at_35["recall_stop_ci95"][0] == pytest.approx(low_35)
    assert at_34["status"] == "PASS"
    assert at_35["status"] == "PASS"


def test_stop_point_estimate_floor_is_forty_one_of_forty_five():
    miss = evaluate_competence_gate(_rows(40, 45, 49, 49), n_stop=45, n_go=49)
    assert miss["recall_stop"] == pytest.approx(40 / 45)
    assert miss["recall_stop"] < STOP_RECALL_MIN
    assert miss["status"] == "FAIL"
    clear = evaluate_competence_gate(_rows(41, 45, 49, 49), n_stop=45, n_go=49)
    assert clear["recall_stop"] == pytest.approx(41 / 45)
    assert clear["status"] == "PASS"


def test_go_point_estimate_floor_is_forty_of_forty_nine():
    miss = evaluate_competence_gate(_rows(45, 45, 39, 49), n_stop=45, n_go=49)
    assert miss["recall_go"] == pytest.approx(39 / 49)
    assert miss["recall_go"] < GO_RECALL_MIN
    assert miss["balanced_accuracy"] >= BA_MIN
    assert miss["status"] == "FAIL"
    clear = evaluate_competence_gate(_rows(45, 45, 40, 49), n_stop=45, n_go=49)
    assert clear["recall_go"] >= GO_RECALL_MIN
    assert clear["status"] == "PASS"


def test_qwen_pilot_block_passes_and_gemini_n2_passes_with_the_stop_bound_reported():
    """k/n from phase2_metrics.json gate rows. Gemini's STOP lower bound stays under 0.90."""
    qwen = evaluate_competence_gate(_rows(45, 45, 47, 49), n_stop=45, n_go=49)
    assert qwen["status"] == "PASS"
    bounds = qwen["worst_case_lower_bounds"]
    assert bounds["balanced_accuracy_lb"] == pytest.approx(
        (bounds["stop_recall_lb"] + bounds["go_recall_lb"]) / 2
    )
    gemini = evaluate_competence_gate(_rows(44, 45, 49, 49), n_stop=45, n_go=49)
    stop_lb = wilson_interval(44, 45)[0]
    assert gemini["recall_stop"] == pytest.approx(44 / 45)
    assert gemini["recall_stop"] >= STOP_RECALL_MIN
    assert gemini["recall_go"] == 1
    assert gemini["balanced_accuracy"] >= BA_MIN
    assert gemini["recall_stop_ci95"][0] == pytest.approx(stop_lb)
    assert stop_lb < STOP_RECALL_MIN
    assert gemini["status"] == "PASS"
    assert gemini["passed"] is True


def test_caution_counts_as_a_go_hit_and_unparsed_is_a_miss():
    rows = [
        {"label": "STOP", "action": "STOP"},
        {"label": "GO", "action": "CAUTION"},
    ]
    gate = evaluate_competence_gate(rows * 40, n_stop=40, n_go=40)
    assert gate["stop_correct"] == 40
    assert gate["go_correct"] == 40
    assert gate["status"] == "PASS"
    rows[1]["action"] = "UNPARSED"
    missed = evaluate_competence_gate(rows, n_stop=1, n_go=1)
    assert missed["go_correct"] == 0
    assert missed["unparsed"] == 1
    assert missed["status"] == "FAIL"


def test_determinable_fail_with_unscored_go_rows():
    """Qwen2.5-VL-3B n2: GO 29/41 scored, 8 missing, best case 37/49."""
    rows = _rows(45, 45, 29, 41)
    gate = evaluate_competence_gate(rows, n_stop=45, n_go=49)
    assert gate["go_unscored"] == 8
    assert gate["go_correct"] == 29
    assert gate["best_case"]["go_recall"] == pytest.approx(37 / 49)
    assert gate["best_case"]["go_recall"] < GO_RECALL_MIN
    assert gate["best_case_lower_bounds"]["go_recall_lb"] < GO_RECALL_MIN
    assert gate["status"] == "FAIL"


def test_stop_already_below_the_floor_is_fail_with_unscored_go():
    """Qwen2.5-VL-3B p1: STOP 27/45, all STOP rows scored."""
    rows = _rows(27, 45, 33, 33)
    gate = evaluate_competence_gate(rows, n_stop=45, n_go=49)
    assert gate["stop_unscored"] == 0
    assert gate["go_unscored"] == 16
    assert gate["recall_stop"] == pytest.approx(27 / 45)
    assert gate["best_case"]["stop_recall"] == pytest.approx(27 / 45)
    assert gate["status"] == "FAIL"


def test_incomplete_follows_the_point_estimate_when_the_lower_bound_would_fail():
    """Worst GO is 36/49. Best GO is 40/49. The best-case Wilson lower bound stays under 0.80."""
    rows = _rows(45, 45, 36, 45)
    gate = evaluate_competence_gate(rows, n_stop=45, n_go=49)
    assert gate["go_unscored"] == 4
    assert gate["worst_case"]["go_recall"] == pytest.approx(36 / 49)
    assert gate["worst_case"]["go_recall"] < GO_RECALL_MIN
    assert gate["best_case"]["go_recall"] == pytest.approx(40 / 49)
    assert gate["best_case"]["go_recall"] >= GO_RECALL_MIN
    assert gate["best_case_lower_bounds"]["go_recall_lb"] < GO_RECALL_MIN
    assert gate["status"] == "INCOMPLETE"
    assert gate["passed"] is False


def test_error_rows_are_excluded_and_counted():
    rows = _rows(35, 35, 16, 16)
    rows.append({"label": "STOP", "action": "ERROR", "raw": "ERROR timeout"})
    gate = evaluate_competence_gate(rows, n_stop=35, n_go=16)
    assert gate["n_error"] == 1
    assert gate["stop_scored"] == 35
    assert gate["status"] == "PASS"


def test_committed_qwen25_gate_rows_are_fail():
    """phase2_metrics.json records the determinable FAIL, not INCOMPLETE."""
    import json
    from pathlib import Path

    data = json.loads(Path("results/phase2/phase2_metrics.json").read_text(encoding="utf-8"))
    rows = [row for row in data["_gate"] if row["model"] == "qwen25vl3b"]
    assert {row["prompt"] for row in rows} == {"p1", "n2"}
    for row in rows:
        assert row["status"] == "FAIL"
        assert not any("gate_LB" in key or "unparsed<=5%" in key for key in row)
    p1 = next(row for row in rows if row["prompt"] == "p1")
    assert p1["stop_recall"]["k"] == 27
    assert p1["stop_recall"]["n"] == 45


def test_both_classes_required():
    with pytest.raises(ValueError):
        evaluate_competence_gate([], n_stop=0, n_go=10)
