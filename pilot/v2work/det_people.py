import csv, json, torch
from ultralytics import YOLO
torch.set_num_threads(2)
D = '/workspace/rai_pivot/pilot/pilot_v2'; y = YOLO('/workspace/rai_pivot/pilot/v2work/yolo11n.pt'); out = {}
for r in csv.DictReader(open(f'{D}/manifest.csv')):
    det = y(f"{D}/{r['file']}", verbose=False, conf=0.25)[0]
    out[r['image_id']] = {'persons': [b for b, c in zip(det.boxes.xyxy.tolist(), det.boxes.cls.tolist()) if int(c) == 0],
                          'vehicles': [b for b, c in zip(det.boxes.xyxy.tolist(), det.boxes.cls.tolist()) if int(c) in (2, 3, 5, 7)]}
json.dump(out, open('/workspace/rai_pivot/pilot/v2work/people_dets.json', 'w'))
print(len(out))
