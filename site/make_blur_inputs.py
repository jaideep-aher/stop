#!/usr/bin/env python3
"""Write blur input lists (id,src,group,is_unedited) from the manifests.

Usage: make_blur_inputs.py <outdir> [--root REPO_ROOT]
The default root is this repository (the parent of site/)."""
import csv, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.abspath(os.path.join(HERE, ".."))
if "--root" in sys.argv:
    R = os.path.abspath(sys.argv[sys.argv.index("--root") + 1])
out = sys.argv[1]
def w(name, rows):
    with open(f'{out}/in_{name}.csv', 'w', newline='') as f: csv.writer(f, lineterminator="\n").writerows(rows)
    print(name, len(rows))
P2 = f'{R}/phase2/stimuli'
man = list(csv.DictReader(open(f'{P2}/manifest.csv')))
w('p2', [[r['image_id'], f"{P2}/{r['file']}", r['base_id'], int(r['variant'] in ('clean', 'sclean'))]
         for r in man if (r['set'] == 'board' and r['arm'] == 'en') or r['set'] == 'stopscene'])
w('real', [[r['image_id'], f"{P2}/{r['file']}"] for r in csv.DictReader(open(f'{P2}/real_manifest.csv'))])
w('pilot', [[r['image_id'], f"{R}/pilot/pilot_v2/{r['file']}"] for r in csv.DictReader(open(f'{R}/pilot/pilot_v2/manifest.csv'))
            if r['blur'].startswith('not_needed')])
