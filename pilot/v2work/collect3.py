import json,re,sys
sys.argv=['x','illegit']
exec(open('collect.py').read().split("pool=sys.argv[1]")[0])
titles=[]

for s in ['Stop & Shop supermarket sign','Stop and Shop store exterior','Stop N Go store sign','truck stop sign highway','Pit stop sign','bus stop sign street','bus stop pole sign road','tram stop sign street','protest march street stop banner','picket line stop sign street','stop the war march street','stop sign shaped billboard roadside','car wash stop sign','STOP lettering on truck back','rest stop sign highway','one stop shop sign street']:
    titles+=search(s,25)
titles=list(dict.fromkeys(t for t in titles if re.search(r'\.(jpe?g|png)$',t,re.I)))
old={x['title'] for x in json.load(open('all_cands.json'))}|{x['title'] for x in json.load(open('cand_illegit2.json'))}
titles=[t for t in titles if t not in old]
print('titles',len(titles))
FREE=re.compile(r'^(CC BY(-SA)? ?[0-9.]*|CC0|Public domain|PD.*|CC BY-SA [0-9.]+ .*|CC BY [0-9.]+ .*)$',re.I)
out=[]
for i in range(0,len(titles),40):
    r=q(action='query',titles='|'.join(titles[i:i+40]),prop='imageinfo',iiprop='url|extmetadata|size|mime',iiurlwidth=640)
    for p in r.get('query',{}).get('pages',{}).values():
        if 'imageinfo' not in p: continue
        ii=p['imageinfo'][0]; m=ii.get('extmetadata',{})
        lic=m.get('LicenseShortName',{}).get('value','')
        if not FREE.match(lic.strip()) or ii.get('width',0)<500: continue
        out.append(dict(title=p['title'],thumb=ii.get('thumburl'),page=ii['descriptionurl'],license=lic,artist=re.sub('<[^>]+>','',m.get('Artist',{}).get('value',''))[:120].strip(),w=ii['width'],h=ii['height']))
json.dump(out,open('cand_illegit3.json','w'),indent=0);print('kept',len(out))
