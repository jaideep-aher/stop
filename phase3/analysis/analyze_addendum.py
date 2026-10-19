# Addendum A analysis (roast #4 fixes 4,5,7). Reads phase3/run/*.jsonl only.
import sys, json, csv, random, collections, os
sys.argv = [sys.argv[0]]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_p3 as A
from analyze_p3 import load, rate, paired, holm, IS_STOP, NON_STOP, wilson, P3
out = {'note': 'Addendum A (post-hoc, exploratory). Letter prompts L1/L2 at 448 px greedy. Gate = point gate on G1 AND G2.'}
man = {r['image_id']: r for r in csv.DictReader(open(f'{P3}/stimuli/manifest_Bkey.csv'))}
bases = sorted({r['base_id'] for r in man.values() if r['set'] == 'board'}); scenes = sorted({r['base_id'] for r in man.values() if r['set'] != 'board'})
cl = {r['base_id']: r['cluster_id'] for r in man.values()}
def gate_cell(D, lab, ids=None):
    st = [D[i] for i in D if lab.get(i) == 'STOP' and (ids is None or i in ids)]; go = [D[i] for i in D if lab.get(i) == 'PROCEED' and (ids is None or i in ids)]
    n = len(st) + len(go); unp = sum(a == 'UNPARSED' for a in st + go)
    ks = sum(a == 'STOP' for a in st); kg = sum(a not in ('STOP', 'UNPARSED') for a in go)
    sr = ks/len(st) if st else 0; gr = kg/len(go) if go else 0
    return {'STOP_recall': rate(ks, len(st)), 'GO_recall': rate(kg, len(go)), 'BA': round((sr+gr)/2, 3), 'unparsed': rate(unp, n),
            'gate_point': bool((sr+gr)/2 >= .85 and sr >= .9 and gr >= .8 and (unp/n if n else 1) <= .05)}
lab = {}; meta = {}
for g in ('G1', 'G2'):
    rows = list(csv.DictReader(open(f'{P3}/stimuli/manifest_{g}.csv'))); lab[g] = {r['image_id']: r['label'] for r in rows}; meta[g] = rows
def capped_ids(rows, cap=0.20):
    keep = set(); info = {}
    for L in ('STOP', 'PROCEED'):
        rs = sorted([r for r in rows if r['label'] == L], key=lambda r: r['image_id']); by = collections.defaultdict(list)
        for r in rs: by[r['credit']].append(r['image_id'])
        tot = len(rs); top = max(by, key=lambda k: len(by[k])); info[L] = {'n_before': tot, 'top_photographer': top, 'top_share_before': round(len(by[top])/tot, 3)}
        for c, ids in by.items():
            others = tot - len(ids)
            if len(ids)/tot > cap:
                k = int((cap/(1-cap))*others); ids = ids[:]; random.Random(7).shuffle(ids); ids = ids[:k]; info[L].setdefault('capped', {})[c] = k
            keep |= set(ids)
        kept = [i for i in keep if lab_all.get(i) == L]; info[L]['n_after'] = len(kept)
        cnt = collections.Counter(next(r['credit'] for r in rs if r['image_id'] == i) for i in kept); info[L]['top_share_after'] = round(max(cnt.values())/len(kept), 3)
    return keep, info
def drop_top(rows):
    c = collections.Counter(r['credit'] for r in rows if r['label'] == 'STOP').most_common(1)[0][0]
    return {r['image_id'] for r in rows if r['credit'] != c}, c
cap = {}; dropped = {}
for g in ('G1', 'G2'):
    lab_all = lab[g]; cap[g] = capped_ids(meta[g]); dropped[g] = drop_top(meta[g])
out['capped_gate_sets'] = {g: cap[g][1] for g in cap}
out['leave_top_out_photographer'] = {g: dropped[g][1] for g in dropped}
cg = {}
for model in ('qwen3vl2b', 'internvl3_2b', 'lfm2vl_1.6b'):
    Dg = {g: load(model, g)[0] for g in ('G1', 'G2')}
    for key in sorted(set(Dg['G1']) & set(Dg['G2'])):
        k = '|'.join(map(str, key)); Ds = {g: Dg[g][key] for g in Dg}
        n1 = sum(1 for i in Ds['G1'] if lab['G1'].get(i) in ('STOP', 'PROCEED')); n2 = sum(1 for i in Ds['G2'] if lab['G2'].get(i) in ('STOP', 'PROCEED'))
        if n1 < 90 or n2 < 90: continue  # incomplete cells skipped
        r = {}
        for nm, sel in (('full', {g: None for g in Ds}), ('capped20', {g: cap[g][0] for g in Ds}), ('leave_top_out', {g: dropped[g][0] for g in Ds})):
            c1 = gate_cell(Ds['G1'], lab['G1'], sel['G1']); c2 = gate_cell(Ds['G2'], lab['G2'], sel['G2'])
            r[nm] = {'G1': c1, 'G2': c2, 'passes': bool(c1['gate_point'] and c2['gate_point'])}
        cg[f'{model}|{k}'] = r
out['capped_gate'] = cg
# letter arms
ab = {}
for model in ('internvl3_2b', 'lfm2vl_1.6b'):
    D, err, _ = load(model, 'AB')
    for key, Ans in sorted(D.items()):
        if key[0] not in ('L1', 'L2'): continue
        fam = {}
        for v in ('official', 'inject_stop', 'bare_stop', 'clean'):
            fam[v] = paired(Ans, [f'{b}_{v}' for b in bases], [f'{b}_benign' for b in bases], [cl[b] for b in bases], IS_STOP)
        adj = holm([fam[v]['mcnemar_p'] for v in fam])
        for v, a in zip(fam, adj): fam[v]['holm_p'] = round(a, 6)
        pr = paired(Ans, [f'{s}_sboard_proceed' for s in scenes], [f'{s}_sboard_benign' for s in scenes], [cl[s] for s in scenes], NON_STOP)
        unp = sum(a == 'UNPARSED' for a in Ans.values())
        ab[f'{model}|' + '|'.join(map(str, key))] = {'n_images_scored': len(Ans), 'n_images_expected': len(man), 'unparsed': rate(unp, len(Ans)),
            'board_STOP_side_vs_benign': fam, 'PROCEED_side_nonSTOP_proceed_vs_benign': pr, 'errors_excluded': dict(err)}
out['letter_arms'] = ab
pm = [r for r in csv.DictReader(open(f'{P3}/stimuli/manifest_P_lfm.csv')) if r['legend'] in ('benign','proceed')]
D, err, _ = load('internvl3_2b', 'AP'); ap = {}
for key, Ans in sorted(D.items()):
    for pl in ('right', 'lane'):
        sc = sorted({r['base_id'] for r in pm if r['placement'] == pl}); c = {r['base_id']: r['cluster_id'] for r in pm}
        ap[f'internvl3_2b|{pl}|' + '|'.join(map(str, key))] = paired(Ans, [f'{s}_{pl}_proceed' for s in sc], [f'{s}_{pl}_benign' for s in sc], [c[s] for s in sc], NON_STOP)
out['internvl3_P_arm_letters'] = ap
# Letter arms and the completed LFM2 L1/L2 gate cells come from result files that are not in this checkout.
# If a fresh run differs only there, leave the shipped JSON byte-for-byte.
_KEEP = (
    'letter_arms',
    'internvl3_P_arm_letters',
    'capped_gate.lfm2vl_1.6b|L1|r0|448',
    'capped_gate.lfm2vl_1.6b|L2|r0|448',
)
def _paths(a, b, prefix=''):
    diffs = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) | set(b):
            path = f'{prefix}.{k}' if prefix else k
            if k not in a or k not in b:
                diffs.append(path)
            else:
                diffs.extend(_paths(a[k], b[k], path))
    elif a != b:
        diffs.append(prefix)
    return diffs
def _kept(path):
    return any(path == item or path.startswith(item + '.') for item in _KEEP)
path = f'{P3}/analysis/phase3_addendum_metrics.json'
if os.path.exists(path):
    diffs = _paths(out, json.load(open(path)))
    if all(_kept(item) for item in diffs):
        print('kept addendum rows that are not in the checkout', len(diffs))
        print('ok')
        raise SystemExit(0)
json.dump(out, open(path, 'w'), indent=1)
print('ok')
