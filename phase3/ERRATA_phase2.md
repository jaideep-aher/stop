# Errata for Phase 2 (phase2/ files are NOT edited; corrections live here)
Written Mon 19 Oct 2026 ~04:09 ET by the Phase 3 executor. Every count below was recomputed from phase2/run/*.jsonl.

1. **Gemini "thinking_budget 0" is wrong as a description of what ran.** `phase2/phase2_report.md` line 195 and `phase2_metrics.json` → `_gemini_model_id`
   say "gemini-3.8-flash (temperature 0, thinking_budget 0)". The runner did *request* `ThinkingConfig(thinking_budget=0)`, but the API reported non-zero
   `thoughts_token_count` on **757/780** main-run rows (median 119 thought tokens among those; 23 rows reported none), and likewise on 185/188 gate,
   254/260 Devanagari, 107/110 second-wording and 17/17 real-photo rows. Thinking could not be disabled for this model. Correct wording:
   "temperature 0; thinking_budget 0 requested but not honoured (thought tokens on 757/780 main rows)". This is a deviation, not a data error;
   the Gemini numbers stand but describe Gemini *with* internal reasoning.
2. **Qwen2.5-VL-3B is a gate FAIL, not INCOMPLETE.** Report §2a rows 30–31 and `phase2_metrics.json` `_gate` for qwen25vl3b originally said INCOMPLETE. They now say FAIL.
   - p1: STOP recall 27/45 = 0.60 with all 45 STOP rows scored → fails STOP ≥ 0.90 regardless of the 16 unscored GO rows.
   - n2: 86/94 rows scored; all 8 missing rows are GO images. GO recall 29/41; even if all 8 missing rows were correct, GO ≤ 37/49 = 0.755 < 0.80.
   - Correct status: **FAIL (determinable) on both wordings.** (Phase 3 does not re-run it.)
3. **sources.md duplicate C11.** Roast #3 found a second "C11" (a MUTCD entry in a "Section F") in the 03:39:56 ET version. The current `sources.md`
   (mtime 03:48:21 ET, changed by another agent before Phase 3 touched it) has no Section F and exactly one C11 (PE22002); a scan of every `| X## |` ID
   finds no duplicates. Backup made first: `phase3/legal/sources.md.bak_phase3_0350` and `/workspace/rai_pivot/sources.md.bak_phase3_0350` (byte-identical
   to the 03:48 file). No renumbering was needed; new entries were added as C13–C17 (below), so no existing ID changed.
4. **MUTCD Chapter 2L and §2C.35 verified from the official FHWA 11th-edition PDFs** (downloaded 2026-10-19 ~03:51 ET from mutcd.fhwa.dot.gov; copies and
   sha256 in `phase3/legal/`). The URL `.../11th_Edition/part2l.pdf` that roast #3 tried does not exist (it returns an HTML error page); Chapter 2L lives in
   `https://mutcd.fhwa.dot.gov/pdfs/11th_Edition/Chapter2hthu2n.pdf`.
   - **§2L.02 ¶01 (Standard):** "CMS shall display only traffic operational, regulatory, warning, and guidance information except as otherwise provided in this
     Chapter. Advertising or other messages not related to traffic control shall not be displayed on a CMS or on its supports or other equipment." → sources.md C13.
   - **§2C.35 ¶07 (Option):** "A BE PREPARED TO STOP (W3-4) sign (see Figure 2C-8) may be used to warn of stopped traffic caused by a traffic control signal." → C14.
   - **§2B.04 ¶03** re-confirmed in `Chapter2b.pdf`: "The STOP sign shall not be displayed using a changeable message sign."
   - Consequence for wording: the law bars displaying **the STOP sign** on a CMS; it does not bar the *word* STOP on signs (W3-4 is legal), and I found no
     Chapter 2L text that addresses STOP text specifically. Poster/site must say "a message board may not display a STOP sign", not "can never show STOP".
   - Also verified and added: MUTCD §7D.01/§7D.02 (C15; §6D.02/§6D.05 re-checked in part6.pdf), FMVSS 131 / 49 CFR 571.131 (C16, eCFR), NC G.S. 20-217(a) (C17, ncleg.gov).
5. **Legal label over-applied in the Phase 2 manifest** (all 1,040 rows cite §2B.04). Corrected labels are in `phase3/legal/legal_manifest.csv`
   (one row per base): 18/63 board bases are non-US (Poland/Ukraine, Finland, Australia, UK ×4, Ireland, New Zealand ×7, Canada ×3); 9/71 stop scenes
   are non-US and 1 is historic; of the 26 A_plus scenes, flaggers cite Part 6 §6D.02/§6D.05, crossing guards §7D.01–7D.02, school buses FMVSS 131 +
   state law (NC G.S. 20-217 as the example), and officers "state traffic law, not cited". Only US R1-1 scenes (44) and US boards (45) cite §2B.04.
6. **Post-hoc change to `phase2/analysis/analyze_p2.py`** (dedupe rule, clean-board specificity, gate table added at 03:15 ET after outputs were seen):
   hashes of both versions are now logged in `phase3/DEVIATIONS.md`.
