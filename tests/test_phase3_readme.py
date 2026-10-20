"""Short README counts match the results JSON. Site and hash checks stay on their own files."""

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "results" / "phase3" / "phase3_metrics.json"
CHANGES = ROOT / "docs" / "changes.md"
PREREG_SHA = "3f00017a0c4889bb6adc4ce920521c6c26e951836cbc240c7a8a907b89d6d1e1"
LABELER = (
    "Labels come from a single labeler; a second human rater and agreement statistics are future work."
)


def _load():
    return json.loads(METRICS.read_text(encoding="utf-8"))


def _readme():
    return (ROOT / "README.md").read_text(encoding="utf-8")


def _pair(row):
    return f"{row['k']}/{row['n']}"


def test_readme_quotes_json_counts():
    doc = _load()
    readme = _readme()
    p2 = json.loads((ROOT / "results" / "phase2" / "phase2_metrics.json").read_text(encoding="utf-8"))
    addendum = json.loads(
        (ROOT / "results" / "phase3" / "phase3_addendum_metrics.json").read_text(encoding="utf-8")
    )
    gates = doc["qwen3vl2b"]["gates"]["phase3_gate_summary"]
    assert gates["p1|r0|640"]["passes_phase3_gate (G1 and G2 point)"] is False
    assert gates["n3|r0|448"]["passes_phase3_gate (G1 and G2 point)"] is True
    qwen = doc["qwen3vl2b"]["R_arm"]["cells"]["p1|r0|640"]
    passing = doc["qwen3vl2b"]["R_arm"]["cells"]["n3|r0|448"]
    inject = qwen["board"]["inject_stop"]
    proceed = qwen["proceed_at_stop"]
    passed_inject = passing["board"]["inject_stop"]
    passed_proceed = passing["proceed_at_stop"]
    lfm = doc["lfm2vl_1.6b"]["board_and_stop_arms_phase2_stimuli"]["cells"]["n2|r0|448"]["proceed_at_stop"]
    lane = doc["qwen3vl2b"]["P_arm"]["cells"]["p1|r0|640"]["lane"]["proceed"]
    intern_l1 = addendum["letter_arms"]["internvl3_2b|L1|r0|448"]["board_STOP_side_vs_benign"]["inject_stop"]
    intern_l2 = addendum["letter_arms"]["internvl3_2b|L2|r0|448"]["board_STOP_side_vs_benign"]["inject_stop"]
    gemini = p2["gemini"]["stop_scenes"]["sboard_proceed"]["non_stop_rate"]
    letters = {
        letter: doc["qwen3vl2b"]["R_arm"]["cells"][f"{letter}|r0|640"]["proceed_at_stop"]
        for letter in ("L1", "L2")
    }
    assert _pair(inject["variant"]) == "62/63" and _pair(inject["control"]) == "13/63"
    assert _pair(proceed["variant"]) == "45/71" and _pair(proceed["control"]) == "14/71"
    assert _pair(passed_inject["variant"]) == "63/63" and _pair(passed_inject["control"]) == "17/63"
    assert _pair(passed_proceed["variant"]) == "48/71" and _pair(passed_proceed["control"]) == "2/71"
    assert _pair(lfm["variant"]) == "43/71" and _pair(lfm["control"]) == "14/71"
    assert _pair(gemini) == "0/71"
    assert _pair(lane["variant"]) == "30/32" and _pair(lane["control"]) == "10/32"
    assert _pair(intern_l1["variant"]) == "62/63" and _pair(intern_l1["control"]) == "9/63"
    assert _pair(intern_l2["variant"]) == "62/63" and _pair(intern_l2["control"]) == "10/63"
    assert letters["L1"]["variant"]["k"] == 16 and letters["L2"]["variant"]["k"] == 22
    assert letters["L1"]["control"]["k"] == letters["L2"]["control"]["k"] == 0
    gemini_pass = [
        row["prompt"]
        for row in p2["_gate"]
        if row["model"] == "gemini" and row["source"] == "phase2" and row["status"] == "PASS"
    ]
    assert gemini_pass == ["n2", "n3"]
    for snippet in (
        "main wording; this wording misses the stricter gate",
        "62/63 vs 13/63",
        "45/71 vs 14/71",
        "63/63 vs 17/63",
        "48/71 vs 2/71",
        "after seeing the results",
        "43/71 vs 14/71",
        "0/71",
        "16/71",
        "22/71",
        "30/32",
        "10/32",
        "62/63 vs 9/63",
        "62/63 vs 10/63",
        "consistent with copying",
        "passed on more than one wording",
        "InternVL3-2B passes the gate",
        "LFM2-VL-1.6B passes the gate",
    ):
        assert snippet in readme


def test_readme_is_first_person_and_short():
    readme = _readme()
    assert "https://who-gets-to-say-stop-site-production.up.railway.app" in readme
    assert "poster/poster.pdf" in readme
    assert "poster_final" not in readme
    assert LABELER in readme
    assert readme.count("Cursor was used to help in this project.") == 1
    assert "I labeled" not in readme
    for banned in ("Phase 2", "Phase 3", "Jay's", "the author", "Grok", "talk script", "## Misuse"):
        assert banned not in readme
    assert "SOTIF" in readme and "UL 4600" in readme and "NHTSA" in readme
    assert "MUTCD" in readme
    assert len(readme.split()) < 650


def test_phase3_gate_facts_stay_in_json():
    doc = _load()
    summary = doc["lfm2vl_1.6b"]["gates"]["phase3_gate_summary"]["n2|r0|448"]
    assert summary["passes_phase3_gate (G1 and G2 point)"] is True
    intern = doc["internvl3_2b"]["gates"]["phase3_gate_summary"]
    assert intern["p1|r0|448"]["passes_phase3_gate (G1 and G2 point)"] is False
    assert intern["L1|r0|448"]["passes_phase3_gate (G1 and G2 point)"] is True
    assert intern["L2|r0|448"]["passes_phase3_gate (G1 and G2 point)"] is True
    assert doc["internvl3_2b"].get("R_arm") is None
    assert all(row["error_rows"] == 0 for row in doc["results_files"].values())
    assert not any("gemini" in name for name in doc["results_files"])
    data = json.loads((ROOT / "site" / "data" / "data.json").read_text(encoding="utf-8"))
    phase = data["phases"][0]
    assert phase["metrics"] is None
    assert phase["phase3"]["grid"]
    assert phase["phase3"]["caveats"]
    app = (ROOT / "site" / "assets" / "app.js").read_text(encoding="utf-8")
    assert "rate.toFixed(3)" in app
    assert "· ${px} px" in app
    assert "INCOMPLETE" in app


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
    changes = CHANGES.read_text(encoding="utf-8")
    assert "23 scored L1 rows and 23 scored L2 rows" in changes


def test_phase3_hashes_and_g2_deviation_are_logged():
    changes = CHANGES.read_text(encoding="utf-8")
    metrics_sha = hashlib.sha256(METRICS.read_bytes()).hexdigest()
    survival_sha = hashlib.sha256((ROOT / "results" / "phase3" / "survival_p3.json").read_bytes()).hexdigest()
    g2_sha = hashlib.sha256((ROOT / "data" / "manifests" / "phase3" / "g2_labels.csv").read_bytes()).hexdigest()
    addendum_sha = hashlib.sha256(
        (ROOT / "results" / "phase3" / "phase3_addendum_metrics.json").read_bytes()
    ).hexdigest()
    prereg_sha = hashlib.sha256((ROOT / "docs" / "PREREG.md").read_bytes()).hexdigest()
    assert prereg_sha == PREREG_SHA
    assert metrics_sha == "c6c1c981ad551295e795db3ae470346df6149cde73ceca9ff88ee30be11d2e2a"
    assert metrics_sha in changes
    assert survival_sha in changes
    assert addendum_sha in changes
    assert g2_sha in changes
    assert "e45d31b857eaed374c5ae9b886af20c687fe322bc3279b9d9e4576b3271b9092" in changes
    assert not (ROOT / "docs" / "DEVIATIONS.md").exists()
    assert not (ROOT / "docs" / "ERRATA.md").exists()


def test_survival_json_matches_the_metrics_file():
    surv = json.loads((ROOT / "results" / "phase3" / "survival_p3.json").read_text(encoding="utf-8"))
    ratios = surv["proceed_survival_ratio_640_greedy"]
    doc = _load()
    h2 = doc["qwen3vl2b"]["R_arm"]["H2_renamed_options_640_greedy"]
    for letter in ("L1", "L2"):
        assert ratios[letter]["h2_ratio"] == h2[letter]["proceed_at_stop"]["ratio"]
        assert ratios[letter]["n_draws"] == surv["cluster_bootstrap"]["n_draws"] == 2000
        assert ratios[letter]["seed"] == surv["cluster_bootstrap"]["seed"] == 0
        assert ratios[letter]["n_pairs_p1"] == 71
    excluded = surv["us_r11"]["excluded"]
    assert [row["base_id"] for row in excluded] == ["stop2_136"]
    assert excluded[0]["historic"] == "yes"
    data = json.loads((ROOT / "site" / "data" / "data.json").read_text(encoding="utf-8"))
    cells = data["phases"][0]["phase3"]["lfm2"]["cells"]
    assert "board" in cells["n2|r0|448"]
    stored = doc["lfm2vl_1.6b"]["gates"]["G1|L1|r0|448"]
    shown = data["phases"][0]["phase3"]["lfm2"]["gates"]["G1|L1|r0|448"]
    assert shown["n_scored"] == stored["n_scored"] == 94
    assert shown["n_expected"] == stored["n_expected"] == 94
    assert shown["status"] is None
    assert "status" not in stored


def test_addendum_and_manifest_stay_internally_consistent():
    addendum = json.loads(
        (ROOT / "results" / "phase3" / "phase3_addendum_metrics.json").read_text(encoding="utf-8")
    )
    arms = addendum["letter_arms"]
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
    l1 = arms["internvl3_2b|L1|r0|448"]["PROCEED_side_nonSTOP_proceed_vs_benign"]
    assert l1["mcnemar_p"] == 0.0001220703125 and l1["cluster_signflip_p"] == 0.0086
    assert addendum["capped_gate"]["internvl3_2b|L1|r0|448"]["full"]["passes"] is True
    assert addendum["capped_gate"]["internvl3_2b|L2|r0|448"]["full"]["passes"] is True
    assert addendum["capped_gate"]["lfm2vl_1.6b|L1|r0|448"]["full"]["passes"] is False
    assert addendum["capped_gate"]["lfm2vl_1.6b|L2|r0|448"]["full"]["passes"] is False
    assert len(addendum["capped_gate"]) == 25
    stop = addendum["capped_gate_sets"]["G2"]["STOP"]
    assert stop["top_share_after"] == 0.294 and stop["n_after"] == 17
    data = json.loads((ROOT / "site" / "data" / "data.json").read_text(encoding="utf-8"))
    shown = data["phases"][0]["phase3"]["addendum"]
    assert shown["claims"]["stop_side_supported"] is True
    assert shown["claims"]["gate_changes"] == []
    assert shown["claims"]["n_gate_cells"] == 25
    assert shown["claims"]["residual_top_share_STOP"]["G2"] == 0.294
    script = (ROOT / "scripts" / "analyze_addendum.py").read_text(encoding="utf-8")
    assert "/workspace/" not in script
    manifest = (ROOT / "data" / "manifests" / "phase3" / "manifest_Bkey.csv").read_text(encoding="utf-8")
    assert "/workspace/" not in manifest
    header = manifest.splitlines()[0]
    assert "credit" in header and "license" in header and "source_url" in header
    locks = [
        line.split()[-1]
        for line in (ROOT / "configs" / "models.lock").read_text(encoding="utf-8").splitlines()
        if line.endswith(".gguf") and not line.split()[-1].startswith("mmproj-")
    ]
    assert len(locks) == 6
