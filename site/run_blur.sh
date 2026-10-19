#!/bin/sh
# Detector-based blur for site display copies. Inputs regenerated from the read-only manifests.
# Pass 1: YOLO boxes (pilot/venv), cached per set and re-run only when that set's input list changes.
# Pass 2: Haar faces/plates + blur + needs_human_check flags (pilot/venv_cv4).
set -e
cd "$(dirname "$0")"
ROOT="$(cd .. && pwd)"
# YOLO and OpenCV may live in different interpreters. Both default to python3 on PATH.
A="${WHOSTOP_YOLO_PYTHON:-${WHOSTOP_PYTHON:-python3}}"
B="${WHOSTOP_CV_PYTHON:-${WHOSTOP_PYTHON:-python3}}"
I=blur_inputs; mkdir -p "$I"
"$A" make_blur_inputs.py "$I" --root "$ROOT"
for s in p2:phase2_blur real:phase2_real_blur pilot:pilot_notneeded_blur; do k=${s%%:*}; c=${s##*:}; mkdir -p blurred/$k
  if [ ! -f $I/boxes_$k.json ] || ! cmp -s $I/in_$k.csv $I/cached_in_$k.csv; then
    echo "YOLO pass for $k"; "$A" yolo_boxes.py $I/boxes_$k.json < $I/in_$k.csv; cp $I/in_$k.csv $I/cached_in_$k.csv; fi
  rm -f blurred/$k/*
  "$B" blur_detect.py site/data/$c.csv blurred/$k blurred/$k $I/boxes_$k.json < $I/in_$k.csv; done
