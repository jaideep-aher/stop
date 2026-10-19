import json,os,requests,hashlib,concurrent.futures as cf,re,time
S=requests.Session();S.headers['User-Agent']='rai-pivot-research/0.2 (Duke AIPI student project; jaideep.aher@duke.edu)'
import sys
LIM=json.loads(sys.argv[1]) if len(sys.argv)>1 else {}
jobs=[]
for p,n in LIM.items():
    for i,x in enumerate(json.load(open(f'filt_{p}.json'))[:n]):
        x['pool']=p; x['id']=f"{p}_{i:03d}"; jobs.append(x)
def get(x):
    fn=f"thumbs/{x['id']}.jpg"
    if os.path.exists(fn): return x
    for k in range(4):
        try:
            r=S.get(x['thumb'],timeout=60)
            if r.status_code==200: open(fn,'wb').write(r.content); return x
            time.sleep(3*(k+1))
        except Exception: time.sleep(3)
    x['fail']=True; return x
with cf.ThreadPoolExecutor(8) as ex: res=list(ex.map(get,jobs))
old=json.load(open('all_cands.json')) if os.path.exists('all_cands.json') else []
ids={x['id'] for x in old}
res=old+[x for x in res if x['id'] not in ids]
json.dump(res,open('all_cands.json','w'),indent=0)
print(len(res),sum(1 for x in res if x.get('fail')))
