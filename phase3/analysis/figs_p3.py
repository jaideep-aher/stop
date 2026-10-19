# Phase 3 figures, from phase3_metrics.json only.
import json, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, numpy as np
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P3 = os.path.join(ROOT, 'phase3'); d = json.load(open(f'{P3}/analysis/phase3_metrics.json'))
q = d['qwen3vl2b']['R_arm']['cells']
cells = [c for c in sorted(q, key=lambda c: (c.split('|')[0], int(c.split('|')[2]), c.split('|')[1]))]
fig, axes = plt.subplots(1, 4, figsize=(17, 0.28*len(cells) + 1.5), sharey=True)
for ax, (title, get) in zip(axes, [('inject_stop vs benign board (P(STOP))', lambda c: q[c]['board']['inject_stop']), ('bare STOP vs benign board', lambda c: q[c]['board']['bare_stop']),
        ('ROAD CLOSED vs benign board', lambda c: q[c]['board']['official']), ('ROAD CLEAR/PROCEED vs benign at real STOP (P(non-STOP))', lambda c: q[c]['proceed_at_stop'])]):
    for i, c in enumerate(cells):
        r = get(c)
        if not r['n']: continue
        v, k = r['variant'], r['control']
        ax.plot([k['rate'], v['rate']], [i, i], color='0.7', lw=1)
        ax.errorbar(v['rate'], i, xerr=[[v['rate'] - v['ci95'][0]], [v['ci95'][1] - v['rate']]], fmt='o', color='C3', ms=4, lw=.8)
        ax.errorbar(k['rate'], i, xerr=[[k['rate'] - k['ci95'][0]], [k['ci95'][1] - k['rate']]], fmt='s', color='C0', ms=4, lw=.8)
    ax.set_title(title, fontsize=9); ax.set_xlim(-.02, 1.02); ax.grid(axis='x', alpha=.3)
axes[0].set_yticks(range(len(cells))); axes[0].set_yticklabels([c.replace('|', ' / ') for c in cells], fontsize=7)
axes[0].invert_yaxis(); fig.suptitle('Qwen3-VL-2B robustness grid (prompt / run / px). Red = edited legend, blue = benign control; Wilson 95% CI. Every row is from phase3_metrics.json.', fontsize=9)
fig.tight_layout(); fig.savefig(f'{P3}/fig1_qwen_robustness_grid.png', dpi=130)
# P arm
for model in [m for m in ('qwen3vl2b', 'internvl3_2b', 'lfm2vl_1.6b') if m in d and d[m].get('P_arm')]:
    P = d[model]['P_arm']['cells']; ks = sorted(P)
    fig, axes = plt.subplots(1, len(ks), figsize=(max(8.5, 4.2*len(ks)), 3.8), sharey=True); axes = np.atleast_1d(axes)
    for ax, k in zip(axes, ks):
        for j, pl in enumerate(('left', 'right', 'lane')):
            fam = P[k][pl]; ben = fam['proceed']['control']
            vals = [ben] + [fam[lg]['variant'] for lg in ('proceed', 'bare', 'clear', 'nonsense')]
            cols = ['C0', 'C3', 'C1', 'C2', '0.6']; keep = [i for i, v in enumerate(vals) if v['n']]   # legends not run (LFM2) are left blank
            xs = np.arange(5)[keep] + j*6; vv = [vals[i] for i in keep]
            ax.bar(xs, [v['rate'] for v in vv], color=[cols[i] for i in keep], yerr=[[v['rate'] - v['ci95'][0] for v in vv], [v['ci95'][1] - v['rate'] for v in vv]], capsize=2)
            ax.text(j*6 + 2, 1.02, f"{pl} (n={fam['n_scenes']})", ha='center', fontsize=8)
        ax.set_xticks([]); ax.set_ylim(0, 1.1); ax.set_title(k.replace('|', ' / '), fontsize=9)
    axes[0].set_ylabel('P(answer is not STOP) at a real STOP scene')
    fig.legend([plt.Rectangle((0, 0), 1, 1, color=c) for c in ['C0', 'C3', 'C1', 'C2', '0.6']], ['benign', 'ROAD CLEAR/PROCEED', 'PROCEED', 'ROAD CLEAR', 'nonsense'], loc='lower center', ncol=5, fontsize=8)
    fig.suptitle(f'{model}: PROCEED-side controls by board placement (Wilson 95% CI)', fontsize=10); fig.tight_layout(rect=(0, .08, 1, .95)); fig.savefig(f'{P3}/fig2_proceed_controls_{model}.png', dpi=130)
print('figs ok')
