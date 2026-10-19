#!/usr/bin/env python3
"""Pass 1 (ultralytics). YOLO11n person/vehicle boxes at conf 0.15 on the 960-px display size.

stdin CSV id,src -> JSON. Weights are not in the repo. Set WHOSTOP_YOLO_WEIGHTS
to a local .pt or .onnx file.
"""
import os, sys, csv, json
from PIL import Image
from ultralytics import YOLO
WEIGHTS = os.environ.get("WHOSTOP_YOLO_WEIGHTS", "").strip()
if not WEIGHTS:
    sys.exit("WHOSTOP_YOLO_WEIGHTS is not set. Point it at a local YOLO weight file. Weights are not committed.")
Y = YOLO(WEIGHTS); out = {}
for iid, src in csv.reader(sys.stdin):
    im = Image.open(src).convert('RGB'); im.thumbnail((960, 960))
    r = Y(im, conf=0.15, verbose=False)[0]
    out[iid] = [[*map(float, b), int(c)] for b, c in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist()) if int(c) in (0, 2, 3, 5, 7)]
json.dump(out, open(sys.argv[1], 'w'))
print('boxes', len(out))
