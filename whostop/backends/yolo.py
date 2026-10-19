"""Detector boxes for the blur pipeline.

ONNX Runtime and Ultralytics are imported only when a weight file is opened.
Tests pass ``predict``. No weight file is committed, and CI does not load one.
"""

from __future__ import annotations

import os
from pathlib import Path

from whostop.backends.errors import GenerationError

# COCO class ids used as privacy boxes in the site blur: person and vehicles.
PRIVACY_CLASS_IDS = frozenset({0, 2, 3, 5, 7})


class YoloBackend:
    """Return ``(x1, y1, x2, y2, class_id)`` boxes for one image."""

    def __init__(self, *, predict=None, weights: Path | None = None):
        self._predict = predict
        self.weights = Path(weights) if weights else None
        if predict is None and weights is not None:
            if os.environ.get("WHOSTOP_FORBID_REMOTE") == "1":
                raise GenerationError("Remote backends are disabled (WHOSTOP_FORBID_REMOTE=1).")
            self._predict = _loader_for(self.weights)

    def boxes(self, image) -> list[tuple]:
        if self._predict is None:
            raise GenerationError("No YOLO runtime is configured.")
        found = []
        for box in self._predict(image):
            x1, y1, x2, y2, class_id = box[:5]
            if int(class_id) in PRIVACY_CLASS_IDS:
                found.append((float(x1), float(y1), float(x2), float(y2), int(class_id)))
        return found


def _loader_for(weights: Path):
    suffix = weights.suffix.lower()
    if suffix == ".onnx":
        return _onnx_predict(weights)
    if suffix == ".pt":
        return _ultralytics_predict(weights)
    raise GenerationError(f"Unsupported detector weights: {weights.name}")


def _onnx_predict(weights: Path):
    try:
        import onnxruntime as ort
    except ImportError as exc:
        raise GenerationError("onnxruntime is not installed.") from exc
    session = ort.InferenceSession(str(weights))

    def predict(_image):
        raise GenerationError(
            f"ONNX session {session.get_inputs()[0].name} is loaded, but image preprocessing "
            "is model-specific and is not run from this helper."
        )

    return predict


def _ultralytics_predict(weights: Path):
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise GenerationError("ultralytics is not installed.") from exc
    model = YOLO(str(weights))

    def predict(image):
        result = model(image, verbose=False)[0]
        boxes = []
        for xyxy, class_id in zip(result.boxes.xyxy.tolist(), result.boxes.cls.tolist(), strict=True):
            boxes.append((*xyxy, int(class_id)))
        return boxes

    return predict
