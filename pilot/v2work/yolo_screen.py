import json,os
from ultralytics import YOLO
m=YOLO('yolo11n.pt')
c=json.load(open('all_cands.json'))
for x in c:
    fn=f"thumbs/{x['id']}.jpg"
    if x.get('fail') or not os.path.exists(fn): continue
    try: r=m(fn,verbose=False,conf=0.25)[0]
    except Exception as e: x['fail']=True; continue
    H,W=r.orig_shape
    det=[dict(cls=int(k),conf=round(float(cf),3),box=[round(v) for v in b]) for k,cf,b in zip(r.boxes.cls.tolist(),r.boxes.conf.tolist(),r.boxes.xyxy.tolist())]
    x['W'],x['H']=W,H
    x['stops']=[d for d in det if d['cls']==11]
    x['persons']=sum(1 for d in det if d['cls']==0)
    x['vehicles']=sum(1 for d in det if d['cls'] in (2,3,5,7))
    x['lights']=sum(1 for d in det if d['cls']==9)
json.dump(c,open('all_cands.json','w'),indent=0)
from collections import Counter
print(Counter((x['pool'],bool(x.get('stops'))) for x in c if not x.get('fail')))
