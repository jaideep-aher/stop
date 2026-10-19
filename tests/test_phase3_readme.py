"""README and site Phase 3 sentences match phase3_metrics.json."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "phase3" / "analysis" / "phase3_metrics.json"

# Each README fraction is this JSON object's k/n.
README_COUNTS = {
    "53/63": ("lfm2vl_1.6b", "board_and_stop_arms_phase2_stimuli", "cells", "n2|r0|448", "board", "inject_stop", "variant"),
    "61/63": ("lfm2vl_1.6b", "board_and_stop_arms_phase2_stimuli", "cells", "n2|r0|448", "board", "bare_stop", "variant"),
    "43/71": ("lfm2vl_1.6b", "board_and_stop_arms_phase2_stimuli", "cells", "n2|r0|448", "proceed_at_stop", "variant"),
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
    site = " ".join(item["title"] + " " + item["text"] for item in phase["phase3"]["caveats"])
    return readme, site, data


def _ci(o):
    return f"{o['rate']:.3f} [{o['ci95'][0]:.2f}, {o['ci95'][1]:.2f}]"


def test_readme_and_site_counts_match_phase3_metrics():
    doc = _load()
    readme, site, data = _texts()
    phase = data["phases"][0]
    assert phase["metrics"] is None
    assert phase["phase3"]["grid"]
    for item in phase["phase3"]["caveats"]:
        assert item["title"] in readme
        assert item["text"] in readme
    for snippet, path in README_COUNTS.items():
        row = _at(doc, path)
        assert f"{row['k']}/{row['n']}" == snippet
        assert snippet in readme
    gates = doc["qwen3vl2b"]["gates"]
    for px in (448, 640, 896):
        row = gates[f"G2|p1|r0|{px}"]
        go = row["GO_recall"]
        stop = row["STOP_recall"]
        phrase = (
            f"{px} px: STOP recall {stop['k']}/{stop['n']}, "
            f"GO recall {go['k']}/{go['n']} = {_ci(go)}, BA {row['BA']}, FAIL"
        )
        assert phrase in readme and phrase in site
        assert f"{go['rate']:.3f}" in readme and f"{go['rate']:.3f}" in site
        g1 = gates[f"G1|p1|r0|{px}"]
        assert g1["gate_point"] is True
        assert f"{px} px pass" in readme and f"{px} px pass" in site
    cells = doc["qwen3vl2b"]["R_arm"]["cells"]
    for pr in ("L1", "L2", "p1"):
        pas = cells[f"{pr}|r0|640"]["proceed_at_stop"]
        phrase = f"{pas['variant']['k']}/{pas['variant']['n']} vs {pas['control']['k']}/{pas['control']['n']}"
        assert phrase in readme and phrase in site
    for pr in ("L1", "L2"):
        board = cells[f"{pr}|r0|640"]["board"]
        for key, label in (("inject_stop", "injection"), ("bare_stop", "bare STOP"), ("official", "ROAD CLOSED")):
            row = board[key]
            phrase = (
                f"{label} {row['variant']['k']}/{row['variant']['n']} vs "
                f"{row['control']['k']}/{row['control']['n']}"
            )
            assert phrase in readme and phrase in site
            assert row["holm_p"] < 0.0001
    assert "Holm p < 0.0001" in readme and "Holm p < 0.0001" in site
    assert "This applies to the PROCEED side only" in readme and "This applies to the PROCEED side only" in site
    assert "The STOP-side contrasts still hold" in readme and "The STOP-side contrasts still hold" in site
    app = (ROOT / "site" / "site" / "assets" / "app.js").read_text(encoding="utf-8")
    assert "rate.toFixed(3)" in app
    assert "· ${px} px" in app


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
