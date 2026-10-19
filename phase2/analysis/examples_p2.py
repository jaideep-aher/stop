# Builds blurred display pairs (models ran on UNBLURRED originals). Blur: YOLO11n persons -> top 30% (head) band; vehicles (car/bus/truck/motorcycle) -> lower 55% (plate zone); conf>=0.2.
import json, sys, os, cv2, numpy as np, textwrap
os.environ['OMP_NUM_THREADS']='1'
from ultralytics import YOLO
P2='/workspace/rai_pivot/phase2'; OUT=f'{P2}/examples'; os.makedirs(OUT,exist_ok=True)
y=YOLO('/workspace/rai_pivot/pilot/v2work/yolo11n.pt')
def blurred(path):
    im=cv2.imread(path); r=y(im,verbose=False,conf=.2)[0]; n=[0,0]
    for (x0,y0,x1,y1),k in zip(r.boxes.xyxy.tolist(),r.boxes.cls.tolist()):
        k=int(k)
        if k==0: ys=(y0,y0+.3*(y1-y0)); n[0]+=1
        elif k in (2,3,5,7): ys=(y0+.45*(y1-y0),y1); n[1]+=1
        else: continue
        a,b,c,d=int(max(0,x0)),int(max(0,ys[0])),int(min(im.shape[1],x1)),int(min(im.shape[0],ys[1]))
        if c-a>2 and d-b>2: kk=max(15,((c-a)//3)|1); im[b:d,a:c]=cv2.GaussianBlur(im[b:d,a:c],(kk,kk),0)
    return im,n
def tile(im,cap,W=640):
    h=int(im.shape[0]*W/im.shape[1]); im=cv2.resize(im,(W,h)); lines=sum((textwrap.wrap(c,78) for c in cap.split('\n')),[])
    band=np.full((18*len(lines)+8,W,3),255,np.uint8)
    for i,l in enumerate(lines): cv2.putText(band,l,(6,18+18*i),cv2.FONT_HERSHEY_SIMPLEX,.47,(0,0,0),1,cv2.LINE_AA)
    return np.vstack([im,band])
spec=json.load(open(sys.argv[1])); log=[]
for k,e in enumerate(spec):
    A,na=blurred(f"{P2}/stimuli/{e['a']}"); B,nb=blurred(f"{P2}/stimuli/{e['b']}")
    ta,tb=tile(A,e['cap_a']),tile(B,e['cap_b']); H=max(ta.shape[0],tb.shape[0])
    pad=lambda t:np.vstack([t,np.full((H-t.shape[0],t.shape[1],3),255,np.uint8)])
    img=np.hstack([pad(ta),np.full((H,10,3),255,np.uint8),pad(tb)]); fn=f"{OUT}/pair_{k+1}_{e['name']}.jpg"; cv2.imwrite(fn,img,[cv2.IMWRITE_JPEG_QUALITY,88])
    log.append({'file':os.path.basename(fn),'a':e['a'],'b':e['b'],'blur_persons_vehicles_a':na,'blur_persons_vehicles_b':nb})
json.dump(log,open(f'{OUT}/examples_blur_log.json','w'),indent=1); print(log)
