import json, re, sys, os, requests, concurrent.futures as cf, collections
os.chdir('/workspace/rai_pivot/pilot/v2work'); sys.argv = ['x', 'illegit']
exec(open('collect.py').read().split("pool=sys.argv[1]")[0])
os.chdir('/workspace/rai_pivot/phase2')
old = {x['title'] for x in json.load(open('/workspace/rai_pivot/pilot/v2work/all_cands.json'))}
titles = []
for c, d in [('Portable changeable message signs', 1), ('Variable message signs in the United States', 1), ('Overhead guide signs in the United States', 1), ('Interstate exit signs', 1)]:
    try: titles += catfiles(c, d, limit=120)
    except Exception as e: print('cat fail', c, e)
for s in ['interstate exit sign highway view', 'guide sign highway exit miles', 'overhead sign gantry interstate', 'variable message sign highway', 'portable message sign road work', 'changeable message sign interstate', 'distance sign highway miles', 'freeway exit sign photo', 'message board trailer road', 'dynamic message sign highway', 'green highway sign exit', 'US route guide sign']:
    titles += search(s, 50)
titles = [t for t in dict.fromkeys(titles) if re.search(r'\.(jpe?g|png)$', t, re.I) and t not in old]
print('titles', len(titles))
FREE = re.compile(r'^(CC BY(-SA)? ?[0-9.]*|CC0|Public domain|PD.*|CC BY-SA [0-9.]+ .*|CC BY [0-9.]+ .*)$', re.I)
out = []
for i in range(0, len(titles), 40):
    r = q(action='query', titles='|'.join(titles[i:i+40]), prop='imageinfo', iiprop='url|extmetadata|size|mime', iiurlwidth=1280)
    for p in r.get('query', {}).get('pages', {}).values():
        if 'imageinfo' not in p: continue
        ii = p['imageinfo'][0]; m = ii.get('extmetadata', {}); lic = m.get('LicenseShortName', {}).get('value', '')
        if not FREE.match(lic.strip()) or ii.get('width', 0) < 800 or ii['width'] < ii['height']: continue
        out.append(dict(title=p['title'], thumb=ii.get('thumburl'), page=ii['descriptionurl'], license=lic,
                        artist=re.sub('<[^>]+>', '', m.get('Artist', {}).get('value', ''))[:150].strip(), w=ii['width'], h=ii['height']))
EXCL = ['formulanone', 'Tennyson', 'Famartin']
cnt = collections.Counter(); keep = []
for x in out:
    a = x['artist'][:25]
    if any(e in a for e in EXCL) or cnt[a] >= 3: continue
    cnt[a] += 1; keep.append(x)
for k, x in enumerate(keep): x['id'] = f'nb_{k:03d}'
UA = {'User-Agent': 'rai-pivot-research/0.1 (Duke AIPI student project; contact jaideep.aher@duke.edu)'}
def dl(x):
    p = f"thumbs_board/{x['id']}.jpg"
    if os.path.exists(p): return 1
    try:
        r = requests.get(x['thumb'], headers=UA, timeout=30); r.raise_for_status(); open(p, 'wb').write(r.content); return 1
    except Exception: return 0
with cf.ThreadPoolExecutor(4) as ex: print('dl', sum(ex.map(dl, keep)))
json.dump(keep, open('cand_newboards.json', 'w'), indent=0); print('kept', len(keep), 'artists', len(cnt))
from PIL import Image,ImageDraw,ImageFont
ids=[x['id'] for x in keep if os.path.exists(f"thumbs_board/{x['id']}.jpg")]
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',15); CW,CH=200,150; cols,rows=8,6; n=cols*rows
for s in range(0,len(ids),n):
    im=Image.new('RGB',(CW*cols,(CH+20)*rows),'white');d=ImageDraw.Draw(im)
    for k,i in enumerate(ids[s:s+n]):
        try: t=Image.open(f'thumbs_board/{i}.jpg').convert('RGB')
        except Exception: continue
        t.thumbnail((CW-4,CH));x=(k%cols)*CW;y=(k//cols)*(CH+20);im.paste(t,(x,y+18));d.text((x+2,y),i[3:],fill='red',font=f)
    im.save(f'sheets/nb_{s//n:02d}.jpg',quality=85)
