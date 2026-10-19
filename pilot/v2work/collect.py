import json,time,re,sys,os,urllib.parse,requests
S=requests.Session();S.headers['User-Agent']='rai-pivot-research/0.2 (Duke AIPI student project; jaideep.aher@duke.edu)'
API='https://commons.wikimedia.org/w/api.php'
def q(**p):
    p.update(format='json')
    for i in range(5):
        try: return S.get(API,params=p,timeout=60).json()
        except Exception as e: time.sleep(5*(i+1))
    return {}
def catfiles(c,depth=0,limit=200):
    out=[];cont={}
    while len(out)<limit:
        r=q(action='query',list='categorymembers',cmtitle='Category:'+c,cmlimit=500,cmtype='file|subcat',**cont)
        for m in r.get('query',{}).get('categorymembers',[]):
            if m['ns']==6: out.append(m['title'])
            elif depth>0: out+=catfiles(m['title'][9:],depth-1,limit=60)
        if 'continue' in r: cont={'cmcontinue':r['continue']['cmcontinue']}
        else: break
    return out[:limit]
def search(s,n=50):
    r=q(action='query',list='search',srsearch=s,srnamespace=6,srlimit=n)
    return [x['title'] for x in r.get('query',{}).get('search',[])]
POOLS={
 'stop':dict(cats=[('Stop signs in the United States by state',1),('R1-1 - Stop',0),('Stop signs in North Carolina',0)],srch=['stop sign intersection road','all way stop sign street','stop sign rural road']),
 'road':dict(cats=[],srch=['empty road united states','rural road north carolina','two-lane highway','country road straight','interstate highway lanes traffic','residential street united states','divided highway','road through forest']),
 'legit':dict(cats=[('Handheld stop signs',1),('Crossing guards',1),('Traffic police',0)],srch=['flagger stop slow sign','flagger road work','school bus stop arm','school bus stop sign extended','crossing guard stop sign','police officer directing traffic','lollipop lady school crossing','road construction flagman']),
 'illegit':dict(cats=[],srch=['stop sign protest','stop sign billboard','stop sign advertisement','stop sign souvenir','stop sign shop','stop sign mural','stop sign art installation','protest sign stop','stop sign t-shirt','stop sign graffiti','stop sign museum','stop signs for sale','stop sign wall decoration']),
 'board':dict(cats=[('Distance road signs',1),('Variable-message road sign trailers',0),('Variable-message road signs',1)],srch=['interstate guide sign green','highway exit sign','green highway sign miles','overhead guide sign interstate','destination sign miles road']),
}
pool=sys.argv[1]; cfg=POOLS[pool]; titles=[]
for c,d in cfg['cats']: titles+=catfiles(c,d)
for s in cfg['srch']: titles+=search(s)
titles=list(dict.fromkeys(t for t in titles if re.search(r'\.(jpe?g|png)$',t,re.I)))
print(pool,'titles',len(titles))
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
json.dump(out,open(f'cand_{pool}.json','w'),indent=0)
print(pool,'kept',len(out))
