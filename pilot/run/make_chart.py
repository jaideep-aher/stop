import json, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, numpy as np
d = json.load(open('/workspace/rai_pivot/pilot/run/pilot_metrics.json'))
models = [('yolo|rule_conf0.35', 'YOLO11n rule\n(gate YOLO-screened)'), ('smolvlm|p1', 'SmolVLM-500M\np1'), ('qwen3vl2b|p1', 'Qwen3-VL-2B\np1'), ('gemini|p1', 'Gemini 3.8 Flash\np1'), ('gemini|p2', 'Gemini 3.8 Flash\np2 (defense prompt)')]
mets = [('Gate STOP recall', lambda o: o['gate']['stop_recall']), ('Gate GO recall', lambda o: o['gate']['proceed_recall']),
        ('Missed legit authority\n(PROCEED on A+)', lambda o: o['study1']['missed_legit_any(PROCEED on A_plus)']),
        ('"False obey"\n(STOP on A−, confounded)', lambda o: o['study1']['false_obey(STOP on A_minus)']),
        ('Tamper: STOP-engine\nflip vs clean', lambda o: o['study2']['inject_stop']['flip_vs_clean']),
        ('Tamper: instruction\necho', lambda o: o['study2']['inject_stop']['instruction_echo']),
        ('Removal: decision change\n(sign removed | orig STOP)', lambda o: o['study3_primary_no_residual']['decision_change_sign_removed|origSTOP']),
        ('Removal: decision change\n(control patch)', lambda o: o['study3_primary_no_residual']['decision_change_control|origSTOP'])]
fig, ax = plt.subplots(figsize=(15, 6.2)); w = 0.16; x = np.arange(len(mets))
cols = ['#888888', '#d98c3a', '#3a78d9', '#3aa65a', '#9ad1a8']
for k, (key, lab) in enumerate(models):
    o = d[key]; vals, lo, hi = [], [], []
    for _, f in mets:
        r = f(o); v = r['rate'] if r and r.get('n') else np.nan; vals.append(v)
        lo.append(v - r['ci95'][0] if r and r.get('ci95') else 0); hi.append(r['ci95'][1] - v if r and r.get('ci95') else 0)
    g = o.get('gate', {}).get('passed'); lab2 = lab + ('\n[gate PASS]' if g else '\n[gate FAIL]')
    ax.bar(x + (k - 2) * w, vals, w, yerr=[lo, hi], capsize=2, color=cols[k], label=lab2, edgecolor='black', linewidth=0.4)
ax.set_xticks(x); ax.set_xticklabels([m for m, _ in mets], fontsize=8.5); ax.set_ylim(0, 1.05); ax.set_ylabel('rate (Wilson 95% CI)')
ax.axhline(0.9, ls=':', c='k', lw=0.7)
ax.set_title('PILOT (underpowered; provisional single-labeler agent labels; Commons photos; box CPU, 640 px, strict parser). Not a result.', fontsize=10)
ax.legend(fontsize=7.5, ncol=5, loc='upper center', bbox_to_anchor=(0.5, -0.17), frameon=False)
n = d['qwen3vl2b|p1']
fig.text(0.01, 0.005, 'n: gate 45 STOP + 49 GO; A+ 44; A− 32 (mostly non-road / pedestrian-confounded); boards 18 bases × 5; removal 29 bases without residual cue. '
         'Dotted line = 0.90 STOP-recall gate. YOLO gate score is biased: gate images were YOLO-screened.', fontsize=7.5)
plt.tight_layout(rect=(0, 0.03, 1, 1)); plt.savefig('/workspace/rai_pivot/pilot/pilot_chart.png', dpi=150); print('saved')
