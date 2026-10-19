import csv, collections
P2='/workspace/rai_pivot/phase2'
rows=list(csv.DictReader(open(f'{P2}/stimuli/manifest.csv')))+list(csv.DictReader(open(f'{P2}/stimuli/real_manifest.csv')))
base={}
for r in rows: base.setdefault((r['set'],r['base_id']),r)
L=['# Phase 2 image licenses and attribution','',
'All base photos come from Wikimedia Commons under free licenses (CC0 / public domain / CC BY / CC BY-SA), and each license was read from the Commons API `extmetadata` at collection time.',
'**Edited stimuli are derivative works.** Board legends were changed digitally, a billboard was added, or a portable message board was added. Each derivative carries the license of its source photo: CC BY-SA sources stay CC BY-SA 4.0-compatible (ShareAlike), and every derivative keeps its attribution. The edits were made by the project (Duke AIPI Responsible AI, Jay Aher) for research. They are **not** depictions of real signs. The real-tampered set (`stimuli/real/`) is unedited.',
'The renderer that produced the edits is kept private (`private/`, not for publication).','',
'| set | base_id | license | credit | source |','|---|---|---|---|---|']
for (s,b),r in sorted(base.items()):
    L.append(f"| {s} | {b} | {r['license']} | {r['credit'].replace('|','/')[:80]} | {r['source_url']} |")
c=collections.Counter(r['license'] for r in base.values())
L+=['',f'License counts over {len(base)} base photos: '+', '.join(f'{k}: {v}' for k,v in c.most_common())]
open(f'{P2}/LICENSES.md','w').write('\n'.join(L)+'\n'); print(len(base),c.most_common(6))
