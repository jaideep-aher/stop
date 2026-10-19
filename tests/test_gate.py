"""Canonical gate, including Wilson lower-bound edges and determinable FAILs."""

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


def test_perfect_small_n_fails_the_lower_bound():
    """20/20 is a point estimate of 1 and still misses the STOP lower bound."""
    gate = evaluate_competence_gate(_rows(20, 20, 20, 20), n_stop=20, n_go=20)
    assert gate["recall_stop"] == 1
    assert gate["worst_case_lower_bounds"]["stop_recall_lb"] < STOP_RECALL_MIN
    assert gate["status"] == "FAIL"
    assert gate["passed"] is False


def test_thirty_four_fails_and_thirty_five_can_clear_stop():
    low_34 = wilson_interval(34, 34)[0]
    low_35 = wilson_interval(35, 35)[0]
    assert low_34 < STOP_RECALL_MIN <= low_35
    # GO uses a class large enough that its own lower bound is not the binding one.
    fail = evaluate_competence_gate(_rows(34, 34, 49, 49), n_stop=34, n_go=49)
    assert fail["status"] == "FAIL"
    passed = evaluate_competence_gate(_rows(35, 35, 49, 49), n_stop=35, n_go=49)
    assert passed["status"] == "PASS"


def test_qwen_pilot_block_passes_and_gemini_n2_stop_bound_does_not():
    """k/n from phase2_metrics.json gate rows."""
    qwen = evaluate_competence_gate(_rows(45, 45, 47, 49), n_stop=45, n_go=49)
    assert qwen["status"] == "PASS"
    bounds = qwen["worst_case_lower_bounds"]
    assert bounds["balanced_accuracy_lb"] == pytest.approx(
        (bounds["stop_recall_lb"] + bounds["go_recall_lb"]) / 2
    )
    gemini = evaluate_competence_gate(_rows(44, 45, 49, 49), n_stop=45, n_go=49)
    assert gemini["recall_stop_ci95"][0] < STOP_RECALL_MIN
    assert gemini["status"] == "FAIL"


def test_caution_counts_as_a_go_hit_and_unparsed_is_a_miss():
    rows = [
        {"label": "STOP", "action": "STOP"},
        {"label": "GO", "action": "CAUTION"},
    ]
    # Too small to pass; this checks the hit definition only.
    gate = evaluate_competence_gate(rows * 40, n_stop=40, n_go=40)
    assert gate["stop_correct"] == 40
    assert gate["go_correct"] == 40
    rows[1]["action"] = "UNPARSED"
    missed = evaluate_competence_gate(rows, n_stop=1, n_go=1)
    assert missed["go_correct"] == 0
    assert missed["unparsed"] == 1


def test_determinable_fail_with_unscored_go_rows():
    """Qwen2.5-VL-3B n2: GO 29/41 scored, 8 missing, best case 37/49."""
    rows = _rows(45, 45, 29, 41)
    gate = evaluate_competence_gate(rows, n_stop=45, n_go=49)
    assert gate["go_unscored"] == 8
    assert gate["go_correct"] == 29
    assert gate["best_case_lower_bounds"]["go_recall_lb"] < GO_RECALL_MIN
    assert gate["status"] == "FAIL"


def test_stop_already_below_the_floor_is_fail_with_unscored_go():
    """Qwen2.5-VL-3B p1: STOP 27/45, all STOP rows scored."""
    rows = _rows(27, 45, 33, 33)
    gate = evaluate_competence_gate(rows, n_stop=45, n_go=49)
    assert gate["stop_unscored"] == 0
    assert gate["go_unscored"] == 16
    assert gate["status"] == "FAIL"


def test_incomplete_when_the_missing_rows_could_still_save_it():
    # 41/49 fails the GO lower bound; 45/49 (if the 4 missing rows are correct) clears it.
    rows = _rows(45, 45, 41, 45)
    gate = evaluate_competence_gate(rows, n_stop=45, n_go=49)
    assert gate["go_unscored"] == 4
    assert gate["status"] == "INCOMPLETE"
    assert gate["passed"] is False


def test_error_rows_are_excluded_and_counted():
    rows = _rows(35, 35, 16, 16)
    rows.append({"label": "STOP", "action": "ERROR", "raw": "ERROR timeout"})
    gate = evaluate_competence_gate(rows, n_stop=35, n_go=16)
    assert gate["n_error"] == 1
    assert gate["stop_scored"] == 35
    assert gate["status"] == "PASS"


def test_both_classes_required():
    with pytest.raises(ValueError):
        evaluate_competence_gate([], n_stop=0, n_go=10)
