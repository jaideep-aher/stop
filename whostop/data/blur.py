"""Privacy-blur geometry for person boxes and YuNet faces.

The pilot display blur used to blur only the
top 22% of each YOLO person box, as a stand-in for the head, plus strict Haar
hits. That is not a coordinate-offset bug: sizes match, there is no EXIF
orientation, and the boxes are xyxy in the original pixel space. In crowd
shots the top of the box is hair, a raised arm, or a placard, so the face
sits below the strip. On ill2_037 the strips end near y = 486–488 and the
faces run about y = 500–620.

``person_blur_box`` returns the whole xyxy rectangle. ``yunet_blur_box`` pads
a YuNet face (x, y, w, h) by 30% on each side. The YuNet weights are
opencv_zoo ``face_detection_yunet_2023mar.onnx``, pinned by
``YUNET_SHA256``. The file is not committed (``.onnx`` is git-ignored).

Copyright (c) 2026 Jaideep Aher. MIT License. See NOTICE.
"""

from __future__ import annotations

from collections.abc import Sequence

# opencv_zoo models/face_detection_yunet/face_detection_yunet_2023mar.onnx
YUNET_SHA256 = "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"


def person_blur_box(box: Sequence[float]) -> tuple[float, float, float, float]:
    """Full person rectangle in xyxy order, top through bottom."""
    x1, y1, x2, y2 = (float(box[0]), float(box[1]), float(box[2]), float(box[3]))
    if x2 <= x1 or y2 <= y1:
        raise ValueError("person box must be xyxy with x2 > x1 and y2 > y1")
    return (x1, y1, x2, y2)


def head_band_box(box: Sequence[float], fraction: float = 0.22) -> tuple[float, float, float, float]:
    """The retired head strip: top ``fraction`` of the person box. Not used to publish."""
    x1, y1, x2, y2 = person_blur_box(box)
    return (x1, y1, x2, y1 + fraction * (y2 - y1))


def yunet_blur_box(xywh: Sequence[float], pad: float = 0.3) -> tuple[float, float, float, float]:
    """YuNet face (x, y, w, h) expanded by ``pad`` on every side, as xyxy."""
    x, y, w, h = (float(xywh[0]), float(xywh[1]), float(xywh[2]), float(xywh[3]))
    if w <= 0 or h <= 0:
        raise ValueError("YuNet face must have positive width and height")
    return (x - pad * w, y - pad * h, x + (1.0 + pad) * w, y + (1.0 + pad) * h)
