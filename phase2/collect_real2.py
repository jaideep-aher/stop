import json, re, sys, os, requests, concurrent.futures as cf
os.chdir('/workspace/rai_pivot/pilot/v2work'); sys.argv = ['x', 'illegit']
exec(open('collect.py').read().split("pool=sys.argv[1]")[0])
os.chdir('/workspace/rai_pivot/phase2')
old = {x['title'] for x in json.load(open('cand_real.json'))}
titles = []
for c, d in [('Modified red octagonal stop signs', 1), ('Graffiti on road signs', 1), ('Stickers on road signs', 1), ('Modified road signs in London', 0), ('Damaged road signs', 0)]:
    titles += catfiles(c, d, limit=150)
for s in ['zombies ahead', 'hacked electronic road sign', 'changeable message sign prank', 'stop sign sticker eating animals', 'stop sign graffiti war', 'stop sign sticker added word', 'sign altered letters', 'variable message sign joke']:
    titles += search(s, 30)
titles = [t for t in dict.fromkeys(titles) if re.search(r'\.(jpe?g|png)$', t, re.I) and t not in old]
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
for k, x in enumerate(out): x['id'] = f'realb_{k:03d}'
UA = {'User-Agent': 'rai-pivot-research/0.1 (Duke AIPI student project; contact jaideep.aher@duke.edu)'}
def dl(x):
    p = f"thumbs_real/{x['id']}.jpg"
    if os.path.exists(p): return 1
    try:
        r = requests.get(x['thumb'], headers=UA, timeout=30); r.raise_for_status(); open(p, 'wb').write(r.content); return 1
    except Exception: return 0
with cf.ThreadPoolExecutor(4) as ex: print('dl', sum(ex.map(dl, out)))
json.dump(out, open('cand_real2.json', 'w'), indent=0); print('kept', len(out))
from PIL import Image,ImageDraw,ImageFont
ids=[x['id'] for x in out if os.path.exists(f"thumbs_real/{x['id']}.jpg")]
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',15); CW,CH,cols,rows=200,160,8,6; n=cols*rows
for s in range(0,len(ids),n):
    im=Image.new('RGB',(CW*cols,(CH+20)*rows),'white');d=ImageDraw.Draw(im)
    for k,i in enumerate(ids[s:s+n]):
        try: t=Image.open(f'thumbs_real/{i}.jpg').convert('RGB')
        except Exception: continue
        t.thumbnail((CW-4,CH));x=(k%cols)*CW;y=(k//cols)*(CH+20);im.paste(t,(x,y+18));d.text((x+2,y),i[6:],fill='red',font=f)
    im.save(f'sheets/realb_{s//n:02d}.jpg',quality=85)
