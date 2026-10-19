# Display-only privacy copies. Models were run on the UNBLURRED originals; these copies are for slides/poster/report.
# Faces: OpenCV Haar frontal+profile + head region (top 22%) of every YOLO11n person box (conf>=0.25).
# Plates: OpenCV Haar russian_plate_number cascade + lower 30% band of YOLO car/truck/bus boxes is NOT blurred (would destroy scene);
# plate coverage is therefore best-effort and flagged for manual review wherever vehicles are present.
import csv, os, json, cv2, torch
from ultralytics import YOLO
torch.set_num_threads(2)
W = os.path.dirname(os.path.abspath(__file__)); D = f'{W}/pilot_v2'; OUT = '/workspace/rai_pivot/pilot/display_blurred'
os.makedirs(OUT, exist_ok=True)
y = YOLO(f'{W}/yolo11n.pt')
cd = cv2.data.haarcascades
fF = cv2.CascadeClassifier(cd + 'haarcascade_frontalface_default.xml'); fP = cv2.CascadeClassifier(cd + 'haarcascade_profileface.xml')
pl = cv2.CascadeClassifier(cd + 'haarcascade_russian_plate_number.xml')
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
    if not (persons or vehicles or faces or plates):
        status = 'not_needed(no person/vehicle detected)'
    else:
        out = img.copy()
        for (x, yy, w, h) in faces: blur(out, x - .2*w, yy - .2*h, x + 1.2*w, yy + 1.2*h)
        for (x0, y0, x1, y1) in persons: blur(out, x0, y0, x1, y0 + 0.22*(y1 - y0))
        for (x, yy, w, h) in plates: blur(out, x, yy, x + w, yy + h)
        cv2.imwrite(f"{OUT}/{os.path.basename(r['file'])}", out, [cv2.IMWRITE_JPEG_QUALITY, 90])
        status = f'blurred(persons={len(persons)},haar_faces={len(faces)},haar_plates={len(plates)})' + ('; vehicles present: plate blur best-effort, MANUAL REVIEW' if vehicles else '')
    r['blur'] = status; log[r['image_id']] = {'persons': len(persons), 'vehicles': len(vehicles), 'faces': len(faces), 'plates': len(plates)}
cols = list(rows[0].keys())
with open(f'{D}/manifest.csv', 'w', newline='') as f: wr = csv.DictWriter(f, fieldnames=cols); wr.writeheader(); wr.writerows(rows)
json.dump(log, open(f'{OUT}/blur_log.json', 'w'), indent=0)
from collections import Counter
print(Counter(s['blur'].split('(')[0] for s in rows), sum('MANUAL' in s['blur'] for s in rows))
