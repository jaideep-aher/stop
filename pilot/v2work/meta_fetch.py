import json, re, requests, time, csv
UA = {'User-Agent': 'rai-pivot-research/0.1 (Duke AIPI student project; contact jaideep.aher@duke.edu)'}
C = {x['id']: x for x in json.load(open('all_cands.json'))}
for x in json.load(open('cand_illegit3.json')): C[x['id']] = x
man = list(csv.DictReader(open('/workspace/rai_pivot/pilot/pilot_v2/manifest.csv')))
bases = sorted({r['base_id'] for r in man} | {'ill3_023','ill3_128','ill3_133','ill3_134','ill3_136','ill3_137','ill3_145','ill3_148','ill3_150'})
titles = {b: C[b]['title'] for b in bases}
out = {}
tl = list(titles.items())
for i in range(0, len(tl), 40):
    chunk = dict((t, b) for b, t in tl[i:i+40])
    params = dict(action='query', format='json', titles='|'.join(chunk), prop='categories|imageinfo', cllimit='max', iiprop='extmetadata', clshow='!hidden')
    while True:
        r = requests.get('https://commons.wikimedia.org/w/api.php', params=params, headers=UA, timeout=60).json()
        norm = {n['to']: n['from'] for n in r.get('query', {}).get('normalized', [])}
        for p in r.get('query', {}).get('pages', {}).values():
            t = norm.get(p['title'], p['title']); b = chunk.get(t) or chunk.get(p['title'])
            if not b: continue
            o = out.setdefault(b, {'cats': [], 'artist': '', 'date': '', 'desc': ''})
            o['cats'] += [c['title'][9:] for c in p.get('categories', [])]
            m = (p.get('imageinfo') or [{}])[0].get('extmetadata', {})
            if m:
                o['artist'] = re.sub('<[^>]+>', '', m.get('Artist', {}).get('value', '')).strip()[:150] or o['artist']
                o['date'] = re.sub('<[^>]+>', '', m.get('DateTimeOriginal', {}).get('value', '')).strip()[:40] or o['date']
                o['desc'] = re.sub('<[^>]+>', '', m.get('ImageDescription', {}).get('value', '')).strip()[:200] or o['desc']
                o['credit'] = re.sub('<[^>]+>', '', m.get('Credit', {}).get('value', '')).strip()[:150]
                o['license'] = m.get('LicenseShortName', {}).get('value', '')
        if 'continue' in r: params.update(r['continue'])
        else: break
    time.sleep(0.5)
json.dump(out, open('commons_meta.json', 'w'), indent=0); print(len(out), len(bases))
