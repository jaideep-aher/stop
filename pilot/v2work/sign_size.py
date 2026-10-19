# Per-block size of the largest YOLO11n "stop sign" box (conf>=0.25) as a share of frame area, on original (unedited) images only.
import csv, json, torch, statistics as st
from ultralytics import YOLO
torch.set_num_threads(1)
D = '/workspace/rai_pivot/pilot/pilot_v2'; y = YOLO('/workspace/rai_pivot/pilot/v2work/yolo11n.pt'); per = {}
for r in csv.DictReader(open(f'{D}/manifest.csv')):
    if r['variant'] not in ('original', 'clean'): continue
    det = y(f"{D}/{r['file']}", verbose=False, conf=0.25)[0]; h, w = det.orig_shape
    a = [((b[2]-b[0])*(b[3]-b[1]))/(w*h) for b, c in zip(det.boxes.xyxy.tolist(), det.boxes.cls.tolist()) if int(c) == 11]
    k = r['block'] + ('|' + r['label'] if r['block'] in ('G', 'A_plus', 'A_minus_supp') else '')
    per.setdefault(k, []).append(max(a) if a else None)
out = {}
for k, v in sorted(per.items()):
    d = [x for x in v if x is not None]
    out[k] = {'n_images': len(v), 'n_with_yolo_stop': len(d), 'median_area_pct': round(100*st.median(d), 2) if d else None,
              'p25_pct': round(100*st.quantiles(d, n=4)[0], 2) if len(d) > 3 else None, 'p75_pct': round(100*st.quantiles(d, n=4)[2], 2) if len(d) > 3 else None}
json.dump(out, open('/workspace/rai_pivot/pilot/run/sign_size_by_block.json', 'w'), indent=1); print(json.dumps(out, indent=0))
