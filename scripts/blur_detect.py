#!/usr/bin/env python3
"""Pass 2 of the detector-based privacy blur for display copies. Source images are read-only.
Pass 1 (yolo_boxes.py) gives YOLO11n person + vehicle boxes at conf 0.15 (when unsure, blur).
Pass 2 (this script) adds OpenCV Haar frontal/profile faces and Haar plates.
Rules, chosen so the detectors do not erase the board legends under study:
  * Scene-level detections per base: every variant of a base gets the UNION of YOLO boxes across all its variants,
    plus Haar faces/plates detected on the base's UNEDITED variant (clean / sclean). Edited legend text is never the trigger.
  * Plate hits are kept only inside (20%-expanded) vehicle boxes. Face hits are always kept (when unsure, blur).
  * Persons: whole box. Vehicles: lower 60% of box. Faces/plates: box + 30% margin.
Status is always 'detector-based, unverified'. Output JPEG, long side 960 px.
Usage: blur_detect.py <out_csv> <out_dir> <rel_prefix> <boxes.json>  < stdin CSV id,src[,group_id,is_unedited]"""
import sys, csv, os, json, cv2
out_csv, out_dir, rel, boxes_json = sys.argv[1:5]
BOX = json.load(open(boxes_json))
HD = cv2.data.haarcascades
FACES = [cv2.CascadeClassifier(HD + f) for f in ('haarcascade_frontalface_default.xml', 'haarcascade_profileface.xml')]
PLATES = [cv2.CascadeClassifier(HD + f) for f in ('haarcascade_russian_plate_number.xml', 'haarcascade_license_plate_rus_16stages.xml')]
def load(src):
    img = cv2.imread(src)
    if img is None: return None
    sc = 960 / max(img.shape[:2])
    if sc < 1: img = cv2.resize(img, (round(img.shape[1] * sc), round(img.shape[0] * sc)), interpolation=cv2.INTER_AREA)
    return img
def blur(img, x1, y1, x2, y2):
    h, w = img.shape[:2]; x1, y1, x2, y2 = max(0, int(x1)), max(0, int(y1)), min(w, int(x2)), min(h, int(y2))
    if x2 - x1 < 2 or y2 - y1 < 2: return
    roi = img[y1:y2, x1:x2]; k = max(15, (max(x2 - x1, y2 - y1) // 3) | 1)
    small = cv2.resize(roi, (max(1, (x2 - x1) // 12), max(1, (y2 - y1) // 12)), interpolation=cv2.INTER_LINEAR)
    img[y1:y2, x1:x2] = cv2.GaussianBlur(cv2.resize(small, (x2 - x1, y2 - y1), interpolation=cv2.INTER_NEAREST), (k, k), 0)
def inside(b, vs):
    x, y, w, h = b; cx, cy = x + w / 2, y + h / 2
    return any(v[0] - .2 * (v[2] - v[0]) <= cx <= v[2] + .2 * (v[2] - v[0]) and v[1] - .2 * (v[3] - v[1]) <= cy <= v[3] + .2 * (v[3] - v[1]) for v in vs)
rows = [r + [r[0], '1'][len(r) - 2:] if len(r) < 4 else r for r in csv.reader(sys.stdin)]
groups = {}
for iid, src, g, une in rows: groups.setdefault(g, []).append((iid, src, une == '1'))
w = csv.writer(open(out_csv, 'w', newline=''))
w.writerow(['image_id', 'source_file', 'blurred_file', 'persons', 'vehicles', 'faces', 'plates', 'blur_status', 'needs_human_check', 'check_reason'])
import numpy as np
def legend_mask(items, rimg):  # pixels that differ between the unedited variant and any edited variant = edited board legend
    m = None
    for iid, src, u in items:
        if u: continue
        im = load(src)
        if im is None or rimg is None or im.shape != rimg.shape: continue
        d = (cv2.cvtColor(cv2.absdiff(im, rimg), cv2.COLOR_BGR2GRAY) > 40).astype(np.uint8)
        m = d if m is None else (m | d)
    if m is not None: m = cv2.dilate(m, np.ones((15, 15), np.uint8))
    return m
def hits_legend(b, m):
    if m is None: return False
    x, y, ww, hh = map(int, b); r = m[max(0, y):y + hh, max(0, x):x + ww]
    return r.size > 0 and r.mean() > 0.10
def in_person(b, ps):
    x, y, ww, hh = b; cx, cy = x + ww / 2, y + hh / 2
    return any(p[0] <= cx <= p[2] and p[1] <= cy <= p[3] for p in ps)
for g, items in groups.items():
    yb = [b for iid, _, _ in items for b in BOX.get(iid, [])]
    pers = [b[:4] for b in yb if b[4] == 0]; veh = [b[:4] for b in yb if b[4] != 0]
    ref = next(((i, s) for i, s, u in items if u), items[0][:2]); rimg = load(ref[1])
    faces, plates = [], []
    if rimg is not None:
        gray = cv2.equalizeHist(cv2.cvtColor(rimg, cv2.COLOR_BGR2GRAY))
        for C in FACES: faces += [tuple(map(int, f)) for f in C.detectMultiScale(gray, 1.1, 3, minSize=(12, 12))]
        for C in PLATES: plates += [tuple(map(int, p)) for p in C.detectMultiScale(gray, 1.1, 3, minSize=(16, 6)) if inside(p, veh)]
    lm = legend_mask(items, rimg); gr = []
    if any(hits_legend(b, lm) for b in faces + plates): gr.append('face/plate detector box overlaps the edited board legend (likely false hit; legend blurred, kept per blur-when-unsure)')
    elif any(not in_person(f, pers) for f in faces): gr.append('face detector box outside any person box (possible false hit on sign/scenery; kept blurred)')
    for iid, src, _ in items:
        img = load(src)
        if img is None: w.writerow([iid, src, '', '', '', '', '', 'ERROR: unreadable']); continue
        if rimg is not None and img.shape != rimg.shape:  # different geometry: use this image's own boxes only, faces re-detected
            gray = cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)); ff = [f for C in FACES for f in C.detectMultiScale(gray, 1.1, 3, minSize=(12, 12))]
        else: ff = faces
        for b in pers: blur(img, *b)
        for x1, y1, x2, y2 in veh: blur(img, x1, y1 + .4 * (y2 - y1), x2, y2)
        for (x, y, ww, hh) in list(ff) + plates: blur(img, x - .3 * ww, y - .3 * hh, x + 1.3 * ww, y + 1.3 * hh)
        fn = f'{iid}.jpg'; cv2.imwrite(os.path.join(out_dir, fn), img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        n = len(pers) + len(veh) + len(ff) + len(plates)
        w.writerow([iid, src, f'{rel}/{fn}', len(pers), len(veh), len(ff), len(plates), ('blurred' if n else 'no_detections') + ' (detector-based, unverified)',
                    'yes' if (gr or not n) else 'no', '; '.join(gr + ([] if n else ['no detections: re-encoded original is unverified; withheld pending human check']))])
print('done', out_csv)
