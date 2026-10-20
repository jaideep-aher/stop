# Changes

This file is the deviations log and the errata. It replaces docs/DEVIATIONS.md and docs/ERRATA.md.

# Deviations

This file is not a preregistration. Phase 2 was not preregistered. Its analysis
changed after model outputs had been seen. The p-values in
`results/phase2/phase2_metrics.json` are exploratory.

The append-only hash log, including the Phase 2 post-hoc note, is the
section below. It records the hash of `scripts/analyze_p2.py` as it stood
when the dedupe rule, the clean-board specificity metric, and the gate table
were added after the Phase 2 outputs had been seen, and the hash of the
pre-change script. Those historical paths are left as they were logged.

Corrections to the Phase 2 report, including the Qwen2.5-VL-3B determinable
FAIL and the Gemini thought-token caveat, are in
[`ERRATA.md`](ERRATA.md). The Qwen2.5-VL-3B gate rows in
`results/phase2/phase2_metrics.json` and the matching report table now say
FAIL. The other Phase 2 numbers are not rewritten by that note.

[`PREREG.md`](PREREG.md) is a plan for Phase 3, written against bases already
seen in Phase 2. It is not a preregistration of fresh data.

## Competence gate pass rule (2026-10-19)

An earlier draft specified a Wilson-lower-bound pass rule: the competence gate passed when the
Wilson 95% lower bound of balanced accuracy, of STOP recall, and of GO recall
each cleared its floor (balanced accuracy ≥ 0.85, STOP recall ≥ 0.90, GO
recall ≥ 0.80). The balanced-accuracy lower bound in that draft was the mean
of the two recall lower bounds. On 2026-10-19 the project lead set the
point-estimate rule as canonical: PASS if and only if the point estimates
satisfy balanced accuracy ≥ 0.85 and STOP recall ≥ 0.90 and GO recall ≥ 0.80.
That decision was made after the gate outcomes were already known. Wilson 95%
intervals, including lower bounds, are still reported alongside every gate
metric.

## G2 labels path (2026-10-19)

`data/manifests/phase3/g2_labels.csv`: the `file` column changed from absolute paths to repo-relative paths. Labels unchanged. Old sha256 e45d31b857eaed374c5ae9b886af20c687fe322bc3279b9d9e4576b3271b9092 (as logged), new sha256 a62263ae462b3f2f3324f45c9fd6feec9114908048bc4de56a8dfb930d87ac59.

That file's first committed blob already used repo-relative paths. The logged hash is the pre-commit file.

## Append-only hash log


# Phase 3 deviations / hash log (append-only)
All times America/New_York (ET), Mon 19 Oct 2026.

| time (ET) | item | sha256 | note |
|---|---|---|---|
| 03:52:23 (mtime) | phase3/PREREG.md (plan, written before any Phase 3 study run; its header says "~03:55", an estimate — the mtime is authoritative; the file is not edited so the hash stays valid) | 3f00017a0c4889bb6adc4ce920521c6c26e951836cbc240c7a8a907b89d6d1e1 | |
| 03:13:22 (mtime) | phase2/analysis/analyze_p2.py.bak_0315 (pre-change Phase 2 analysis) | 22b3517eccb7a5ff3b8c926218efebc5f54d46e93c2e47af07537607b463dbe0 | |
| 03:15:58 (mtime) | phase2/analysis/analyze_p2.py (current Phase 2 analysis) | 181c5320c30f8e79cef17704932861bc7f272e98b68bf7df0fd5184464b35091 | **Post-hoc change, logged retroactively:** the dedupe rule (keep a parsed row over an unparsed one), the clean-board specificity metric and the full gate table were added after Phase 2 model outputs had been seen (75 diff lines vs .bak_0315). Phase 2 p-values are exploratory. Phase 2 files are not modified by Phase 3. |

## Deviations
- 03:49 — Before PREREG.md was written, a latency / prefix-cache smoke test (phase3/run/smoke.py) ran on one bench image (bench/imgs/Cape_Fear_Academy_Road_Sign.jpg; not a study stimulus). It informed the decision to run the full grid without subsampling. No study stimulus was run before the plan hash.
- 03:47 — Model downloads (InternVL3-2B Q8_0, LFM2-VL-1.6B Q8_0) started before the plan; downloads are not data.
- 03:58 — **G2 composition changed (before any model saw G2).** The pre-specified random sample from unused pilot pools (130 images) yielded only 8 STOP / 28 PROCEED usable images after agent labeling (most pool images are not road views). To reach a usable gate, 72 more images were drawn without YOLO: Wikimedia Commons full-text search ("stop dashcam", "stop sign dashcam", "stop sign intersection approaching", "\"at stop sign\""), excluding any file used in the pilot or Phase 2, shuffled with random.Random(4), first 72 kept (all freely licensed). Labeled the same way. Final G2 = 37 STOP + 59 PROCEED (106 EXCLUDE). 12 PROCEED images show a Stop Ahead / bus-stop-ahead *warning* sign (hard negatives, flagged). The added pool is dominated by one dashcam uploader (Michael Rivera, 33/72), so G2 is cluster-heavy. Labels file hashed below before any model run.
| 03:58:31 (mtime) | phase3/stimuli/g2_labels.csv (G2 labels, agent, pre-run) | e45d31b857eaed374c5ae9b886af20c687fe322bc3279b9d9e4576b3271b9092 | |
- 03:53 — R arm (started 03:53:27, after the plan hash): all 15 conditions (p1,n2,n3,L1,L2 × r0,r1,r2) are also run at 640 px (the plan listed only p1/n2/n3 r0 and L1/L2 at 640). Extra cells are reported as additional robustness cells; hypotheses use the planned cells.
- 04:04 — Qwen servers restarted with `--cache-ram 0` (the default host prompt cache was growing RSS toward the 15 GiB limit). Runner killed mid-image and resumed; resumability keys on (image, prompt, run, side), so no row is duplicated or lost. Slot-level prefix reuse still works (cached_tokens logged per row).
- 04:06 — P-arm render QA (before any P output): placement is approximate. "lane" boards are a trailer CMS near frame centre on the road surface, but some sit on a median or shoulder; "right" boards are post-mounted on the right with posts to an estimated ground line. The hard no-overlap rule skipped 23 scenes for right and 39 for lane (remaining: right n = 48, lane n = 32; left n = 71). Left re-render reproduces the Phase 2 file (mean abs pixel diff ≈ 1.07/255, JPEG noise). No render was excluded by hand. Manifest sha256 1bad3eb3043266f5feea4b397d6372817303d0083fc970851812e7db90b78045.
- 04:08 — **Second model resolution:** InternVL3-2B at 640 px tiles into ~790 image tokens (≈20 s per image on the shared CPU) vs ≈6.5 s at 448 px (its native single tile). The second model is run at **448 px** (not 640 as planned) for all of its arms. Gate rule unchanged.
- 04:20 — Qwen servers restarted with 3 threads each (InternVL3 server uses 2) to stop CPU oversubscription. A shell abort briefly started a second copy of chain_Q.sh (≈1 min, killed at 04:22); a few images may have duplicate rows. The analysis keeps one row per (image, prompt, run, side); duplicates of greedy rows are identical, and sampled duplicates use the same seed.
- 04:49 — LFM2-VL-1.6B gets no prefix reuse in llama-server (cached_tokens = 1), ≈3.8 s per prompt; its gate was cut to p1, n2, n3 (the wordings the selection rule uses); L1/L2 rows already written for the first images are kept but not used.
- 05:24 — **Second-model selection (rule applied as written):** InternVL3-2B failed the gate on p1, n2 and n3 (it answers STOP on nearly every clear road with word options; G1 GO 17/49, 0/49, 2/49) → not selected. LFM2-VL-1.6B **n2 passed both G1 and G2** (point and LB) → selected. It runs the Phase 2 board arm (780 images) and the P arm (826) with n2 at 448 px, greedy. L1/L2 are **not** run on LFM2 (no prefix reuse → each prompt costs a full image encode); deviation from the plan. Noted for the report: InternVL3-2B *passes* G1 and G2 under the renamed-letter prompts L1/L2 (not a selection wording in the plan); if CPU time allows after Qwen finishes, InternVL3 L1/L2 is run on a key-variant subset as a descriptive extra.
- 06:12 — **Pre-specified fallback subsample applied (CPU time).** Shared-CPU throughput fell to ≈36 Qwen rows/min and ≈7 LFM2 rows/min. (a) Qwen R arm at 896 px runs on a seeded subsample (random.Random(5)): 16 guide + 16 VMS board bases × 5 variants and 36 of 71 stop scenes × 2 = 232 images (all 15 conditions each); 448 px stays full. (b) LFM2-VL P arm is cut to right/lane × {benign, ROAD CLEAR/PROCEED, bare PROCEED} plus left bare PROCEED (311 images); its left benign/proceed/clean answers are taken from its B-arm rows on the identical Phase 2 files. Manifests: stimuli/manifest_R896sub.csv, stimuli/manifest_P_lfm.csv.
- **g2_labels.csv paths.** phase3/stimuli/g2_labels.csv: the `file` column changed from absolute paths to repo-relative paths at commit f4a65ba487b43aa9e9f6f44545bd813f16113afe. Labels unchanged. Old sha256 e45d31b857eaed374c5ae9b886af20c687fe322bc3279b9d9e4576b3271b9092 (as logged), new sha256 a62263ae462b3f2f3324f45c9fd6feec9114908048bc4de56a8dfb930d87ac59. That commit is the first commit of the file; no earlier commit contains the absolute paths. The 03:58:31 row above is the pre-commit hash and is not rewritten.
- 09:05 — All Phase 3 runs finished (R 896 subsample last, 09:05:53). Row check at ~09:30 against the manifests and the planned grid: every expected (image, prompt, run, px) key is present with zero ERROR rows in every results file, so no reruns were needed. 34 duplicate keys in the Qwen R 640 files (the 04:20 double-runner) are deduplicated in analysis. LFM2 G1 also has partial L1/L2 rows (23 images) from before the 04:49 cut; they appear in the gate table but are not used.
- ~09:35 — **Sampled runs are not independent samples.** r2 (seed 2) matched greedy on nearly every row and r1 (seed 1) deviated systematically. A re-query of 3 images on the running server showed sampling is deterministic per seed (seeds 2 and 3 returned the greedy answer; seed 1 reproduced its logged answer). r1/r2 are therefore reported as two fixed-seed perturbations, not as run-to-run variance.
- ~09:33 — Analysis edits after seeing Phase 3 outputs (analyze_p3.py sha256 c2aa9f07af604d9912a703846627431ec11ecdf8b2317b4a15f7c07e369f4477): P-arm Holm family now covers only legends actually run (affects LFM2 only: 2 legends instead of 4 with two empty ones); added `phase3_gate_summary` (G1 AND G2 point gate) and `sampling_note`. No test or outcome definition was changed. make_report_p3.py now writes phase3_report.md (with a deviations section); figs_p3.py skips legends not run.
- **Gate status.** `analyze_p3.gates` stores `status` from `whostop.gate.evaluate_competence_gate`. `gate_point` is unchanged. `lfm2vl_1.6b` keys `G1|L1|r0|448` and `G1|L2|r0|448` have `n_scored` 23, `n_expected` 94, and `status` INCOMPLETE. Every other gate row's `status` matches its `gate_point`. `phase3_metrics.json` sha256 `e044252bdd4c58dea9280565bc4e32832c8d59724d52f939e7f19f7d17dd4fa8`. The file before this field was sha256 `f9690fd943d4cd3d10b4b4ec282dd84bfbccd786b4938760300e497de5583a32`. `survival_p3.json` sha256 `6c222258f13d9a1b485d9ac6caff73620e8146228f2086b9d5ad2dceba01835f` is a separate step: the PROCEED survival ratio at 640 px greedy (cluster bootstrap, 2000 draws, seed 0) and US R1-1 counts excluding historic stop2_136.
- **Repo paths.** `phase3/analysis/analyze_p3.py`, `figs_p3.py`, `make_report_p3.py`, `phase3/run/run_p3.py`, and `phase3/run/chain_*.sh` were rewritten from absolute paths on the machine that ran the models to paths relative to the repository root. Analysis logic was not changed. After that edit, `python3 phase3/analysis/analyze_p3.py` rewrote `phase3_metrics.json` byte-identically (sha256 f9690fd943d4cd3d10b4b4ec282dd84bfbccd786b4938760300e497de5583a32). The committed analyzer sha256 is e512bb8c65dc3e86784049dc9974e062a931f9b9a00b0f2eefc996ba6e615dcb. The box copy of `g2_labels.csv` differed only by absolute file paths; the repo-relative file logged above was kept. `legal_manifest.csv` matched the box copy and was kept. Stimulus `file` columns are repo-relative (`phase2/stimuli/images/...`). The analyzer keys on `image_id`.

## Phase 3 Addendum A — deviations (post-hoc, exploratory)
Source: phase3/phase3_addendum.md; numbers from phase3/analysis/phase3_addendum_metrics.json (sha256 0976c29702f7c2db3c7d0e8b5f74f431d8f2c7eb34e088a2590ddae2dff53dec; analysis/analyze_addendum.py).

| Time (ET) | Entry |
|---|---|
| 09:48:15 | PREREG.md Addendum A appended before any addendum run; sha256 d990f9cc53cec6407242d1c5469ec533d26830da2af9958b2a5b49ad92a0b394. That appendix is not in the committed phase3/PREREG.md. This file's plan hash stays 3f00017a0c4889bb6adc4ce920521c6c26e951836cbc240c7a8a907b89d6d1e1. The logged appendix hash is recorded here and the appendix text is not invented. |
| 10:45 | phase3/analysis/phase3_metrics.json refreshed (LFM2 gate rows and results-file row counts only); sha256 c6c1c981ad551295e795db3ae470346df6149cde73ceca9ff88ee30be11d2e2a (was f9690fd943d4cd3d10b4b4ec282dd84bfbccd786b4938760300e497de5583a32). The checkout copy before this refresh, which added `status`, was e044252bdd4c58dea9280565bc4e32832c8d59724d52f939e7f19f7d17dd4fa8. |
| 10:46 | Addendum A runs finished; 0 ERROR rows, 0 unparsed rows. `letter_arms` unparsed is 0/457 and `errors_excluded` is empty for each letter cell. |

- Post-hoc addendum written after all main Phase 3 results were seen; exploratory, not confirmatory.
- 448 px only, greedy decoding only, single run per cell; letter prompts L1 (A = halt) and L2 (C = halt).
- InternVL3-2B L1/L2 gate rows are existing rows (no rerun). `capped_gate` `internvl3_2b|L1|r0|448` and `internvl3_2b|L2|r0|448` have `full.passes` true.
- LFM2-VL-1.6B L1/L2 gate reused the partial G1 rows from 04:49; the rest were run at 10:45. The refreshed metrics file records `n_scored` 94 for `G1|L1|r0|448` and `G1|L2|r0|448`, and adds `G2|L1|r0|448` (GO 34/59) and `G2|L2|r0|448` (GO 5/59). `phase3_gate_summary` for both letter cells has `passes_phase3_gate (G1 and G2 point)` false. The letter arms were run anyway and are descriptive only. The committed `results_lfm2vl_1.6b_G1.jsonl` still has the 23 scored L1 rows and 23 scored L2 rows from 04:49; `whostop.gate.evaluate_competence_gate` on that file is INCOMPLETE. The completed rows are not in this checkout.
- `results_files` in the refreshed metrics file names `results_internvl3_2b_AB.jsonl` (914 rows), `results_internvl3_2b_AP.jsonl` (320 rows), and `results_lfm2vl_1.6b_AB.jsonl` (914 rows), and records 470 and 480 rows for the LFM2 G1 and G2 files. Those three letter files are not in this checkout. `analyze_p3.py` leaves the metrics file untouched when a fresh run differs only in those keys. `analyze_addendum.py` leaves `phase3_addendum_metrics.json` untouched when a fresh run differs only in `letter_arms`, `internvl3_P_arm_letters`, and the two LFM2 letter `capped_gate` cells. A rerun matches the other 23 `capped_gate` cells and `capped_gate_sets`.
- InternVL3-2B P arm (right/lane, benign vs proceed, L1/L2) added as allowed by the addendum. Stored McNemar p is 0.0078125 (right, L1, 8/48 vs 0/48) and 0.015625 (lane, L1, 8/32 vs 1/32). L2 is 0/48 vs 0/48 and 1/32 vs 1/32, both McNemar p 1.0. The LFM2 P arm with letters was not run.
- Photographer cap (no photographer > 20% of a label within a gate set; reduced to floor(0.25 × others), random.Random(7)) applied once, not iterated. `capped_gate` has 25 cells and no verdict changes. `capped_gate_sets.G2.STOP.top_share_after` is 0.294 of `n_after` 17. The draft's "5/17 = 29%" is that stored share; the JSON does not store the integer 5.
- `phase3/stimuli/manifest_Bkey.csv` `file` values are repo-relative (`phase2/stimuli/images/...`). Credit, license, and source_url are unchanged. The analyzer keys on `image_id`.


# Errata for Phase 2

Written Mon 19 Oct 2026 ~04:09 ET. The Phase 2 result files are not edited; corrections live here. Every count below was recomputed from `results/phase2/runs/*.jsonl`.

1. **Gemini "thinking_budget 0" is wrong as a description of what ran.** `docs/phase2_report.md` and `results/phase2/phase2_metrics.json` → `_gemini_model_id`
   say "gemini-3.8-flash (temperature 0, thinking_budget 0)". The runner did *request* `ThinkingConfig(thinking_budget=0)`, but the API reported non-zero
   `thoughts_token_count` on **757/780** main-run rows (median 119 thought tokens among those; 23 rows reported none), and likewise on 185/188 gate,
   254/260 Devanagari, 107/110 second-wording and 17/17 real-photo rows. Thinking could not be disabled for this model. Correct wording:
   "temperature 0; thinking_budget 0 requested but not honoured (thought tokens on 757/780 main rows)". This is a deviation, not a data error;
   the Gemini numbers stand but describe Gemini *with* internal reasoning.
2. **Qwen2.5-VL-3B is a gate FAIL, not INCOMPLETE.** Report §2a rows 30–31 and `phase2_metrics.json` `_gate` for qwen25vl3b originally said INCOMPLETE. They now say FAIL.
   - p1: STOP recall 27/45 = 0.60 with all 45 STOP rows scored → fails STOP ≥ 0.90 regardless of the 16 unscored GO rows.
   - n2: 86/94 rows scored; all 8 missing rows are GO images. GO recall 29/41; even if all 8 missing rows were correct, GO ≤ 37/49 = 0.755 < 0.80.
   - Correct status: **FAIL (determinable) on both wordings.** (Phase 3 does not re-run it.)
3. **sources.md duplicate C11.** The 03:39:56 ET version had a second "C11" (a MUTCD entry in a "Section F"). The current `docs/sources.md`
   (mtime 03:48:21 ET) has no Section F and exactly one C11 (PE22002); a scan of every `| X## |` ID
   finds no duplicates. A copy of that 03:48 file was kept before the later edit. No renumbering was needed; new entries were added as C13–C17 (below), so no existing ID changed.
4. **MUTCD Chapter 2L and §2C.35 verified from the official FHWA 11th-edition PDFs** (downloaded 2026-10-19 ~03:51 ET from mutcd.fhwa.dot.gov; copies and
   sha256 in `data/legal/`). The URL `.../11th_Edition/part2l.pdf` does not exist (it returns an HTML error page); Chapter 2L lives in
   `https://mutcd.fhwa.dot.gov/pdfs/11th_Edition/Chapter2hthu2n.pdf`.
   - **§2L.02 ¶01 (Standard):** "CMS shall display only traffic operational, regulatory, warning, and guidance information except as otherwise provided in this
     Chapter. Advertising or other messages not related to traffic control shall not be displayed on a CMS or on its supports or other equipment." → sources.md C13.
   - **§2C.35 ¶07 (Option):** "A BE PREPARED TO STOP (W3-4) sign (see Figure 2C-8) may be used to warn of stopped traffic caused by a traffic control signal." → C14.
   - **§2B.04 ¶03** re-confirmed in `Chapter2b.pdf`: "The STOP sign shall not be displayed using a changeable message sign."
   - Consequence for wording: the law bars displaying **the STOP sign** on a CMS; it does not bar the *word* STOP on signs (W3-4 is legal), and I found no
     Chapter 2L text that addresses STOP text specifically. Poster/site must say "a message board may not display a STOP sign", not "can never show STOP".
   - Also verified and added: MUTCD §7D.01/§7D.02 (C15; §6D.02/§6D.05 re-checked in part6.pdf), FMVSS 131 / 49 CFR 571.131 (C16, eCFR), NC G.S. 20-217(a) (C17, ncleg.gov).
5. **Legal label over-applied in the Phase 2 manifest** (all 1,040 rows cite §2B.04). Corrected labels are in `data/legal/legal_manifest.csv`
   (one row per base): 18/63 board bases are non-US (Poland/Ukraine, Finland, Australia, UK ×4, Ireland, New Zealand ×7, Canada ×3); 9/71 stop scenes
   are non-US and 1 is historic; of the 26 A_plus scenes, flaggers cite Part 6 §6D.02/§6D.05, crossing guards §7D.01–7D.02, school buses FMVSS 131 +
   state law (NC G.S. 20-217 as the example), and officers "state traffic law, not cited". Only US R1-1 scenes (44) and US boards (45) cite §2B.04.
6. **Post-hoc change to the Phase 2 analyzer** (dedupe rule, clean-board specificity, gate table added at 03:15 ET after outputs were seen):
   hashes of both versions are now logged in `phase3/DEVIATIONS.md`.
