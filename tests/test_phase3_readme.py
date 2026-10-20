"""README and site Phase 3 sentences match phase3_metrics.json."""

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "results" / "phase3" / "phase3_metrics.json"

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
    data = json.loads((ROOT / "site" / "data" / "data.json").read_text(encoding="utf-8"))
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
    app = (ROOT / "site" / "assets" / "app.js").read_text(encoding="utf-8")
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
    assert intern["L1|r0|448"]["passes_phase3_gate (G1 and G2 point)"] is True
    assert intern["L2|r0|448"]["passes_phase3_gate (G1 and G2 point)"] is True
    assert doc["internvl3_2b"].get("R_arm") is None
    assert all(row["error_rows"] == 0 for row in doc["results_files"].values())
    assert not any("gemini" in name for name in doc["results_files"])
    assert "two gate-passing models" not in readme.lower()
    assert "out of six tried" in readme and "out of six tried" in site
    assert "was not run on the study arms" in readme and "was not run on the study arms" in site
    assert "What this does not show" in readme
    assert readme.count("Cursor was used to help in this project.") == 1
    assert "Grok" not in readme


def _fmt_num(value):
    if value == 0:
        return "0"
    if value == 1:
        return "1.0"
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _fmt_kn(row):
    return f"{row['k']}/{row['n']} [{_fmt_num(row['ci95'][0])}, {_fmt_num(row['ci95'][1])}]"


def test_headline_table_matches_phase3_metrics():
    doc = _load()
    readme, _site, _data = _texts()
    cells = doc["qwen3vl2b"]["R_arm"]["cells"]
    for key in ("p1|r0|640", "n3|r0|448", "L1|r0|640", "L2|r0|640"):
        cell = cells[key]
        for name in ("inject_stop", "bare_stop", "official"):
            board = cell["board"][name]
            phrase = f"{_fmt_kn(board['variant'])} vs {_fmt_kn(board['control'])}"
            assert phrase in readme
        assert _fmt_kn(cell["board"]["clean_board_specificity"]) in readme
        proceed = cell["proceed_at_stop"]
        assert f"{_fmt_kn(proceed['variant'])} vs {_fmt_kn(proceed['control'])}" in readme
    planned = doc["qwen3vl2b"]["R_arm"]["robustness_summary"]["planned_18_cells_word_prompts_448_896"]
    h1 = (
        "H1 as preregistered (contrasts hold in every robustness cell) was not met. "
        f"In the 18 planned cells, inject is {planned['inject_stop']['cells_significant_positive_holm_or_mcnemar']}/"
        f"{planned['inject_stop']['cells_present']}, bare STOP is "
        f"{planned['bare_stop']['cells_significant_positive_holm_or_mcnemar']}/{planned['bare_stop']['cells_present']}, "
        f"and ROAD CLOSED is {planned['official']['cells_significant_positive_holm_or_mcnemar']}/"
        f"{planned['official']['cells_present']}."
    )
    assert h1 in readme
    assert "Choosing which cell to headline is post hoc" in readme
    headline = readme.split("## Why it matters", 1)[0]
    proceed = "fragile; depends on letter mapping; consistent with answer-word or position copying; not directly tested"
    assert proceed in headline
    assert "likely" not in headline.lower()
    assert "The plan was hashed locally before the runs and committed later" in readme
    locks = [
        line.split()[-1]
        for line in (ROOT / "configs" / "models.lock").read_text(encoding="utf-8").splitlines()
        if line.endswith(".gguf") and not line.split()[-1].startswith("mmproj-")
    ]
    assert len(locks) == 6
    for name in (
        "SmolVLM-500M",
        "SmolVLM2-2.2B",
        "Qwen2.5-VL-3B",
        "InternVL3-2B",
        "Qwen3-VL-2B",
        "LFM2-VL-1.6B",
    ):
        assert any(name in path for path in locks)
        assert name in readme


def test_survival_and_us_r11_json_are_quoted():
    readme, site, data = _texts()
    surv = json.loads((ROOT / "results" / "phase3" / "survival_p3.json").read_text(encoding="utf-8"))
    ratios = surv["proceed_survival_ratio_640_greedy"]
    doc = _load()
    h2 = doc["qwen3vl2b"]["R_arm"]["H2_renamed_options_640_greedy"]
    for letter in ("L1", "L2"):
        assert ratios[letter]["h2_ratio"] == h2[letter]["proceed_at_stop"]["ratio"]
        assert ratios[letter]["n_draws"] == surv["cluster_bootstrap"]["n_draws"] == 2000
        assert ratios[letter]["seed"] == surv["cluster_bootstrap"]["seed"] == 0
        assert ratios[letter]["n_pairs_p1"] == 71
        phrase = (
            f"{letter} {ratios[letter]['h2_ratio']} "
            f"(cluster-bootstrap 95% CI {json.dumps(ratios[letter]['ci95'])})"
        )
        assert phrase in readme and phrase in site
    excluded = surv["us_r11"]["excluded"]
    assert [row["base_id"] for row in excluded] == ["stop2_136"]
    assert excluded[0]["historic"] == "yes"
    us = surv["us_r11"]["counts"]

    def pair(block):
        return f"{block['variant_k']}/{block['variant_n']} vs {block['control_k']}/{block['control_n']}"

    p1 = us["r_arm"]["qwen3vl2b"]["p1|r0|640"]
    right = us["p_arm"]["lfm2vl_1.6b"]["n2|r0|448"]["right"]
    sentence = (
        f"US R1-1 stop scenes excluding historic stop2_136, p1 / r0 / 640 PROCEED-at-STOP is {pair(p1['excluding_historic'])}"
        f" (including that scene, {pair(p1['including_historic'])})."
        f" LFM2 n2 / 448 right placement is {pair(right['excluding_historic'])} excluding it"
        f" and {pair(right['including_historic'])} including it."
    )
    assert sentence in readme and sentence in site
    cells = data["phases"][0]["phase3"]["lfm2"]["cells"]
    assert "board" in cells["n2|r0|448"]
    stored = doc["lfm2vl_1.6b"]["gates"]["G1|L1|r0|448"]
    shown = data["phases"][0]["phase3"]["lfm2"]["gates"]["G1|L1|r0|448"]
    assert shown["n_scored"] == stored["n_scored"] == 94
    assert shown["n_expected"] == stored["n_expected"] == 94
    assert shown["status"] is None
    assert "status" not in stored


def test_lfm2_letter_rows_in_the_checkout_are_incomplete_under_gate_py():
    sys.path.insert(0, str(ROOT / "scripts"))
    import analyze_p3 as analyze
    from whostop.gate import evaluate_competence_gate

    doc = _load()
    labels = {
        row["image_id"]: row["label"]
        for row in csv.DictReader((ROOT / "data" / "manifests" / "phase3" / "manifest_G1.csv").open(encoding="utf-8"))
    }
    n_stop = sum(label == "STOP" for label in labels.values())
    n_go = sum(label == "PROCEED" for label in labels.values())
    loaded = analyze.load("lfm2vl_1.6b", "G1")[0]
    summary = doc["lfm2vl_1.6b"]["gates"]["phase3_gate_summary"]
    assert summary["L1|r0|448"]["passes_phase3_gate (G1 and G2 point)"] is False
    assert summary["L2|r0|448"]["passes_phase3_gate (G1 and G2 point)"] is False
    for prompt in ("L1", "L2"):
        answers = loaded[(prompt, "r0", 448)]
        scored = [
            {"label": labels[image], "action": action}
            for image, action in answers.items()
            if labels.get(image) in ("STOP", "PROCEED")
        ]
        status = evaluate_competence_gate(scored, n_stop=n_stop, n_go=n_go)["status"]
        row = doc["lfm2vl_1.6b"]["gates"][f"G1|{prompt}|r0|448"]
        assert status == "INCOMPLETE"
        assert len(scored) == 23
        assert row["n_scored"] == row["n_expected"] == n_stop + n_go == 94
        assert "status" not in row
    readme, site, _data = _texts()
    assert "n_scored` 94 and `n_expected` 94" in readme
    assert "fails the gate with letter answers" in readme and "fails the gate with letter answers" in site
    app = (ROOT / "site" / "assets" / "app.js").read_text(encoding="utf-8")
    assert "INCOMPLETE" in app
    deviations = (ROOT / "docs" / "DEVIATIONS.md").read_text(encoding="utf-8")
    assert "23 scored L1 rows and 23 scored L2 rows" in deviations


def test_phase3_hashes_and_g2_deviation_are_logged():
    readme, _site, _data = _texts()
    metrics_sha = hashlib.sha256(METRICS.read_bytes()).hexdigest()
    survival = ROOT / "results" / "phase3" / "survival_p3.json"
    survival_sha = hashlib.sha256(survival.read_bytes()).hexdigest()
    g2_sha = hashlib.sha256((ROOT / "data" / "manifests" / "phase3" / "g2_labels.csv").read_bytes()).hexdigest()
    deviations = (ROOT / "docs" / "DEVIATIONS.md").read_text(encoding="utf-8")
    docs = (ROOT / "docs" / "DEVIATIONS.md").read_text(encoding="utf-8")
    assert metrics_sha in readme and metrics_sha in deviations
    assert survival_sha in readme and survival_sha in deviations
    assert g2_sha in deviations and g2_sha in docs
    assert "e45d31b857eaed374c5ae9b886af20c687fe322bc3279b9d9e4576b3271b9092" in deviations
    assert "e45d31b857eaed374c5ae9b886af20c687fe322bc3279b9d9e4576b3271b9092" in docs
    addendum = ROOT / "results" / "phase3" / "phase3_addendum_metrics.json"
    addendum_sha = hashlib.sha256(addendum.read_bytes()).hexdigest()
    assert addendum_sha in readme and addendum_sha in deviations
    assert "c6c1c981ad551295e795db3ae470346df6149cde73ceca9ff88ee30be11d2e2a" == metrics_sha


def test_addendum_headline_matches_json():
    readme, _site, data = _texts()
    addendum = json.loads(
        (ROOT / "results" / "phase3" / "phase3_addendum_metrics.json").read_text(encoding="utf-8")
    )
    arms = addendum["letter_arms"]
    headline = readme.split("## Why it matters", 1)[0]
    assert "likely" not in headline.lower()
    phrase = "fragile; depends on letter mapping; consistent with answer-word or position copying; not directly tested"
    assert phrase in headline
    for key, official, inject, bare, proceed_k, proceed_c, holm in (
        ("internvl3_2b|L1|r0|448", (49, 9), (62, 9), (60, 9), 16, 2, 0.0),
        ("internvl3_2b|L2|r0|448", (57, 10), (62, 10), (60, 10), 1, 0, 0.0),
    ):
        board = arms[key]["board_STOP_side_vs_benign"]
        assert (board["official"]["variant"]["k"], board["official"]["control"]["k"]) == official
        assert (board["inject_stop"]["variant"]["k"], board["inject_stop"]["control"]["k"]) == inject
        assert (board["bare_stop"]["variant"]["k"], board["bare_stop"]["control"]["k"]) == bare
        assert board["official"]["holm_p"] == board["inject_stop"]["holm_p"] == board["bare_stop"]["holm_p"] == holm
        proceed = arms[key]["PROCEED_side_nonSTOP_proceed_vs_benign"]
        assert proceed["variant"]["k"] == proceed_k and proceed["control"]["k"] == proceed_c
        assert f"{proceed_k}/71 vs {proceed_c}/71" in headline
    l1 = arms["internvl3_2b|L1|r0|448"]["PROCEED_side_nonSTOP_proceed_vs_benign"]
    assert l1["mcnemar_p"] == 0.0001220703125 and l1["cluster_signflip_p"] == 0.0086
    assert "0.0001220703125" in headline and "0.0086" in headline
    l2 = arms["internvl3_2b|L2|r0|448"]["PROCEED_side_nonSTOP_proceed_vs_benign"]
    assert l2["mcnemar_p"] == 1.0
    assert addendum["capped_gate"]["internvl3_2b|L1|r0|448"]["full"]["passes"] is True
    assert addendum["capped_gate"]["internvl3_2b|L2|r0|448"]["full"]["passes"] is True
    assert addendum["capped_gate"]["lfm2vl_1.6b|L1|r0|448"]["full"]["passes"] is False
    assert addendum["capped_gate"]["lfm2vl_1.6b|L2|r0|448"]["full"]["passes"] is False
    assert len(addendum["capped_gate"]) == 25
    assert "25 cells" in headline
    stop = addendum["capped_gate_sets"]["G2"]["STOP"]
    assert stop["top_share_after"] == 0.294 and stop["n_after"] == 17
    assert "0.294" in headline and "`n_after` 17" in headline
    shown = data["phases"][0]["phase3"]["addendum"]
    assert shown["claims"]["stop_side_supported"] is True
    assert shown["claims"]["gate_changes"] == []
    assert shown["claims"]["n_gate_cells"] == 25
    assert shown["claims"]["residual_top_share_STOP"]["G2"] == 0.294
    script = (ROOT / "scripts" / "analyze_addendum.py").read_text(encoding="utf-8")
    assert "/workspace/rai_pivot" not in script
    manifest = (ROOT / "data" / "manifests" / "phase3" / "manifest_Bkey.csv").read_text(encoding="utf-8")
    assert "/workspace/" not in manifest
    assert "credit" in manifest.splitlines()[0] and "license" in manifest.splitlines()[0] and "source_url" in manifest.splitlines()[0]
