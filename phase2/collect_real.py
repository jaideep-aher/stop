import json, re, sys, os, requests, concurrent.futures as cf
os.chdir('/workspace/rai_pivot/pilot/v2work'); sys.argv = ['x', 'illegit']
exec(open('collect.py').read().split("pool=sys.argv[1]")[0])
os.chdir('/workspace/rai_pivot/phase2')
titles = []
for c, d in [('Billboard hacking', 1), ('Subvertising', 1), ('Modified road signs', 1), ('Joke road signs', 0), ('Vandalised road signs', 0), ('Mock traffic signs in Amarillo, Texas', 0)]:
    titles += catfiles(c, d, limit=120)
for s in ['hacked road sign', 'hacked message sign', 'zombies ahead sign', 'altered highway sign', 'variable message sign hacked', 'prank road sign', 'altered road sign text', 'subvertising billboard']:
    titles += search(s, 30)
titles = list(dict.fromkeys(t for t in titles if re.search(r'\.(jpe?g|png)$', t, re.I)))
print('titles', len(titles))
FREE = re.compile(r'^(CC BY(-SA)? ?[0-9.]*|CC0|Public domain|PD.*|CC BY-SA [0-9.]+ .*|CC BY [0-9.]+ .*)$', re.I)
out = []
for i in range(0, len(titles), 40):
    r = q(action='query', titles='|'.join(titles[i:i+40]), prop='imageinfo', iiprop='url|extmetadata|size|mime', iiurlwidth=960)
    for p in r.get('query', {}).get('pages', {}).values():
        if 'imageinfo' not in p: continue
        ii = p['imageinfo'][0]; m = ii.get('extmetadata', {}); lic = m.get('LicenseShortName', {}).get('value', '')
        if not FREE.match(lic.strip()) or ii.get('width', 0) < 400: continue
        out.append(dict(title=p['title'], thumb=ii.get('thumburl'), page=ii['descriptionurl'], license=lic,
                        artist=re.sub('<[^>]+>', '', m.get('Artist', {}).get('value', ''))[:150].strip(), w=ii['width'], h=ii['height']))
for k, x in enumerate(out): x['id'] = f'real_{k:03d}'
UA = {'User-Agent': 'rai-pivot-research/0.1 (Duke AIPI student project; contact jaideep.aher@duke.edu)'}
def dl(x):
    p = f"thumbs_real/{x['id']}.jpg"
    if os.path.exists(p): return 1
    try:
        r = requests.get(x['thumb'], headers=UA, timeout=30); r.raise_for_status(); open(p, 'wb').write(r.content); return 1
    except Exception: return 0
with cf.ThreadPoolExecutor(4) as ex: print('dl', sum(ex.map(dl, out)))
json.dump(out, open('cand_real.json', 'w'), indent=0); print('kept', len(out))
