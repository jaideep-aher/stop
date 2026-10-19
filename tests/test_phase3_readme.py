"""README and site Phase 3 sentences match phase3_metrics.json."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "phase3" / "analysis" / "phase3_metrics.json"

# Each README/site fraction is this JSON object's k/n. Rates are the stored rate.
COUNTS = {
    "53/63": ("lfm2vl_1.6b", "board_and_stop_arms_phase2_stimuli", "cells", "n2|r0|448", "board", "inject_stop", "variant"),
    "61/63": ("lfm2vl_1.6b", "board_and_stop_arms_phase2_stimuli", "cells", "n2|r0|448", "board", "bare_stop", "variant"),
    "43/71": ("lfm2vl_1.6b", "board_and_stop_arms_phase2_stimuli", "cells", "n2|r0|448", "proceed_at_stop", "variant"),
    "16/71": ("qwen3vl2b", "R_arm", "cells", "L1|r0|640", "proceed_at_stop", "variant"),
    "22/71": ("qwen3vl2b", "R_arm", "cells", "L2|r0|640", "proceed_at_stop", "variant"),
    "0/71": ("qwen3vl2b", "R_arm", "cells", "L1|r0|640", "proceed_at_stop", "control"),
    "47/59": ("qwen3vl2b", "gates", "G2|p1|r0|448", "GO_recall"),
    "43/59": ("qwen3vl2b", "gates", "G2|p1|r0|640", "GO_recall"),
    "46/63": ("qwen3vl2b", "R_arm", "cells", "p1|r0|640", "board", "clean_board_specificity"),
}
RATES = {
    "0.797": ("qwen3vl2b", "gates", "G2|p1|r0|448", "GO_recall"),
    "0.729": ("qwen3vl2b", "gates", "G2|p1|r0|640", "GO_recall"),
    "0.73": ("qwen3vl2b", "R_arm", "cells", "p1|r0|640", "board", "clean_board_specificity"),
}


def _load():
    return json.loads(METRICS.read_text(encoding="utf-8"))


def _at(doc, path):
    cur = doc
    for key in path:
        cur = cur[key]
    return cur


def _texts():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    data = json.loads((ROOT / "site" / "site" / "data" / "data.json").read_text(encoding="utf-8"))
    phase = data["phases"][0]
    site = " ".join(item["text"] for item in phase["phase3"]["caveats"])
    return readme, site, data


def test_readme_and_site_counts_match_phase3_metrics():
    doc = _load()
    readme, site, data = _texts()
    assert data["phases"][0]["metrics"] is None
    assert data["phases"][0]["phase3"]["grid"]
    for snippet, path in COUNTS.items():
        row = _at(doc, path)
        assert f"{row['k']}/{row['n']}" == snippet
        assert snippet in readme
        if snippet in {"16/71", "22/71", "0/71", "47/59", "43/59", "46/63"}:
            assert snippet in site
    for snippet, path in RATES.items():
        row = _at(doc, path)
        assert str(row["rate"]) == snippet
        assert snippet in readme
        assert snippet in site
    l1 = _at(doc, ("qwen3vl2b", "P_arm", "cells", "L1|r0|640", "left", "proceed", "variant"))
    l2 = _at(doc, ("qwen3vl2b", "P_arm", "cells", "L2|r0|640", "left", "proceed", "variant"))
    assert (l1["k"], l1["n"]) == (16, 71)
    assert (l2["k"], l2["n"]) == (22, 71)
    assert "16/71" in site and "22/71" in site
    go896 = _at(doc, ("qwen3vl2b", "gates", "G2|p1|r0|896", "GO_recall"))
    assert (go896["k"], go896["n"], go896["rate"]) == (47, 59, 0.797)
    h2 = doc["qwen3vl2b"]["R_arm"]["H2_renamed_options_640_greedy"]
    for arm, label in (("L1", "48%"), ("L2", "29%")):
        ratio = h2[arm]["proceed_at_stop"]["ratio"]
        assert f"{round((1 - ratio) * 100)}%" == label
        assert label in readme and label in site
        assert "round((1 - ratio) * 100)" in readme and "round((1 - ratio) * 100)" in site


def test_phase3_claims_and_zero_errors():
    doc = _load()
    readme, site, _data = _texts()
    assert "LFM2-VL-1.6B" in readme
    assert "not true run-to-run variance" in readme
    assert "InternVL3-2B failed the gate" in readme
    assert "640 px" in site and "448 px" in site and "896 px" in site
    summary = doc["lfm2vl_1.6b"]["gates"]["phase3_gate_summary"]["n2|r0|448"]
    assert summary["passes_phase3_gate (G1 and G2 point)"] is True
    intern = doc["internvl3_2b"]["gates"]["phase3_gate_summary"]
    assert intern["p1|r0|448"]["passes_phase3_gate (G1 and G2 point)"] is False
    assert all(row["error_rows"] == 0 for row in doc["results_files"].values())
    assert not any("gemini" in name for name in doc["results_files"])
