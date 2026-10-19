# Display-only privacy copies (models ran on UNBLURRED originals). Run with venv_cv4 (OpenCV 4 has Haar cascades).
# Blur: Haar frontal+profile faces, head band (top 22%) of every YOLO11n person box (conf>=0.25), Haar plate cascade.
# Plate coverage is best-effort: rows with vehicles are flagged for manual review.
import csv, json, os, cv2
D = '/workspace/rai_pivot/pilot/pilot_v2'; OUT = f'{D}/blurred'; os.makedirs(OUT, exist_ok=True)
dets = json.load(open('/workspace/rai_pivot/pilot/v2work/people_dets.json'))
cd = cv2.data.haarcascades
fF = cv2.CascadeClassifier(cd + 'haarcascade_frontalface_default.xml'); fP = cv2.CascadeClassifier(cd + 'haarcascade_profileface.xml')
pl = cv2.CascadeClassifier(cd + 'haarcascade_russian_plate_number.xml')
def blur(img, x0, y0, x1, y1):
    h, w = img.shape[:2]; x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(w, int(x1)), min(h, int(y1))
    if x1 - x0 < 2 or y1 - y0 < 2: return
    k = max(15, ((x1 - x0) // 3) | 1); img[y0:y1, x0:x1] = cv2.GaussianBlur(img[y0:y1, x0:x1], (k, k), 0)
rows = list(csv.DictReader(open(f'{D}/manifest.csv'))); cols = list(rows[0].keys())
for r in rows:
    img = cv2.imread(f"{D}/{r['file']}"); g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY); d = dets.get(r['image_id'], {'persons': [], 'vehicles': []})
    faces = list(fF.detectMultiScale(g, 1.1, 6, minSize=(14, 14))) + list(fP.detectMultiScale(g, 1.1, 6, minSize=(14, 14)))
    plates = list(pl.detectMultiScale(g, 1.1, 5, minSize=(24, 8)))
    P, V = d['persons'], d['vehicles']
    if not (P or V or faces):
        r['blur'] = 'not_needed (no person/vehicle/face detected; detector-based, unverified)'; r['blurred_file'] = ''; continue
    out = img.copy()
    for (x, y, w, h) in faces: blur(out, x - .2*w, y - .2*h, x + 1.2*w, y + 1.2*h)
    for (x0, y0, x1, y1) in P: blur(out, x0, y0, x1, y0 + 0.22*(y1 - y0))
    for (x, y, w, h) in plates: blur(out, x, y, x + w, y + h)
    fn = os.path.basename(r['file']); cv2.imwrite(f'{OUT}/{fn}', out, [cv2.IMWRITE_JPEG_QUALITY, 90])
    r['blurred_file'] = f'blurred/{fn}'
    r['blur'] = f'blurred (yolo_persons={len(P)}, haar_faces={len(faces)}, haar_plates={len(plates)})' + ('; vehicles present: plate blur best-effort, MANUAL REVIEW' if V else '')
w = csv.DictWriter(open(f'{D}/manifest.csv', 'w', newline=''), fieldnames=cols); w.writeheader(); w.writerows(rows)
import collections; print(collections.Counter(r['blur'].split(' ')[0] for r in rows), sum('MANUAL' in r['blur'] for r in rows))
