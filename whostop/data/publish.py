"""License check, detector-box blur, and the publish filter.

Redistributable licenses are CC0, public domain, CC BY, and CC BY-SA.
CC BY-NC, CC BY-ND, and any other license are refused. Mapillary and BDD100K
are refused even if a row names a free license: no such images are in the
manifests today, and the filter still blocks them.

An image is published only when it is licensed, has a credit and a source
URL, has been blurred from at least one detector box (or an existing blur
record that is not ``no_detections``), and ``needs_human_check`` is explicitly
no. A manual-review note in the blur column is a flag. Zero detector boxes
are a flag: the copy would be an unverified re-encode, and it is not published.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

_BLOCKED_SOURCE = re.compile(r"mapillary|bdd100k|bdd-100k|bdd_100k", re.IGNORECASE)
_LICENSE_OK = re.compile(r"^cc by( sa)?( \d+(\.\d+)?)?$")


def is_redistributable_license(text: str) -> bool:
    """True for CC0, public domain / PD, CC BY, and CC BY-SA only."""
    raw = " ".join((text or "").lower().replace("_", " ").replace("-", " ").split())
    if not raw:
        return False
    if re.search(r"\bnc\b|non ?commercial|\bnd\b|no ?deriv", raw):
        return False
    if "cc0" in raw or "public domain" in raw or raw in {"pd", "publicdomain"}:
        return True
    return _LICENSE_OK.fullmatch(raw) is not None


def _source_blob(row: Mapping) -> str:
    return " ".join(
        str(row.get(key) or "")
        for key in ("source_url", "source", "credit", "license", "file", "image_id")
    )


def human_check_reasons(row: Mapping, *, n_boxes: int | None = None) -> list[str]:
    """Reasons the row still needs a person, or an empty list when it is cleared."""
    reasons = []
    flag = row.get("needs_human_check_flag")
    if flag is None:
        raw = str(row.get("needs_human_check") or "").strip().lower()
        if raw in {"yes", "true", "1", "y"}:
            flag = True
        elif raw in {"no", "false", "0", "n"}:
            flag = False
    if flag is True:
        reasons.append("flagged")
    elif flag is None:
        reasons.append("needs_human_check_not_recorded")
    blur = str(row.get("blur") or "")
    upper = blur.upper()
    if "MANUAL REVIEW" in upper:
        reasons.append("manual_review")
    if blur.lower().startswith("no_detections"):
        reasons.append("no_detections")
    if n_boxes == 0:
        reasons.append("no_detections")
    return reasons


def decide_publication(row: Mapping, *, n_boxes: int | None = None) -> dict:
    """Return ``publish`` and the refusal reasons.

    ``n_boxes`` is the number of detector boxes that were blurred. Pass 0 when
    the detector found nothing. Omit it when the decision rests on the blur
    column alone; a column that does not start with a blur record is refused
    as unblurred.
    """
    reasons: list[str] = []
    if not is_redistributable_license(str(row.get("license") or "")):
        reasons.append("unlicensed")
    if _BLOCKED_SOURCE.search(_source_blob(row)):
        reasons.append("nonredistributable_source")
    if not str(row.get("credit") or "").strip():
        reasons.append("no_credit")
    if not str(row.get("source_url") or "").strip():
        reasons.append("no_source_url")
    flags = human_check_reasons(row, n_boxes=n_boxes)
    if flags:
        reasons.append("needs_human_check")
        reasons.extend(flags)
    if not _has_blur(row, n_boxes=n_boxes):
        reasons.append("unblurred")
    # Preserve order while dropping duplicates.
    deduped: list[str] = []
    for reason in reasons:
        if reason not in deduped:
            deduped.append(reason)
    edited = row.get("edited_flag")
    if edited is None:
        edited_text = str(row.get("edited") or "").strip().lower()
        edited = edited_text.startswith("yes") or edited_text in {"true", "1"}
    return {
        "publish": not deduped,
        "reasons": deduped,
        "needs_human_check": bool(flags),
        "edited": bool(edited),
        "license": str(row.get("license") or ""),
    }


def _has_blur(row: Mapping, *, n_boxes: int | None) -> bool:
    if n_boxes is not None:
        return n_boxes > 0
    blur = str(row.get("blur") or "").strip().lower()
    if not blur or blur.startswith("no_detections") or blur.startswith("not_needed"):
        return False
    return blur.startswith("blurred") or "detector" in blur


def blur_boxes(image, boxes: Sequence[Sequence[float]]):
    """Return a copy of ``image`` with each box pixelated.

    ``boxes`` are ``(x1, y1, x2, y2)`` in pixel coordinates. An empty box list
    returns an unblurred copy; ``decide_publication`` refuses that case when
    ``n_boxes`` is 0. Pillow is imported here so the decision function can be
    used without it.
    """
    from PIL import Image

    if not isinstance(image, Image.Image):
        image = Image.open(image)
    out = image.convert("RGB").copy()
    width, height = out.size
    for box in boxes:
        x1, y1, x2, y2 = (int(box[0]), int(box[1]), int(box[2]), int(box[3]))
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(width, x2), min(height, y2)
        if x2 - x1 < 2 or y2 - y1 < 2:
            continue
        crop = out.crop((x1, y1, x2, y2))
        small = crop.resize((max(1, (x2 - x1) // 12), max(1, (y2 - y1) // 12)))
        out.paste(small.resize((x2 - x1, y2 - y1), Image.Resampling.NEAREST), (x1, y1))
    return out
