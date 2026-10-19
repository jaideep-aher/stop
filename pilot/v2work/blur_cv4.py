# Display-only privacy copies (models ran on UNBLURRED originals). Run with venv_cv4 (OpenCV 4 has Haar cascades).
# Blur: Haar frontal+profile faces, the FULL YOLO11n person box (conf>=0.25), YuNet faces padded 30%, Haar plates.
# The retired head band (top 22% of the person box) left faces visible in crowds. Not a coordinate bug.
# YuNet: opencv_zoo face_detection_yunet_2023mar.onnx, sha256 8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4.
# Plate coverage is best-effort: rows with vehicles are flagged for manual review.
import csv, hashlib, json, os, cv2
D = '/workspace/rai_pivot/pilot/pilot_v2'; OUT = f'{D}/blurred'; os.makedirs(OUT, exist_ok=True)
dets = json.load(open('/workspace/rai_pivot/pilot/v2work/people_dets.json'))
cd = cv2.data.haarcascades
fF = cv2.CascadeClassifier(cd + 'haarcascade_frontalface_default.xml'); fP = cv2.CascadeClassifier(cd + 'haarcascade_profileface.xml')
pl = cv2.CascadeClassifier(cd + 'haarcascade_russian_plate_number.xml')
YUNET_SHA256 = '8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4'
def load_yunet():
    path = os.environ.get('WHOSTOP_YUNET') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'face_detection_yunet_2023mar.onnx')
    digest = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    if digest != YUNET_SHA256:
        raise SystemExit(f'YuNet sha256 {digest} != {YUNET_SHA256}')
    return cv2.FaceDetectorYN.create(path, '', (320, 320), 0.45, 0.3, 5000)
YN = load_yunet()
def yunet_faces(img):
    YN.setInputSize((img.shape[1], img.shape[0])); _, faces = YN.detect(img)
    return [] if faces is None else [tuple(row[:4]) for row in faces]
def blur(img, x0, y0, x1, y1):
    h, w = img.shape[:2]; x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(w, int(x1)), min(h, int(y1))
    if x1 - x0 < 2 or y1 - y0 < 2: return
    k = max(15, ((x1 - x0) // 3) | 1); img[y0:y1, x0:x1] = cv2.GaussianBlur(img[y0:y1, x0:x1], (k, k), 0)
rows = list(csv.DictReader(open(f'{D}/manifest.csv'))); cols = list(rows[0].keys())
for r in rows:
    img = cv2.imread(f"{D}/{r['file']}"); g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY); d = dets.get(r['image_id'], {'persons': [], 'vehicles': []})
    faces = list(fF.detectMultiScale(g, 1.1, 6, minSize=(14, 14))) + list(fP.detectMultiScale(g, 1.1, 6, minSize=(14, 14)))
    plates = list(pl.detectMultiScale(g, 1.1, 5, minSize=(24, 8)))
    yfaces = yunet_faces(img)
    P, V = d['persons'], d['vehicles']
    if not (P or V or faces or yfaces):
        r['blur'] = 'not_needed (no person/vehicle/face detected; detector-based, unverified)'; r['blurred_file'] = ''; continue
    out = img.copy()
    for (x, y, w, h) in faces: blur(out, x - .2*w, y - .2*h, x + 1.2*w, y + 1.2*h)
    for (x0, y0, x1, y1) in P: blur(out, x0, y0, x1, y1)
    for (x, y, w, h) in yfaces: blur(out, x - .3*w, y - .3*h, x + 1.3*w, y + 1.3*h)
    for (x, y, w, h) in plates: blur(out, x, y, x + w, y + h)
    fn = os.path.basename(r['file']); cv2.imwrite(f'{OUT}/{fn}', out, [cv2.IMWRITE_JPEG_QUALITY, 90])
    r['blurred_file'] = f'blurred/{fn}'
    r['blur'] = f'blurred (yolo_persons={len(P)}, haar_faces={len(faces)}, yunet_faces={len(yfaces)}, haar_plates={len(plates)})' + ('; vehicles present: plate blur best-effort, MANUAL REVIEW' if V else '')
w = csv.DictWriter(open(f'{D}/manifest.csv', 'w', newline=''), fieldnames=cols); w.writeheader(); w.writerows(rows)
import collections; print(collections.Counter(r['blur'].split(' ')[0] for r in rows), sum('MANUAL' in r['blur'] for r in rows))
