"""Detector re-check on published copies, same settings as docs/PRIVACY_AUDIT.md:
Haar frontal+profile (minNeighbors=3) and YuNet (score 0.45, 1x and 2x)."""
import cv2,sys,csv,hashlib,os
H=cv2.data.haarcascades
fr=cv2.CascadeClassifier(H+'haarcascade_frontalface_default.xml'); pr=cv2.CascadeClassifier(H+'haarcascade_profileface.xml')
M=os.environ.get('WHOSTOP_YUNET', 'face_detection_yunet_2023mar.onnx')
def yun(img):
    h,w=img.shape[:2]; d=cv2.FaceDetectorYN.create(M,'',(w,h),0.45,0.3,5000); _,f=d.detect(img); return [] if f is None else f
def chk(p):
    img=cv2.imread(p); g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    hf=len(fr.detectMultiScale(g,1.1,3)); hp=len(pr.detectMultiScale(g,1.1,3))+len(pr.detectMultiScale(cv2.flip(g,1),1.1,3))
    y1=len(yun(img)); y2=len(yun(cv2.resize(img,None,fx=2,fy=2)))
    return hf,hp,y1,y2
w=csv.writer(sys.stdout); w.writerow(['path','sha256','haar_frontal','haar_profile','yunet_1x','yunet_2x','result'])
for line in sys.stdin:
    p=line.strip()
    if not p: continue
    r=chk(p); w.writerow([p,hashlib.sha256(open(p,'rb').read()).hexdigest(),*r,'pass' if sum(r)==0 else 'fail'])
