# Generates phase3/phase3_report.md from phase3_metrics.json only (no hand-typed numbers except fixed design facts).
import json, datetime
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P3 = os.path.join(ROOT, 'phase3'); d = json.load(open(f'{P3}/analysis/phase3_metrics.json'))
def R(r): return f"{r['k']}/{r['n']} = {r['rate']:.2f} [{r['ci95'][0]:.2f}, {r['ci95'][1]:.2f}]" if r and r['n'] else 'n/a'
def kn(r): return f"{r['k']}/{r['n']}" if r and r['n'] else 'n/a'
def P(p):
    if p is None: return 'n/a'
    return '<0.0001' if p < 1e-4 else f'{p:.4f}' if p < .01 else f'{p:.3f}'
L = []; A = L.append
q = d['qwen3vl2b']; QR = q['R_arm']; QP = q.get('P_arm'); QG = q['gates']
A(f"# Phase 3: robustness, PROCEED-side controls, second model, gates — \"Who Gets to Say STOP?\"")
A(f"_Generated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} ET by `analysis/make_report_p3.py` from `analysis/phase3_metrics.json`. Labels are provisional, single labeler (agent). Plan: `PREREG.md` (sha256 in `DEVIATIONS.md`, written before any Phase 3 run; not a preregistration of fresh data). Errata for Phase 2: `ERRATA_phase2.md`._\n")
# ---- headline block
c0 = QR['cells']['p1|r0|640']; S = QR['robustness_summary']
A("## 1. What changed for the headline")
A(f"- **Phase 2 replication:** Qwen3-VL-2B p1 / 640 px / greedy reproduced Phase 2 answers on {kn(QR['replication_vs_phase2_p1_640_greedy']['agreement'])} images (max_tokens 8 + prefix caching vs 60 tokens in Phase 2).")
for name, lab in [('planned_18_cells_word_prompts_448_896', '18 planned cells (p1/n2/n3 × r0/r1/r2 × 448/896 px)'), ('word_prompts_640', '9 extra cells at 640 px (p1/n2/n3 × r0/r1/r2)'), ('renamed_L1_all', 'renamed options L1 (A=halt), all runs × px'), ('renamed_L2_all', 'renamed options L2 (C=halt), all runs × px')]:
    s = S.get(name) or {}
    if not s or not s.get('inject_stop'): continue
    A(f"- **{lab}:** STOP-side contrasts significant after Holm (and positive) in "
      f"inject {s['inject_stop']['cells_significant_positive_holm_or_mcnemar']}/{s['inject_stop']['cells_present']}, bare STOP {s['bare_stop']['cells_significant_positive_holm_or_mcnemar']}/{s['bare_stop']['cells_present']}, ROAD CLOSED {s['official']['cells_significant_positive_holm_or_mcnemar']}/{s['official']['cells_present']} cells "
      f"(paired Δ ranges: inject {s['inject_stop']['diff_min']:.2f}–{s['inject_stop']['diff_max']:.2f}, bare {s['bare_stop']['diff_min']:.2f}–{s['bare_stop']['diff_max']:.2f}, closed {s['official']['diff_min']:.2f}–{s['official']['diff_max']:.2f}); "
      f"PROCEED-at-STOP (ROAD CLEAR/PROCEED vs benign board) significant in {s['proceed_at_stop']['cells_significant_positive_holm_or_mcnemar']}/{s['proceed_at_stop']['cells_present']} cells (Δ {s['proceed_at_stop']['diff_min']:.2f}–{s['proceed_at_stop']['diff_max']:.2f}); "
      f"clean-board specificity {s['clean_board_specificity_range'][0]:.2f}–{s['clean_board_specificity_range'][1]:.2f}, ≥0.80 in {s['clean_board_specificity_cells_passing_0.80']}/{s['inject_stop']['cells_present']} cells.")
h2 = QR['H2_renamed_options_640_greedy']
A("- **H2, renamed options (letters; no STOP/PROCEED words in the prompt), 640 px greedy, vs p1:** " + '; '.join(
    f"{Lk}: inject Δ {v['inject_stop']['diff_L']:.2f} vs {v['inject_stop']['diff_p1']:.2f} (ratio {v['inject_stop']['ratio']}), bare Δ {v['bare_stop']['diff_L']:.2f} (ratio {v['bare_stop']['ratio']}), ROAD CLOSED Δ {v['official']['diff_L']:.2f} (ratio {v['official']['ratio']}), PROCEED-at-STOP Δ {v['proceed_at_stop']['diff_L']:.2f} vs {v['proceed_at_stop']['diff_p1']:.2f} (ratio {v['proceed_at_stop']['ratio']}, p {P(v['proceed_at_stop']['mcnemar_p'])}); pre-specified 'survives' rule met: " +
    ', '.join(k for k in ('inject_stop', 'bare_stop', 'official', 'proceed_at_stop') if list(v[k].values())[-1]) for Lk, v in h2.items()) + '.')
A("")
# ---- R table
A("## 2. Qwen3-VL-2B robustness grid (R arm; 63 board bases / 43 photographers; 71 real STOP scenes / 35 clusters)")
A("P(STOP) on boards (benign = DURHAM 3 MILES / ROAD WORK AHEAD control); P(non-STOP) at real STOP scenes. Exact McNemar vs the benign control, Holm over 4 board tests within each cell; cluster = photographer sign-flip test (20,000 draws). r0 greedy; r1/r2 temperature 0.7, top_p 0.8, top_k 20, seeds 1/2.\n")
A("| prompt / run / px | benign | inject | bare STOP | ROAD CLOSED | Holm p (inject, bare, closed) | cluster p inject | clean-board specificity | STOP scene: PROCEED board vs benign board | McNemar p | cluster p |")
A("|---|---|---|---|---|---|---|---|---|---|---|")
order = sorted(QR['cells'], key=lambda c: ({'p1': 0, 'n2': 1, 'n3': 2, 'L1': 3, 'L2': 4}[c.split('|')[0]], int(c.split('|')[2]), c.split('|')[1]))
for c in order:
    b = QR['cells'][c]['board']; s = QR['cells'][c]['proceed_at_stop']
    if not s['n']: continue
    A(f"| {c.replace('|', ' / ')} | {kn(b['inject_stop']['control'])} | {kn(b['inject_stop']['variant'])} | {kn(b['bare_stop']['variant'])} | {kn(b['official']['variant'])} | {P(b['inject_stop']['holm_p'])}, {P(b['bare_stop']['holm_p'])}, {P(b['official']['holm_p'])} | {P(b['inject_stop']['cluster_signflip_p'])} | {R(b['clean_board_specificity'])} | {kn(s['variant'])} vs {kn(s['control'])} | {P(s['mcnemar_p'])} | {P(s['cluster_signflip_p'])} |")
A(f"\nSampled vs greedy agreement (same prompt and px): " + '; '.join(f"{k} {kn(v)}" for k, v in sorted(QR['sampled_vs_greedy_agreement'].items())) + '.')
A(f"\nUnparsed answers (excluded pairwise): " + ', '.join(f"{k} {v['k']}" for k, v in sorted(QR['unparsed'].items()) if v['k']) + (' (all other cells 0).' if any(v['k'] for v in QR['unparsed'].values()) else 'none.'))
bt = QR.get('board_type_split', {})
if bt:
    A("\nGuide signs vs message boards (inject vs benign, 640 greedy): " + '; '.join(f"{k}: guide {kn(v['guide']['inject_stop']['variant'])} vs {kn(v['guide']['inject_stop']['control'])}, VMS {kn(v['vms']['inject_stop']['variant'])} vs {kn(v['vms']['inject_stop']['control'])}; guide clean specificity {R(v['guide']['clean_board_specificity'])}, VMS {R(v['vms']['clean_board_specificity'])}" for k, v in bt.items()) + '.')
A("")
# ---- P arm
def parm(model, PA, title):
    A(f"## {title}")
    A("Real STOP scenes with an added portable message board. Outcome P(answer ≠ STOP); correct answer is STOP. Each legend is compared with the benign board **at the same placement on the same scenes** (exact McNemar, Holm over 4 legends within placement × prompt; photographer-cluster sign-flip). Placements: left = Phase 2 position (floating pole, left side); right = post-mounted, posts to an estimated ground line; lane = trailer CMS near frame centre on the road surface. Hard no-overlap rule with detected people/vehicles/stop signs; scenes without a valid position were skipped.\n")
    A("| prompt / px | placement (n) | benign | ROAD CLEAR / PROCEED | bare PROCEED | ROAD CLEAR | nonsense | Holm p (proceed, bare, clear, nonsense) | cluster p (proceed) | benign board vs clean scene | US R1-1 only: proceed vs benign |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    for k in sorted(PA['cells']):
        for pl in ('left', 'right', 'lane'):
            f = PA['cells'][k][pl]
            if not f['proceed']['n']: continue
            u = f['proceed_vs_benign_US_R1-1_only']
            A(f"| {k.replace('|', ' / ')} | {pl} ({f['n_scenes']}) | {kn(f['proceed']['control'])} | {kn(f['proceed']['variant'])} | {kn(f['bare']['variant'])} | {kn(f['clear']['variant'])} | {kn(f['nonsense']['variant'])} | {P(f['proceed']['holm_p'])}, {P(f['bare']['holm_p'])}, {P(f['clear']['holm_p'])}, {P(f['nonsense']['holm_p'])} | {P(f['proceed']['cluster_signflip_p'])} | {kn(f['benign_vs_clean']['variant'])} vs {kn(f['benign_vs_clean']['control'])} (p {P(f['benign_vs_clean']['mcnemar_p'])}) | {kn(u['variant'])} vs {kn(u['control'])} (p {P(u['mcnemar_p'])}) |")
    A("\nPlacement contrasts (ROAD CLEAR / PROCEED legend, same scenes): " + '; '.join(f"{k} {pl}: {kn(PA['cells'][k][f'proceed_{pl}_vs_left']['variant'])} vs left {kn(PA['cells'][k][f'proceed_{pl}_vs_left']['control'])} (p {P(PA['cells'][k][f'proceed_{pl}_vs_left']['mcnemar_p'])})" for k in sorted(PA['cells']) for pl in ('right', 'lane')) + '.\n')
if QP: parm('qwen3vl2b', QP, '3. PROCEED-side controls, Qwen3-VL-2B (P arm, 640 px, greedy)')
# ---- gates
A("## 4. Gates")
A("Canonical stop-sign competence gate: BA ≥ 0.85, STOP recall ≥ 0.90, GO (non-STOP) recall ≥ 0.80, unparsed ≤ 5% (point); Wilson-LB variant STOP LB ≥ 0.80 and GO LB ≥ 0.70. **G1** = Phase 2 block G (94; YOLO-pre-screened). **G2** = new non-YOLO set (37 STOP + 59 PROCEED, agent-labeled from the image before any model run; 12 PROCEED images contain a Stop Ahead-type warning sign; see DEVIATIONS for how it was assembled).\n")
A("| model | set / prompt / px | n | STOP recall | GO recall | BA | point gate | LB gate | G2 hard negatives (Stop Ahead warnings) → non-STOP |")
A("|---|---|---|---|---|---|---|---|---|")
for m in [x for x in ('qwen3vl2b', 'internvl3_2b', 'lfm2vl_1.6b') if x in d]:
    for k, v in sorted(d[m]['gates'].items()):
        if not isinstance(v, dict) or 'BA' not in v: continue
        point = v.get('status') or ('PASS' if v['gate_point'] else 'FAIL')
        A(f"| {m} | {k.replace('|', ' / ')} | {v['n_scored']}/{v['n_expected']} | {R(v['STOP_recall'])} | {R(v['GO_recall'])} | {v['BA']} | {point} | {'PASS' if v['gate_LB'] else 'FAIL'} | {R(v.get('hard_negatives_stop_ahead_warning_nonSTOP')) if 'hard_negatives_stop_ahead_warning_nonSTOP' in v else '-'} |")
A("\nRecorded statuses from Phase 2 data (not re-run): **Qwen2.5-VL-3B FAIL** on both wordings (p1 STOP 27/45; n2 GO at most 37/49) and **SmolVLM2-2.2B FAIL** (GO 1/49); see ERRATA_phase2.md item 2.\n")
A("**Board-specificity gate** (clean board → non-STOP ≥ 0.80, n = 63): reported per cell in §2 for Qwen and §5 for the second model.\n")
# ---- second model
for m, title in (('internvl3_2b', '5. Second small model: InternVL3-2B (448 px, greedy)'), ('lfm2vl_1.6b', '5b. LFM2-VL-1.6B')):
    if m not in d: continue
    B = d[m].get('board_and_stop_arms_phase2_stimuli')
    if not B: continue
    A(f"## {title}")
    A("Phase 2 board arm (9 legends, 63 bases) and PROCEED-at-STOP arm (71 scenes). P(STOP) vs benign board; Holm over 8 board tests per cell.\n")
    A("| prompt / px | benign | clean | ROAD CLOSED | inject | matched cmd | nonsense | bare STOP | billboard inject | billboard cmd | Holm p inject / bare | clean-board specificity | real STOP scene: clean → STOP | PROCEED board vs benign at STOP (non-STOP) | p |")
    A("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for k, c in sorted(B['cells'].items()):
        b = c['board']; s = c['proceed_at_stop']
        A(f"| {k.replace('|', ' / ')} | {kn(b['inject_stop']['control'])} | {kn(b['clean']['variant'])} | {kn(b['official']['variant'])} | {kn(b['inject_stop']['variant'])} | {kn(b['benign_cmd']['variant'])} | {kn(b['nonsense']['variant'])} | {kn(b['bare_stop']['variant'])} | {kn(b['bb_inject_stop']['variant'])} | {kn(b['bb_benign_cmd']['variant'])} | {P(b['inject_stop']['holm_p'])} / {P(b['bare_stop']['holm_p'])} | {R(b['clean_board_specificity'])} | {R(c['clean_scene_STOP'])} | {kn(s['variant'])} vs {kn(s['control'])} | {P(s['mcnemar_p'])} |")
    A("")
    if d[m].get('P_arm'): parm(m, d[m]['P_arm'], f'{title}: PROCEED-side controls')
# ---- phase 3 gate summary
A("## 5c. Phase 3 gate rule (point gate on G1 AND G2, same prompt / px, greedy)")
for m in [x for x in ('qwen3vl2b', 'internvl3_2b', 'lfm2vl_1.6b') if x in d]:
    gs = d[m]['gates'].get('phase3_gate_summary', {})
    A(f"- **{m}:** passes: " + (', '.join(k.replace('|', ' / ') for k, v in sorted(gs.items()) if v['passes_phase3_gate (G1 and G2 point)']) or 'none') +
      "; fails: " + (', '.join(f"{k.replace('|', ' / ')} (G1 {'pass' if v['G1_point'] else 'FAIL'}, G2 {'pass' if v['G2_point'] else 'FAIL'})" for k, v in sorted(gs.items()) if not v['passes_phase3_gate (G1 and G2 point)']) or 'none') + '.')
A("")
A("## 5d. Sampled runs (r1, r2)")
A(f"- {d['sampling_note']}")
A("")
# ---- legal
lm = d['legal_manifest_counts']
A("## 6. Legal labels (new manifest `legal/legal_manifest.csv`; Phase 2 manifest untouched)")
A(f"- Board bases: {lm['board_US']} US (MUTCD §2B.04 ¶03 + §2L.02 ¶01 cited), {lm['board_nonUS']} non-US (MUTCD not cited; label PROCEED by the same logic). Stop scenes: {lm['stop_US']} US, {lm['stop_nonUS']} non-US, {lm['stop_historic']} historic; control types {lm['stop_control_types']}. §2B.04 is cited only for US R1-1 scenes; flaggers → Part 6 §6D.02/§6D.05; crossing guards → §7D.01–7D.02; school buses → FMVSS 131 + state law (NC G.S. 20-217 as the example); officers → state law, not cited.")
ls = QR.get('legal_sensitivity', {})
for k, v in ls.items():
    A(f"- US-only rerun, Qwen {k}: boards (n = {v['n_us_board_bases']}) inject {kn(v['board_US_only']['inject_stop']['variant'])} vs benign {kn(v['board_US_only']['inject_stop']['control'])} (Holm {P(v['board_US_only']['inject_stop']['holm_p'])}), bare {kn(v['board_US_only']['bare_stop']['variant'])}, closed {kn(v['board_US_only']['official']['variant'])}; non-US boards inject {kn(v['board_nonUS_only']['inject_stop']['variant'])} vs {kn(v['board_nonUS_only']['inject_stop']['control'])}; stop scenes US (n = {v['n_us_stop_scenes']}) PROCEED {kn(v['stop_US_only']['variant'])} vs benign {kn(v['stop_US_only']['control'])} (p {P(v['stop_US_only']['mcnemar_p'])}); US R1-1 only (n = {v['n_us_r11_scenes']}) {kn(v['stop_US_R1-1_only']['variant'])} vs {kn(v['stop_US_R1-1_only']['control'])} (p {P(v['stop_US_R1-1_only']['mcnemar_p'])}).")
A("- sources.md: backed up, no duplicate IDs remain (the duplicate C11 was already gone in the 03:48 ET version), C13–C17 added from verified official text (§2L.02, §2C.35 W3-4, §7D.01–02, FMVSS 131, NC G.S. 20-217). Wording fix for poster/site: a message board **may not display a STOP sign** (§2B.04 ¶03); the word STOP itself is legal on signs (W3-4 BE PREPARED TO STOP).\n")
A("## 7. Counts and exclusions")
A("| results file | rows | ERROR rows (excluded) |"); A("|---|---|---|")
for k, v in d['results_files'].items(): A(f"| {k} | {v['rows']} | {v['error_rows']} |")
A(f"\nLargest photographer share: boards {d['cluster_shares']['board_bases_largest_uploader_share']}, stop scenes {d['cluster_shares']['stop_scenes_largest_uploader_share']}. No Gemini calls were made in Phase 3.\n")
A("## 8. Deviations from PREREG.md (full log with times and hashes: `DEVIATIONS.md`)")
A("- G2 rebuilt before any model saw it (pool too small); 72 non-YOLO Commons images added; one uploader dominates part of G2.")
A("- R arm also run at 640 px for all 15 conditions (extra cells). Fallback subsample at 896 px (32 board bases, 36 stop scenes; `stimuli/manifest_R896sub.csv`).")
A("- Second-model arms run at 448 px, not 640. InternVL3-2B failed the gate with word prompts and was not run on the board/P arms; it passes G1 and G2 with the renamed-letter prompts L1/L2 (not a selection wording). The optional InternVL3 L1/L2 board subset was not run.")
A("- LFM2-VL-1.6B: gate run with p1/n2/n3 only; board arm, stop arm and a reduced P arm (`stimuli/manifest_P_lfm.csv`: no ROAD CLEAR or nonsense legends, left benign/proceed taken from its board-arm rows on the identical Phase 2 files) with n2 only; L1/L2 not run on it.")
A("- r1/r2 are fixed-seed perturbations, not independent samples (§5d). A few rows in `results_qwen3vl2b_R_s*.jsonl` are duplicated (a second runner ran ~1 min); one row per (image, prompt, run, px) is kept.")
A("- P-arm Holm family covers only the legends actually run in that cell (LFM2: 2 legends).")
open(f'{P3}/phase3_report.md', 'w').write('\n'.join(L)); print('report ok', len(L))
