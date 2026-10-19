# Display-only privacy copies. Models were run on the UNBLURRED originals; these copies are for slides/poster/report.
# Faces: OpenCV Haar frontal+profile + the full YOLO11n person box (conf>=0.25)
# + YuNet faces padded 30% (opencv_zoo face_detection_yunet_2023mar.onnx,
# sha256 8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4).
# Plates: OpenCV Haar russian_plate_number cascade + lower 30% band of YOLO car/truck/bus boxes is NOT blurred (would destroy scene);
# plate coverage is therefore best-effort and flagged for manual review wherever vehicles are present.
import csv, hashlib, os, json, cv2, torch
from ultralytics import YOLO
torch.set_num_threads(2)
W = os.path.dirname(os.path.abspath(__file__)); D = f'{W}/pilot_v2'; OUT = '/workspace/rai_pivot/pilot/display_blurred'
os.makedirs(OUT, exist_ok=True)
y = YOLO(f'{W}/yolo11n.pt')
cd = cv2.data.haarcascades
fF = cv2.CascadeClassifier(cd + 'haarcascade_frontalface_default.xml'); fP = cv2.CascadeClassifier(cd + 'haarcascade_profileface.xml')
pl = cv2.CascadeClassifier(cd + 'haarcascade_russian_plate_number.xml')
YUNET_SHA256 = '8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4'
def load_yunet():
    path = os.environ.get('WHOSTOP_YUNET') or os.path.join(W, 'face_detection_yunet_2023mar.onnx')
    digest = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    if digest != YUNET_SHA256:
        raise SystemExit(f'YuNet sha256 {digest} != {YUNET_SHA256}')
    return cv2.FaceDetectorYN.create(path, '', (320, 320), 0.45, 0.3, 5000)
YN = load_yunet()
def yunet_faces(img):
    YN.setInputSize((img.shape[1], img.shape[0])); _, faces = YN.detect(img)
    return [] if faces is None else [tuple(row[:4]) for row in faces]
rows = list(csv.DictReader(open(f'{D}/manifest.csv'))); log = {}
def blur(img, x0, y0, x1, y1):
    h, w = img.shape[:2]; x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(w, int(x1)), min(h, int(y1))
    if x1 - x0 < 2 or y1 - y0 < 2: return
    k = max(15, ((x1 - x0) // 3) | 1); img[y0:y1, x0:x1] = cv2.GaussianBlur(img[y0:y1, x0:x1], (k, k), 0)
for r in rows:
    p = f"{D}/{r['file']}"; img = cv2.imread(p); g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    det = y(img, verbose=False, conf=0.25)[0]
    persons = [b for b, c in zip(det.boxes.xyxy.tolist(), det.boxes.cls.tolist()) if int(c) == 0]
    vehicles = [b for b, c in zip(det.boxes.xyxy.tolist(), det.boxes.cls.tolist()) if int(c) in (2, 3, 5, 7)]
    faces = list(fF.detectMultiScale(g, 1.1, 5, minSize=(12, 12))) + list(fP.detectMultiScale(g, 1.1, 5, minSize=(12, 12)))
    plates = list(pl.detectMultiScale(g, 1.1, 4, minSize=(20, 8)))
    yfaces = yunet_faces(img)
    if not (persons or vehicles or faces or plates or yfaces):
        status = 'not_needed(no person/vehicle detected)'
    else:
        out = img.copy()
        for (x, yy, w, h) in faces: blur(out, x - .2*w, yy - .2*h, x + 1.2*w, yy + 1.2*h)
        for (x0, y0, x1, y1) in persons: blur(out, x0, y0, x1, y1)
        for (x, yy, w, h) in yfaces: blur(out, x - .3*w, yy - .3*h, x + 1.3*w, yy + 1.3*h)
        for (x, yy, w, h) in plates: blur(out, x, yy, x + w, yy + h)
        cv2.imwrite(f"{OUT}/{os.path.basename(r['file'])}", out, [cv2.IMWRITE_JPEG_QUALITY, 90])
        status = f'blurred(persons={len(persons)},haar_faces={len(faces)},yunet_faces={len(yfaces)},haar_plates={len(plates)})' + ('; vehicles present: plate blur best-effort, MANUAL REVIEW' if vehicles else '')
    r['blur'] = status; log[r['image_id']] = {'persons': len(persons), 'vehicles': len(vehicles), 'faces': len(faces), 'plates': len(plates)}
cols = list(rows[0].keys())
with open(f'{D}/manifest.csv', 'w', newline='') as f: wr = csv.DictWriter(f, fieldnames=cols); wr.writeheader(); wr.writerows(rows)
json.dump(log, open(f'{OUT}/blur_log.json', 'w'), indent=0)
from collections import Counter
print(Counter(s['blur'].split('(')[0] for s in rows), sum('MANUAL' in s['blur'] for s in rows))
