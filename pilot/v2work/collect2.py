import json,re,sys
sys.argv=['x','illegit']
exec(open('collect.py').read().split("pool=sys.argv[1]")[0])
titles=[]
for c,d in [('Stop sign symbols associated with demonstrations and protests',1)]: titles+=catfiles(c,d,limit=150)
for s in ['protester holding stop sign','demonstrator stop sign placard','person holding stop sign','stop sign costume','stop sign on truck','stop sign for sale antique','stop sign shop window','stop sign decoration wall','stop sign artwork','stop sign mural painting','stop sign parody','stop sign sculpture','stop sign souvenir shop','stop sign museum display','stop sign on vehicle','stop sign advertising','stop sign billboard advertisement','stop sign t-shirt','stop sign toy','stop sign sticker car','stop sign garage collection','stop sign umbrella','street art stop','Stop sign placard march']:
    titles+=search(s,40)
titles=list(dict.fromkeys(t for t in titles if re.search(r'\.(jpe?g|png)$',t,re.I)))
old={x['title'] for x in json.load(open('all_cands.json'))}
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
json.dump(out,open('cand_illegit2.json','w'),indent=0);print('kept',len(out))
