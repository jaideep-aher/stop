# PROCEED survival ratios and US R1-1 counts without the historic scene.
# Outputs phase3/analysis/survival_p3.json. Numbers are computed here, not copied.
import collections, csv, json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_p3 as ap

HERE = os.path.dirname(os.path.abspath(__file__))
N_DRAWS = 2000
SEED = 0
# Same order statistics as analyze_p3.boot / phase2 cluster bootstrap.
LO_INDEX = int(0.025 * N_DRAWS)
HI_INDEX = int(0.975 * N_DRAWS) - 1


def contrast_pairs(A, ids_v, ids_c, clusters, pos):
    rows = []
    for image_v, image_c, cluster in zip(ids_v, ids_c, clusters):
        left, right = A.get(image_v), A.get(image_c)
        if left and right and left != "UNPARSED" and right != "UNPARSED":
            rows.append((cluster, int(pos(left)), int(pos(right))))
    return rows


def proceed_pairs(A, scenes):
    return contrast_pairs(
        A,
        [f"{scene}_sboard_proceed" for scene in scenes],
        [f"{scene}_sboard_benign" for scene in scenes],
        [ap.scl[scene] for scene in scenes],
        ap.NON_STOP,
    )


def _by_cluster(pairs):
    by = collections.defaultdict(list)
    for cluster, variant, control in pairs:
        by[cluster].append(variant - control)
    return by


def mean_diff(by, keys, picks):
    total = 0
    count = 0
    for pick in picks:
        diffs = by.get(keys[int(pick)])
        if not diffs:
            continue
        total += sum(diffs)
        count += len(diffs)
    if count == 0:
        return None
    return total / count


def survival_ratio(pairs_p1, pairs_letter):
    """Cluster bootstrap of diff_letter / diff_p1.

    Clusters are the photographer ids already on the Phase 2 stop-scene manifest.
    Each draw resamples those clusters with replacement and keeps every image in a
    drawn cluster, matching analyze_p3.boot. Draws with a zero p1 difference are
    left out of the interval and counted.
    """
    by_p1 = _by_cluster(pairs_p1)
    by_letter = _by_cluster(pairs_letter)
    keys = sorted(set(by_p1) | set(by_letter))
    observed_p1 = mean_diff(by_p1, keys, range(len(keys)))
    observed_letter = mean_diff(by_letter, keys, range(len(keys)))
    observed = None if not observed_p1 else observed_letter / observed_p1
    rng = np.random.default_rng(SEED)
    draws = rng.integers(0, len(keys), size=(N_DRAWS, len(keys)))
    ratios = []
    skipped = 0
    for picks in draws:
        diff_p1 = mean_diff(by_p1, keys, picks)
        diff_letter = mean_diff(by_letter, keys, picks)
        if diff_p1 is None or diff_letter is None or diff_p1 == 0:
            skipped += 1
            continue
        ratios.append(diff_letter / diff_p1)
    ratios.sort()
    if len(ratios) != N_DRAWS:
        raise SystemExit(f"survival bootstrap skipped {skipped} of {N_DRAWS} draws; refusing a partial interval")
    return {
        "ratio_unrounded": observed,
        "diff_p1_unrounded": observed_p1,
        "diff_L_unrounded": observed_letter,
        "ci95": [round(float(ratios[LO_INDEX]), 3), round(float(ratios[HI_INDEX]), 3)],
        "n_draws": N_DRAWS,
        "seed": SEED,
        "n_pairs_p1": len(pairs_p1),
        "n_pairs_L": len(pairs_letter),
        "n_clusters": len(keys),
    }


def r11_ids(exclude_historic):
    kept, excluded = [], []
    for scene in ap.SBASES:
        row = ap.legal[scene]
        if row["us_scene"] != "yes" or row["control_type"] != "R1-1 stop sign":
            continue
        if exclude_historic and row["historic"] == "yes":
            excluded.append(scene)
            continue
        kept.append(scene)
    return kept, excluded


def pack(block):
    return {
        "variant_k": block["variant"]["k"],
        "variant_n": block["variant"]["n"],
        "variant_ci95": block["variant"]["ci95"],
        "control_k": block["control"]["k"],
        "control_n": block["control"]["n"],
        "control_ci95": block["control"]["ci95"],
        "diff": block["diff"],
        "mcnemar_p": block["mcnemar_p"],
        "n_clusters": block["n_clusters"],
    }


def p_answers(model):
    """Same left-board fill as analyze_p3.p_arm, so the US R1-1 recount uses those answers."""
    loaded, _err, _raw = ap.load(model, "P")
    board, _berr, _braw = ap.load(model, "B")
    if not loaded:
        return {}
    out = {}
    for key, answers in loaded.items():
        filled = dict(answers)
        donor = board.get(key, {})
        for scene in ap.SBASES:
            for src, dst in (("sboard_benign", "left_benign"), ("sboard_proceed", "left_proceed")):
                if f"{scene}_{dst}" not in filled and f"{scene}_{src}" in donor:
                    filled[f"{scene}_{dst}"] = donor[f"{scene}_{src}"]
            if f"{scene}_sclean" not in filled and f"{scene}_sclean" in donor:
                filled[f"{scene}_sclean"] = donor[f"{scene}_sclean"]
        out["|".join(map(str, key))] = filled
    return out


def main():
    metrics = json.load(open(os.path.join(HERE, "phase3_metrics.json")))
    qwen = ap.load("qwen3vl2b", "R")[0]
    ratios = {}
    base_key = ("p1", "r0", 640)
    for letter in ("L1", "L2"):
        ratios[letter] = survival_ratio(
            proceed_pairs(qwen[base_key], ap.SBASES),
            proceed_pairs(qwen[(letter, "r0", 640)], ap.SBASES),
        )
        stored = metrics["qwen3vl2b"]["R_arm"]["H2_renamed_options_640_greedy"][letter]["proceed_at_stop"]
        ratios[letter]["h2_ratio"] = stored["ratio"]
        ratios[letter]["h2_diff_L"] = stored["diff_L"]
        ratios[letter]["h2_diff_p1"] = stored["diff_p1"]

    kept, excluded = r11_ids(False)
    kept_ex, excluded_rows = r11_ids(True)
    historic_rows = []
    for scene in excluded_rows:
        row = ap.legal[scene]
        historic_rows.append({
            "base_id": scene,
            "historic": row["historic"],
            "country": row["country"],
            "control_type": row["control_type"],
        })
    manifest_p = list(csv.DictReader(open(f"{ap.P3}/stimuli/manifest_P.csv")))
    us_counts = {"r_arm": {}, "p_arm": {}}
    for model in ("qwen3vl2b", "internvl3_2b", "lfm2vl_1.6b"):
        loaded = ap.load(model, "R")[0]
        arm = metrics[model].get("R_arm") or {}
        sensitivity = arm.get("legal_sensitivity") or {}
        us_counts["r_arm"][model] = {}
        for key in sensitivity:
            prompt, run, side = key.split("|")
            answers = loaded.get((prompt, run, int(side)))
            if not answers:
                continue
            with_historic = ap.stop_contrast(answers, kept)
            without = ap.stop_contrast(answers, kept_ex)
            stored = sensitivity[key]["stop_US_R1-1_only"]
            if (with_historic["variant"]["k"], with_historic["variant"]["n"]) != (stored["variant"]["k"], stored["variant"]["n"]):
                raise SystemExit(f"R-arm US R1-1 recount disagrees with metrics for {model} {key}")
            us_counts["r_arm"][model][key] = {"excluding_historic": pack(without), "including_historic": pack(with_historic)}
        answers_p = p_answers(model)
        p_arm = (metrics[model].get("P_arm") or {}).get("cells") or {}
        us_counts["p_arm"][model] = {}
        for key, cell in p_arm.items():
            filled = answers_p.get(key)
            if not filled:
                continue
            us_counts["p_arm"][model][key] = {}
            for placement in ("left", "right", "lane"):
                if placement not in cell or "proceed_vs_benign_US_R1-1_only" not in cell[placement]:
                    continue
                scenes = sorted({row["base_id"] for row in manifest_p if row["placement"] == placement})
                with_ids = [scene for scene in scenes if scene in set(kept)]
                without_ids = [scene for scene in scenes if scene in set(kept_ex)]
                with_historic = ap.stop_contrast(filled, with_ids, "proceed", "benign", "{s}_" + placement + "_{v}")
                without = ap.stop_contrast(filled, without_ids, "proceed", "benign", "{s}_" + placement + "_{v}")
                stored = cell[placement]["proceed_vs_benign_US_R1-1_only"]
                if (with_historic["variant"]["k"], with_historic["variant"]["n"]) != (stored["variant"]["k"], stored["variant"]["n"]):
                    raise SystemExit(f"P-arm US R1-1 recount disagrees with metrics for {model} {key} {placement}")
                us_counts["p_arm"][model][key][placement] = {
                    "excluding_historic": pack(without),
                    "including_historic": pack(with_historic),
                }

    out = {
        "_generated_by": "phase3/analysis/survival_p3.py",
        "cluster_bootstrap": {
            "cluster": "photographer cluster_id from the Phase 2 stop-scene manifest (the same id analyze_p3.paired uses)",
            "resample": "clusters drawn with replacement; every image in a drawn cluster is kept",
            "n_draws": N_DRAWS,
            "seed": SEED,
            "interval": "sorted draw index int(0.025 * n_draws) and int(0.975 * n_draws) - 1",
            "ratio": "diff_L / diff_p1 on P(non-STOP) for ROAD CLEAR / PROCEED vs the benign board, 640 px greedy",
        },
        "proceed_survival_ratio_640_greedy": ratios,
        "us_r11": {
            "rule": "us_scene yes and control_type R1-1 stop sign, then drop historic yes",
            "n_including_historic": len(kept),
            "n_excluding_historic": len(kept_ex),
            "excluded": historic_rows,
            "counts": us_counts,
        },
    }
    dest = os.path.join(HERE, "survival_p3.json")
    json.dump(out, open(dest, "w"), indent=1)
    print("wrote", dest)


if __name__ == "__main__":
    main()
